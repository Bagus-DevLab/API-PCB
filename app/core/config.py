from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.device import SensorLog

# --- HAPUS BARIS INI JIKA ADA: ---
# from app.core.config import settings  <-- INI BIANG KEROKNYA, HAPUS!

# Fungsi pembantu untuk simpan ke DB
def save_sensor_data(device_id: str, topic_type: str, payload: str):
    db: Session = SessionLocal()
    try:
        new_log = SensorLog(
            device_id=device_id,
            topic_type=topic_type,
            value=payload
        )
        db.add(new_log)
        db.commit()
        print(f"💾 Saved: [{device_id}] {topic_type} -> {payload}")
    except Exception as e:
        print(f"❌ DB Error: {e}")
        db.rollback()
    finally:
        db.close()

# Callback utama saat ada pesan MQTT masuk
def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        
        # Format Topik: alat/{DEVICE_ID}/status/{TIPE}
        parts = topic.split("/")
        
        if len(parts) == 4 and parts[0] == "alat" and parts[2] == "status":
            device_id = parts[1]   
            sensor_type = parts[3] 
            
            save_sensor_data(device_id, sensor_type, payload)
        else:
            print(f"⚠️ Topik tidak dikenal: {topic}")

    except Exception as e:
        print(f"Error processing MQTT: {e}")