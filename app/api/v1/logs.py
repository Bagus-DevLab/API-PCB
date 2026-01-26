from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# --- IMPORT RATE LIMITER ---
from fastapi_limiter.depends import RateLimiter

# --- IMPORT AUTH (SATPAM) ---
from app.api.v1.auth import get_current_user  # <--- Tambah ini

# --- IMPORT DATABASE & MODEL ---
from app.core.database import get_db     # <--- Fix path ke app.db
from app.crud import log as crud_log
from app.schemas.log import LogResponse
from app.models.device import Device   # <--- Import Device buat cek owner

router = APIRouter()

# times=5, seconds=10 artinya: Max 5 request dalam 10 detik.
@router.get("/{device_id}", response_model=List[LogResponse], dependencies=[Depends(RateLimiter(times=5, seconds=10))])
def read_device_logs(
    device_id: str, 
    limit: int = 20, 
    db: Session = Depends(get_db),
    user_uid: str = Depends(get_current_user) # <--- Wajib Login
):
    # --- LOGIKA TAMBAHAN: CEK KEPEMILIKAN ---
    # Biar orang iseng gak bisa intip data kandang orang lain
    
    # 1. Cari alatnya dulu di DB
    # Note: Kita gunakan strip().upper() biar konsisten sama ID penyimpanan
    clean_id = device_id.strip().upper()
    device = db.query(Device).filter(Device.device_id == clean_id).first()
    
    # 2. Validasi
    if not device:
         # Kalau alat tidak ditemukan, return list kosong (atau 404)
         return []

    # 3. Cek apakah User yang login == Pemilik Alat
    if device.owner_uid != user_uid:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke alat ini.")

    # 4. Kalau aman, baru ambil datanya
    logs = crud_log.get_logs_by_device(db, device_id=clean_id, limit=limit)
    
    if not logs:
        return []
        
    return logs