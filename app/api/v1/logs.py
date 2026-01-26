from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db  # Pastikan path ini sesuai dengan file koneksi DB kamu
from app.crud import log as crud_log
from app.schemas.log import LogResponse

router = APIRouter()

@router.get("/{device_id}", response_model=List[LogResponse])
def read_device_logs(
    device_id: str, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    """
    Ambil histori data sensor.
    Contoh: GET /api/logs/ALAT_PALSU_01?limit=5
    """
    logs = crud_log.get_logs_by_device(db, device_id=device_id, limit=limit)
    if not logs:
        # Kita tidak return 404, tapi list kosong saja biar frontend gak error
        return []
    return logs