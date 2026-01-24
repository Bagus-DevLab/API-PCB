from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.device import Device
from app.core.security import get_current_user # <--- Import Satpam tadi
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request # <--- Wajib import Request
from app.core.limiter import limiter # <--- Import ini
from app.mqtt.client import mqtt_client

router = APIRouter()

# Schema Input (Biar validasi data rapi)
class ClaimRequest(BaseModel):
    device_id: str
    pin_code: str

@router.post("/claim")
@limiter.limit("5/minute")
def claim_device(
    request: Request, # <--- Wajib ada parameter 'request' di sini buat Slowapi baca IP
    input_data: ClaimRequest, 
    db: Session = Depends(get_db), 
    user_uid: str = Depends(get_current_user)
):
    # 1. Cari alat berdasarkan ID
    device = db.query(Device).filter(Device.device_id == request.device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Alat tidak ditemukan. Cek ID di stiker.")

    # 2. Cek apakah sudah ada yang punya?
    if device.owner_uid:
        if device.owner_uid == user_uid:
             return {"message": "Alat ini memang sudah punya kamu kok."}
        raise HTTPException(status_code=400, detail="Alat ini sudah dimiliki orang lain!")

    # 3. Cek PIN (Password Alat)
    if device.pin_code != request.pin_code:
        raise HTTPException(status_code=400, detail="PIN Salah! Cek stiker alat.")

    # 4. SAH! Ikatkan alat ke user ini
    device.owner_uid = user_uid
    device.device_name = "Alat Baru Saya" # Default name
    db.commit()
    
    return {
        "status": "success",
        "message": f"Selamat! Alat {request.device_id} berhasil ditambahkan ke akunmu.",
        "owner": user_uid
    }
    
    
# --- API CONTROL RELAY (TESTING MQTT) --- <--- Tambahan 3
@router.post("/control-relay")
@limiter.limit("5/minute")
def control_relay(
    request: Request,
    device_id: str, 
    state: str
    ):
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