from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import engine, get_db, Base
from app.models.device import Device
from app.mqtt.client import connect_mqtt, mqtt_client # <--- Tambahan 1
from app.api.v1.devices import router as device_router

import os

# --- INIT DATABASE ---
Base.metadata.create_all(bind=engine)

app = FastAPI(title="IoT Backend API")

app.include_router(device_router, prefix="/api/v1", tags=["Devices"])

# --- INIT MQTT SAAT SERVER NYALA --- <--- Tambahan 2
@app.on_event("startup")
async def startup_event():
    print("🚀 Menyalakan Mesin MQTT...")
    connect_mqtt()

@app.get("/")
def read_root():
    return {"status": "Backend is Running", "db_connected": True}

# --- API CONTROL RELAY (TESTING MQTT) --- <--- Tambahan 3
@app.post("/control-relay")
def control_relay(device_id: str, state: str):
    # Validasi input
    if state not in ["ON", "OFF"]:
        return {"error": "State harus ON atau OFF"}
    
    # Tentukan Topic: alat/{ID}/command
    topic = f"alat/{device_id}/command"
    payload = f'{{"relay": "{state}"}}'
    
    # Kirim Pesan via MQTT
    mqtt_client.publish(topic, payload)
    
    return {
        "message": "Perintah dikirim", 
        "topic": topic, 
        "payload": payload
    }

# ... (Biarkan endpoint test-create-device yang lama tetap ada di bawah sini)
@app.post("/test-create-device")
def create_dummy_device(device_id: str, pin: str, db: Session = Depends(get_db)):
    # ... (code lama)
    existing_device = db.query(Device).filter(Device.device_id == device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Device ID sudah ada bro!")
    new_device = Device(device_id=device_id, pin_code=pin)
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return {"message": "Sukses nambah alat!", "data": new_device}