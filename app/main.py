import os
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.mqtt.client import start_mqtt

# Import Module Kita
from app.core.database import engine, get_db, Base
from app.models.device import Device
from app.mqtt.client import start_mqtt
from app.api.v1.devices import router as device_router
from app.core.limiter import limiter
from app.api import logs

# --- INIT DATABASE ---
Base.metadata.create_all(bind=engine)

# --- SETUP APP ---
app = FastAPI(title="IoT Backend API")

# 1. Pasang State Limiter (Wajib di main.py)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. Register Router
app.include_router(device_router, prefix="/api/v1", tags=["Devices"])
app.include_router(logs.router, prefix="/api/logs", tags=["Sensor Logs"])

# --- STARTUP EVENTS ---
@app.on_event("startup")
async def startup_event():
    print("🚀 Menyalakan Mesin MQTT...")
    print("🚀 APLIKASI UPDATE DARI GITHUB ACTION BERHASIL!")
    start_mqtt()

# --- ROOT ENDPOINT (Contoh penggunaan di main.py) ---
@app.get("/")
@limiter.limit("5/minute") # Contoh: IP yg sama cuma boleh refresh halaman ini 5x semenit
def read_root(request: Request): # <--- JANGAN LUPA request: Request
    return {
        "status": "Backend is Running", 
        "service": "IoT Platform",
        "docs_url": "/docs"
    }

# --- ENDPOINT TEST DUMMY (Boleh dihapus nanti kalau production) ---
@app.post("/test-create-device")
def create_dummy_device(device_id: str, pin: str, db: Session = Depends(get_db)):
    existing_device = db.query(Device).filter(Device.device_id == device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Device ID sudah ada bro!")
    new_device = Device(device_id=device_id, pin_code=pin)
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return {"message": "Sukses nambah alat!", "data": new_device}