from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

# --- IMPORT RATE LIMITER ---
from fastapi_limiter.depends import RateLimiter

# --- IMPORT DATABASE ---
from app.core.database import get_db
from app.models.device import Device 

# --- PERBAIKAN VITAL DISINI ---
# Kita import 'mqtt_client' karena itu nama variabel asli di file mqtt/client.py
from app.mqtt.client import mqtt_client 

router = APIRouter()

# --- SCHEMA ---
class UserClaimSchema(BaseModel):
    device_id: str
    pin_code: str

class AutoRegisterSchema(BaseModel):
    device_id: str
    pin_code: str
    factory_secret: str

# --- 1. ENDPOINT CLAIM (User) ---
@router.post("/claim", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def claim_device(
    claim_data: UserClaimSchema, 
    db: Session = Depends(get_db)
):
    # Hardcode user sementara
    user_uid = "TEST_USER_UID_001" 

    clean_id = claim_data.device_id.strip().upper()
    clean_pin = claim_data.pin_code.strip()

    device = db.query(Device).filter(Device.device_id == clean_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Alat {clean_id} tidak ditemukan.")

    if device.owner_uid:
        if device.owner_uid == user_uid:
             return {"message": "Alat ini memang sudah punya kamu kok."}
        raise HTTPException(status_code=400, detail="Alat ini sudah dimiliki orang lain!")

    if device.pin_code != clean_pin:
        raise HTTPException(status_code=400, detail="PIN Salah!")

    device.owner_uid = user_uid
    device.device_name = "Alat Baru Saya"
    db.commit()
    
    return {"status": "success", "message": f"Alat {clean_id} berhasil diklaim!"}


# --- 2. ENDPOINT CONTROL RELAY ---
@router.post("/control-relay", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def control_relay(
    device_id: str,
    state: str,
    db: Session = Depends(get_db)
):
    clean_id = device_id.strip().upper()

    if state not in ["ON", "OFF"]:
        return {"error": "State harus ON atau OFF"}

    device = db.query(Device).filter(Device.device_id == clean_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Alat tidak ditemukan.")

    topic = f"alat/{clean_id}/command"
    payload = f'{{"relay": "{state}"}}'

    # --- PAKAI mqtt_client YANG BENAR ---
    mqtt_client.publish(topic, payload)

    return {"message": "Perintah dikirim", "topic": topic, "state": state}


# --- 3. ENDPOINT AUTO REGISTER (ESP32) ---
@router.post("/auto-register", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def auto_register_device(
    data: AutoRegisterSchema,
    db: Session = Depends(get_db)
):
    FACTORY_SECRET = "RAHASIA_PABRIK_PCB_SERIUS_2026"
    
    if data.factory_secret != FACTORY_SECRET:
        raise HTTPException(status_code=403, detail="Anda bukan perangkat resmi!")

    clean_id = data.device_id.strip().upper()
    clean_pin = data.pin_code.strip()
    
    existing_device = db.query(Device).filter(Device.device_id == clean_id).first()
    if existing_device:
        return {"message": "Alat sudah terdaftar, skip."}

    new_device = Device(
        device_id=clean_id,
        pin_code=clean_pin,
        device_name="New Device",
    )
    db.add(new_device)
    db.commit()
    
    return {"message": f"Sukses! Alat {clean_id} didaftarkan."}