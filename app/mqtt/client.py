import paho.mqtt.client as mqtt
# Jika kamu belum punya app.core.config, kita hardcode dulu credentials-nya
# from app.core.config import settings 
from app.mqtt.callbacks import on_message 

# Variabel Global Client
mqtt_client = mqtt.Client(client_id="Backend_Listener_Worker", protocol=mqtt.MQTTv311)

def start_mqtt():
    """
    Fungsi ini dipanggil oleh main.py saat server start.
    Tugasnya konek ke Broker dan mulai loop listener.
    """
    # 1. Setup Auth (Sesuaikan dengan kredensial EMQX kamu)
    MQTT_BROKER = "k2519aa6.ala.asia-southeast1.emqxsl.com"
    MQTT_PORT = 8883
    MQTT_USER = "PCB01"
    MQTT_PASS = "5ywnMzsVX4Ss9vH"

    print(f"🔌 Menghubungkan ke MQTT Broker: {MQTT_BROKER}...")

    # Set Username & Password
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    
    # Wajib SSL untuk port 8883
    mqtt_client.tls_set() 

    # 2. Hubungkan logic Callback (PENTING!)
    mqtt_client.on_message = on_message

    # 3. Konek & Subscribe
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Subscribe ke Topik Dinamis
        mqtt_client.subscribe("alat/+/status/#")
        
        # Jalankan di background thread
        mqtt_client.loop_start() 
        
        print("✅ MQTT Listener Berjalan! Mendengarkan: alat/+/status/#")
        
    except Exception as e:
        print(f"❌ Gagal Konek MQTT: {e}")

# Fungsi helper untuk publish (dipakai nanti buat control)
def publish(topic: str, payload: str):
    if mqtt_client.is_connected():
        mqtt_client.publish(topic, payload)
        print(f"📡 Published: {topic} -> {payload}")
    else:
        print("⚠️ MQTT belum terhubung, gagal publish.")