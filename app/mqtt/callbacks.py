from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.device import SensorLog

# --- FUNGSI SIMPAN KE DB ---
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
        print(f"💾 Saved DB: [{device_id}] {topic_type} -> {payload}")
    except Exception as e:
        print(f"❌ Gagal Simpan DB: {e}")
        db.rollback()
    finally:
        db.close()

# --- CALLBACK SAAT PESAN MASUK ---
def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        
        # LOGIKA MEMBEDAH TOPIK DINAMIS
        # Format: alat/{DEVICE_ID}/status/{TIPE}
        # Contoh: alat/441D64BE2208/status/suhu
        
        parts = topic.split("/")
        
        # Validasi: Harus ada 4 bagian, depannya 'alat', tengahnya 'status'
        if len(parts) == 4 and parts[0] == "alat" and parts[2] == "status":
            device_id = parts[1]   # Ambil ID (441D...)
            sensor_type = parts[3] # Ambil Tipe (suhu/ldr/lampu)
            
            # Simpan ke Database
            save_sensor_data(device_id, sensor_type, payload)
            
        else:
            print(f"⚠️ Topik tidak sesuai format: {topic}")

    except Exception as e:
        print(f"Error processing MQTT: {e}")