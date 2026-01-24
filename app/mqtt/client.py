import paho.mqtt.client as mqtt
import os
import time
from app.mqtt.handlers import on_message

# Ambil credential dari .env
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# Inisialisasi Client
mqtt_client = mqtt.Client()

# Setup Callback (Aksi ketika connect & terima pesan)
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ BERHASIL Konek ke MQTT Broker!")
        # Subscribe ke semua topik alat (Wildcard #)
        # Artinya: Dengerin semua chat di channel "alat/..."
        client.subscribe("alat/#") 
    else:
        print(f"❌ Gagal Konek, Return Code: {rc}")

# Pasang fungsi-fungsinya
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message # Panggil handler yang kita buat di Langkah 2

def connect_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start() # Jalan di background thread
    except Exception as e:
        print(f"⚠️ Error Koneksi MQTT: {e}")