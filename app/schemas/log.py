from pydantic import BaseModel
from datetime import datetime

# Cetakan dasar (isi data)
class LogBase(BaseModel):
    topic_type: str
    value: str

# Cetakan untuk Response API (ditambah ID & Waktu)
class LogResponse(LogBase):
    id: int
    device_id: str
    created_at: datetime

    class Config:
        from_attributes = True  # Supaya bisa baca data dari SQLAlchemy