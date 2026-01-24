from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.device import Device
from app.core.security import get_current_user  # <--- Import Satpam tadi
from pydantic import BaseModel
# <--- Wajib import Request
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.limiter import limiter  # <--- Import ini
from app.mqtt.client import mqtt_client
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.device import Device

router = APIRouter()

# Schema Input (Biar validasi data rapi)


class ClaimRequest(BaseModel):
    device_id: str
    pin_code: str


# app/api/v1/devices.py

@router.post("/claim")
@limiter.limit("5/minute") 
def claim_device(
    request: Request,             # <--- 1. Ini buat Rate Limiter (Wajib ada)
    claim_data: ClaimRequest,     # <--- 2. Ini buat Data JSON (device_id & pin ada disini)
    db: Session = Depends(get_db), 
    user_uid: str = Depends(get_current_user)
):
    # Gunakan 'claim_data' untuk ambil ID, BUKAN 'request'
    device = db.query(Device).filter(Device.device_id == claim_data.device_id).first()
    
    if not device:
        # Gunakan 'claim_data' juga disini
        raise HTTPException(status_code=404, detail=f"Alat {claim_data.device_id} tidak ditemukan.")

    if device.owner_uid:
        if device.owner_uid == user_uid:
             return {"message": "Alat ini memang sudah punya kamu kok."}
        raise HTTPException(status_code=400, detail="Alat ini sudah dimiliki orang lain!")

    # Gunakan 'claim_data' buat cek PIN
    if device.pin_code != claim_data.pin_code:
        raise HTTPException(status_code=400, detail="PIN Salah! Cek stiker alat.")

    device.owner_uid = user_uid
    device.device_name = "Alat Baru Saya"
    db.commit()
    
    return {
        "status": "success",
        # Gunakan 'claim_data' disini juga
        "message": f"Selamat! Alat {claim_data.device_id} berhasil ditambahkan ke akunmu.",
        "owner": user_uid
    }


# --- API CONTROL RELAY (TESTING MQTT) --- <--- Tambahan 3
@router.post("/control-relay")
@limiter.limit("5/minute")
def control_relay(
    request: Request,
    device_id: str,
    state: str,
    user_uid: str = Depends(get_current_user),  # User yang sedang login
    db: Session = Depends(get_db)
):
    # Validasi input
    if state not in ["ON", "OFF"]:
        return {"error": "State harus ON atau OFF"}

    # 2. [LOGIC BARU] Cek Database: Apakah alat ini ada & milik user ini?
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=404, detail="Alat tidak ditemukan di sistem kami.")

    # Skenario B: Alat ada, TAPI bukan milik user yang login
    if device.owner_uid != user_uid:
        raise HTTPException(
            status_code=403, detail="Eits! Ini bukan alat kamu. Dilarang kontrol!")

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
