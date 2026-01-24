from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models.device import Device, Base
import os

# --- INIT DATABASE ---
# Perintah sakti ini akan membuat semua tabel yang ada di models
Base.metadata.create_all(bind=engine)

app = FastAPI(title="IoT Backend API")

@app.get("/")
def read_root():
    return {"status": "Backend is Running", "db_connected": True}

# --- API TEST BUAT NAMBAH ALAT (HANYA BUAT NYOBA) ---
@app.post("/test-create-device")
def create_dummy_device(device_id: str, pin: str, db: Session = Depends(get_db)):
    # 1. Cek dulu apakah ID sudah ada?
    existing_device = db.query(Device).filter(Device.device_id == device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Device ID sudah ada bro!")

    # 2. Buat data baru
    new_device = Device(device_id=device_id, pin_code=pin)
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    return {"message": "Sukses nambah alat!", "data": new_device}

@app.get("/test-get-devices")
def get_all_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return devices