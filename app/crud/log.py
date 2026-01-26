from sqlalchemy.orm import Session
from app.models.device import SensorLog  # Pastikan import model kamu benar

def get_logs_by_device(db: Session, device_id: str, limit: int = 100):
    """
    Mengambil data log sensor berdasarkan ID Alat.
    Diurutkan dari yang paling baru.
    """
    return db.query(SensorLog)\
             .filter(SensorLog.device_id == device_id)\
             .order_by(SensorLog.created_at.desc())\
             .limit(limit)\
             .all()