from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.device import Device
from app.core.security import get_current_user
from app.core.limiter import limiter
from app.mqtt.client import mqtt_client

router = APIRouter()

# --- SCHEMA 1: UNTUK USER (CLAIM) ---
# User HANYA input ID dan PIN. Tidak perlu Factory Secret.
class UserClaimSchema(BaseModel):
    device_id: str
    pin_code: str

# --- SCHEMA 2: UNTUK ESP32 (AUTO REGISTER) ---
# Alat WAJIB punya Factory Secret.
class AutoRegisterSchema(BaseModel):
    device_id: str
    pin_code: str
    factory_secret: str


# --- 1. ENDPOINT CLAIM (User) ---
@router.post("/claim")
@limiter.limit("5/minute") 
def claim_device(
    request: Request,
    claim_data: UserClaimSchema, # <--- GUNAKAN SCHEMA USER
    db: Session = Depends(get_db), 
    user_uid: str = Depends(get_current_user)
):
    # 1. Bersihkan Input (Spasi & Huruf Besar)
    clean_id = claim_data.device_id.strip().upper()
    clean_pin = claim_data.pin_code.strip()

    # 2. Cari Alat
    device = db.query(Device).filter(Device.device_id == clean_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Alat {clean_id} tidak ditemukan. Pastikan alat sudah nyala.")

    if device.owner_uid:
        if device.owner_uid == user_uid:
             return {"message": "Alat ini memang sudah punya kamu kok."}
        raise HTTPException(status_code=400, detail="Alat ini sudah dimiliki orang lain!")

    # 3. Cek PIN
    if device.pin_code != clean_pin:
        raise HTTPException(status_code=400, detail="PIN Salah! Cek stiker alat.")

    # 4. Simpan Pemilik
    device.owner_uid = user_uid
    device.device_name = "Alat Baru Saya"
    db.commit()
    
    return {
        "status": "success",
        "message": f"Selamat! Alat {clean_id} berhasil ditambahkan ke akunmu.",
        "owner": user_uid
    }


# --- 2. ENDPOINT CONTROL RELAY ---
@router.post("/control-relay")
@limiter.limit("10/minute") # Limit agak longgar buat kontrol
def control_relay(
    request: Request,
    device_id: str,
    state: str,
    user_uid: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_id = device_id.strip().upper()

    if state not in ["ON", "OFF"]:
        return {"error": "State harus ON atau OFF"}

    device = db.query(Device).filter(Device.device_id == clean_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Alat tidak ditemukan.")

    if device.owner_uid != user_uid:
        raise HTTPException(status_code=403, detail="Eits! Ini bukan alat kamu.")

    topic = f"alat/{clean_id}/command"
    payload = f'{{"relay": "{state}"}}'

    mqtt_client.publish(topic, payload)

    return {"message": "Perintah dikirim", "topic": topic, "payload": payload}


# --- 3. ENDPOINT AUTO REGISTER (ESP32) ---
@router.post("/auto-register")
@limiter.limit("5/minute")
def auto_register_device(
    request: Request,
    data: AutoRegisterSchema, # <--- GUNAKAN SCHEMA ALAT
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
        is_active=True
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    return {"message": f"Sukses! Alat {clean_id} berhasil didaftarkan otomatis."}