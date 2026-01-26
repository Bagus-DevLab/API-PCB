from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

# --- UPDATE IMPORT (Sesuai Struktur Baru) ---
from app.core.database import get_db          # <-- Folder db
from app.models.device import SensorLog     # <-- Sesuaikan nama class device kamu (Device/SensorLog?)
# Cek model kamu: Kalau nama classnya Device, ganti SensorLog jadi Device di baris atas
from app.mqtt.client import publish_message # <-- Kita pakai helper publish kalau ada, atau client langsung

# --- IMPORT RATE LIMITER REDIS ---
from fastapi_limiter.depends import RateLimiter

router = APIRouter()

# --- SCHEMA ---
class UserClaimSchema(BaseModel):
    device_id: str
    pin_code: str

class AutoRegisterSchema(BaseModel):
    device_id: str
    pin_code: str
    factory_secret: str

# Kita butuh model Device (Definisikan ulang kalau belum import)
# Asumsi kamu punya model Device di app/models/device.py
from app.models.device import Device # Pastikan ini ada

# --- 1. ENDPOINT CLAIM (User) ---
# Rate Limit: 5x per 60 detik
@router.post("/claim", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def claim_device(
    claim_data: UserClaimSchema, 
    db: Session = Depends(get_db)
    # user_uid: str = Depends(get_current_user) # <-- Aktifkan ini nanti kalau AUTH firebase sudah dipasang
):
    # Sementara kita hardcode user_uid dulu biar bisa tes tanpa login frontend
    user_uid = "TEST_USER_UID_001" 

    clean_id = claim_data.device_id.strip().upper()
    clean_pin = claim_data.pin_code.strip()

    # Cari Alat
    device = db.query(Device).filter(Device.device_id == clean_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Alat {clean_id} tidak ditemukan.")

    if device.owner_uid:
        if device.owner_uid == user_uid:
             return {"message": "Alat ini memang sudah punya kamu kok."}
        raise HTTPException(status_code=400, detail="Alat ini sudah dimiliki orang lain!")

    # Cek PIN
    if device.pin_code != clean_pin:
        raise HTTPException(status_code=400, detail="PIN Salah!")

    # Simpan Pemilik
    device.owner_uid = user_uid
    device.device_name = "Alat Baru Saya"
    db.commit()
    
    return {"status": "success", "message": f"Alat {clean_id} berhasil diklaim!"}


# --- 2. ENDPOINT CONTROL RELAY ---
# Rate Limit: 10x per 60 detik
@router.post("/control-relay", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def control_relay(
    device_id: str,
    state: str,
    db: Session = Depends(get_db)
):
    # Hardcode user dulu
    user_uid = "TEST_USER_UID_001"
    
    clean_id = device_id.strip().upper()

    if state not in ["ON", "OFF"]:
        return {"error": "State harus ON atau OFF"}

    device = db.query(Device).filter(Device.device_id == clean_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Alat tidak ditemukan.")

    # Proteksi Kepemilikan (Nyalakan nanti kalau Auth siap)
    # if device.owner_uid != user_uid:
    #    raise HTTPException(status_code=403, detail="Bukan alat kamu!")

    topic = f"alat/{clean_id}/command"
    payload = f'{{"relay": "{state}"}}'

    # Publish ke MQTT
    # Pastikan kamu import client mqtt yg benar, atau pakai cara ini:
    from app.mqtt.client import client as mqtt_client
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
        # is_active=True # Sesuaikan dengan model kamu
    )
    db.add(new_device)
    db.commit()
    
    return {"message": f"Sukses! Alat {clean_id} didaftarkan."}