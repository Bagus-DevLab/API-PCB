from pydantic import BaseModel
from datetime import datetime
from typing import Optional # <--- WAJIB IMPORT INI

class LogBase(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    amonia: float
    feed_level: float
    # relay boleh tidak diisi saat create
    relay_1: Optional[bool] = None 
    relay_2: Optional[bool] = None
    relay_3: Optional[bool] = None

class LogCreate(LogBase):
    pass

class LogResponse(LogBase):
    id: int
    created_at: datetime
    
    # KITA TIMPA LAGI DISINI BIAR AMAN
    # Kalau data dari DB null/gak ada, dia bakal isi None (gak error)
    relay_1: Optional[bool] = None
    relay_2: Optional[bool] = None
    relay_3: Optional[bool] = None

    class Config:
        from_attributes = True