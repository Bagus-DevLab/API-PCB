import paho.mqtt.client as mqtt
from app.core.config import settings # Asumsi config ada di sini
from app.mqtt.callbacks import on_message # Import logika langkah 2

# Global variable buat client
mqtt_client = mqtt.Client(client_id="Backend_Listener_Worker", protocol=mqtt.MQTTv311)

def start_mqtt():
    # 1. Setup Auth (Sesuaikan dengan kredensial EMQX kamu)
    # Lebih baik ambil dari .env/config, tapi hardcode dulu buat test gapapa
    MQTT_BROKER = "k2519aa6.ala.asia-southeast1.emqxsl.com"
    MQTT_PORT = 8883
    MQTT_USER = "PCB01"
    MQTT_PASS = "5ywnMzsVX4Ss9vH"

    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.tls_set() # Wajib SSL untuk port 8883

    # 2. Hubungkan logic Callback
    mqtt_client.on_message = on_message

    # 3. Konek
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # 4. Subscribe Dynamic Topic
        # Tanda '+' adalah wildcard. 
        # Artinya kita dengar semua alat di topik status
        mqtt_client.subscribe("alat/+/status/#")
        
        mqtt_client.loop_start() # Jalankan di background thread
        print("✅ MQTT Listener Berjalan! Mendengarkan: alat/+/status/#")
        
    except Exception as e:
        print(f"❌ Gagal Konek MQTT: {e}")