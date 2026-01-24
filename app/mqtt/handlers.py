def on_message(client, userdata, msg):
    """
    Fungsi ini dipanggil otomatis setiap kali ada pesan masuk 
    ke topik yang kita subscribe.
    """
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    
    print(f"\n📩 PESAN MASUK!")
    print(f"   Topic  : {topic}")
    print(f"   Isi    : {payload}")

    # --- DISINI NANTI TEMPAT LOGIC CANGGIH KAMU ---
    # Contoh pengembangan masa depan:
    # if "sensor" in topic:
    #     save_sensor_to_db(payload)
    # elif "status" in topic:
    #     update_device_online_status(payload)