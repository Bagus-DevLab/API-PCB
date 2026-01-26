from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# --- IMPORT RATE LIMITER ---
from fastapi_limiter.depends import RateLimiter

from app.core.database import get_db
from app.crud import log as crud_log
from app.schemas.log import LogResponse

router = APIRouter()

# --- TEMPELKAN DI SINI (dependencies) ---
# times=5, seconds=10 artinya: Max 5 request dalam 10 detik.
@router.get("/{device_id}", response_model=List[LogResponse], dependencies=[Depends(RateLimiter(times=5, seconds=10))])
def read_device_logs(
    device_id: str, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    logs = crud_log.get_logs_by_device(db, device_id=device_id, limit=limit)
    if not logs:
        return []
    return logs