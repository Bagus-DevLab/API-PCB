from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identitas Alat
    device_id = Column(String, unique=True, index=True, nullable=False) # Contoh: A1B2C3 (Dari MAC Address)
    pin_code = Column(String, nullable=False) # Contoh: 8821 (Buat validasi saat claim)
    
    # Kepemilikan (Diisi saat user melakukan Claim)
    owner_uid = Column(String, nullable=True, index=True) # UID dari Firebase
    device_name = Column(String, nullable=True) # Nama bebas, misal "Lampu Teras"
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())