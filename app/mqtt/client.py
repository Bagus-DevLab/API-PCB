import paho.mqtt.client as mqtt
from app.mqtt.callbacks import on_message 

# Global Client
mqtt_client = mqtt.Client(client_id="Backend_Listener_Worker", protocol=mqtt.MQTTv311)

def start_mqtt():
    # 1. SETUP KREDENSIAL (Hardcode dulu biar aman dari error import)
    MQTT_BROKER = "k2519aa6.ala.asia-southeast1.emqxsl.com"
    MQTT_PORT = 8883
    MQTT_USER = "PCB01"
    MQTT_PASS = "5ywnMzsVX4Ss9vH"

    print(f"🔌 Menghubungkan ke EMQX: {MQTT_BROKER}...")

    # 2. CONFIG CLIENT
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.tls_set() # WAJIB SSL KARENA PORT 8883
    mqtt_client.on_message = on_message # Sambungkan ke otak logic tadi

    # 3. CONNECT & SUBSCRIBE
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # SUBSCRIBE WILDCARD
        # "+" artinya ID alat apa saja
        # "#" artinya status apa saja (suhu, ldr, dll)
        mqtt_client.subscribe("alat/+/status/#")
        
        mqtt_client.loop_start() # Jalan di background
        print("✅ MQTT Listener Berjalan! Mendengarkan: alat/+/status/#")
        
    except Exception as e:
        print(f"❌ Gagal Konek MQTT: {e}")

# Fungsi helper untuk control (dipakai nanti)
def publish(topic: str, payload: str):
    if mqtt_client.is_connected():
        mqtt_client.publish(topic, payload)
        print(f"📡 Backend Kirim: {topic} -> {payload}")