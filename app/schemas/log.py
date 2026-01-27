from pydantic import BaseModel
from datetime import datetime

# Cetakan dasar (isi data)
class LogBase(BaseModel):
    topic_type: str
    value: str

class LogResponse(BaseModel):
    id: int
    device_id: str
    temperature: float
    humidity: float
    amonia: float
    feed_level: float
    
    # Tambahkan status relay ini
    relay_1: bool # Lampu
    relay_2: bool # Kipas/Pompa Minum
    relay_3: bool # Pompa Siram
    
    created_at: datetime

    class Config:
        from_attributes = True