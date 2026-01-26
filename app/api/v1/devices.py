from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

# --- IMPORT RATE LIMITER (Anti-Spam) ---
from fastapi_limiter.depends import RateLimiter

# --- IMPORT AUTH (Satpam Firebase) ---
from app.api.v1.auth import get_current_user

# --- IMPORT DATABASE ---
from app.core.database import get_db
from app.models.device import Device 

# --- IMPORT MQTT (Buat Control) ---
from app.mqtt.client import mqtt_client 

router = APIRouter()

# ==========================================
# 1. SCHEMAS
# ==========================================
class UserClaimSchema(BaseModel):
    device_id: str
    pin_code: str

class AutoRegisterSchema(BaseModel):
    device_id: str
    pin_code: str
    factory_secret: str

class UpdateDeviceSchema(BaseModel):
    device_name: str

class DeviceResponse(BaseModel):
    device_id: str
    device_name: str
    owner_uid: Optional[str] = None
    
    class Config:
        from_attributes = True 

# ==========================================
# 2. ENDPOINTS
# ==========================================

# --- A. LIST MY DEVICES (Dashboard) ---
# Limit: 20 request / menit (Karena sering direfresh user)
@router.get("/my-devices", response_model=List[DeviceResponse], dependencies=[Depends(RateLimiter(times=20, seconds=60))])
def get_my_devices(
    db: Session = Depends(get_db),
    user_uid: str = Depends(get_current_user) # 🔒 Wajib Login
):
    """
    Mengambil daftar alat milik user yang sedang login.
    """
    devices = db.query(Device).filter(Device.owner_uid == user_uid).all()
    return devices


# --- B. CLAIM DEVICE ---
# Limit: 5 request / menit (Biar gak brute-force PIN)
@router.post("/claim", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def claim_device(
    claim_data: UserClaimSchema, 
    db: Session = Depends(get_db),
    user_uid: str = Depends(get_current_user) # 🔒 Wajib Login
):
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

    # SAH: Pindahkan kepemilikan
    device.owner_uid = user_uid
    device.device_name = "Alat Baru Saya"
    db.commit()
    
    return {"status": "success", "message": f"Alat {clean_id} berhasil diklaim!"}


# --- C. UPDATE DEVICE NAME ---
# Limit: 10 request / menit
@router.put("/{device_id}", response_model=DeviceResponse, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def update_device_name(
    device_id: str,
    update_data: UpdateDeviceSchema,
    db: Session = Depends(get_db),
    user_uid: str = Depends(get_current_user) # 🔒 Wajib Login
):
    clean_id = device_id.strip().upper()
    
    device = db.query(Device).filter(Device.device_id == clean_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Alat tidak ditemukan")
        
    if device.owner_uid != user_uid:
        raise HTTPException(status_code=403, detail="Bukan alat kamu!")
        
    device.device_name = update_data.device_name
    db.commit()
    db.refresh(device)
    
    return device


# --- D. UNCLAIM / DELETE DEVICE ---
# Limit: 5 request / menit (Tindakan berbahaya/kritis)
@router.delete("/{device_id}", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def unclaim_device(
    device_id: str,
    db: Session = Depends(get_db),
    user_uid: str = Depends(get_current_user) # 🔒 Wajib Login
):
    clean_id = device_id.strip().upper()
    
    device = db.query(Device).filter(Device.device_id == clean_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Alat tidak ditemukan")
        
    if device.owner_uid != user_uid:
        raise HTTPException(status_code=403, detail="Bukan alat kamu!")
        
    # Reset kepemilikan
    device.owner_uid = None
    device.device_name = "Unclaimed Device"
    db.commit()
    
    return {"message": f"Alat {clean_id} berhasil dihapus dari akunmu."}


# --- E. CONTROL RELAY ---
# Limit: 20 request / menit (Biar bisa on/off agak cepat)
@router.post("/control-relay", dependencies=[Depends(RateLimiter(times=20, seconds=60))])
def control_relay(
    device_id: str,
    state: str,
    db: Session = Depends(get_db),
    user_uid: str = Depends(get_current_user) # 🔒 Wajib Login
):
    clean_id = device_id.strip().upper()

    if state not in ["ON", "OFF"]:
        return {"error": "State harus ON atau OFF"}

    device = db.query(Device).filter(Device.device_id == clean_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Alat tidak ditemukan.")

    if device.owner_uid != user_uid:
        raise HTTPException(status_code=403, detail="Eits! Bukan alat kamu.")

    topic = f"alat/{clean_id}/command"
    payload = f'{{"relay": "{state}"}}'

    mqtt_client.publish(topic, payload)

    return {"message": "Perintah dikirim", "topic": topic, "state": state}


# --- F. AUTO REGISTER (Mesin ke Mesin) ---
# Limit: 5 request / menit
# TIDAK PAKAI 'user_uid' KARENA YANG REQUEST ADALAH ESP32 (Bukan Manusia)
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