
from app.models.device import Device
from unittest.mock import ANY

# ==========================================
# 1. TEST AUTO REGISTER (Device -> Server)
# ==========================================
def test_auto_register_success(client, db_session):
    payload = {
        "device_id": "TEST_DEV_01",
        "pin_code": "1234",
        "factory_secret": "RAHASIA_PABRIK_PCB_SERIUS_2026"
    }
    response = client.post("/api/devices/auto-register", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Sukses! Alat TEST_DEV_01 didaftarkan."}
    
    # Cek DB apakah masuk
    device = db_session.query(Device).filter_by(device_id="TEST_DEV_01").first()
    assert device is not None
    assert device.pin_code == "1234"

def test_auto_register_invalid_secret(client):
    payload = {
        "device_id": "HACKER_DEV",
        "pin_code": "0000",
        "factory_secret": "SALAH_BRO"
    }
    response = client.post("/api/devices/auto-register", json=payload)
    assert response.status_code == 403


# ==========================================
# 2. TEST CLAIM DEVICE (User -> Server)
# ==========================================
def test_claim_device_success(client, db_session):
    # Setup data awal (Alat harus ada dulu di DB hasil auto-register)
    new_device = Device(device_id="CLAIM_ME", pin_code="9999", device_name="Unknown")
    db_session.add(new_device)
    db_session.commit()
    
    # User melakukan claim
    payload = {"device_id": "CLAIM_ME", "pin_code": "9999"}
    response = client.post("/api/devices/claim", json=payload)
    
    assert response.status_code == 200
    
    # Cek apakah owner berubah jadi test_user_uid (dari override auth)
    db_session.refresh(new_device)
    assert new_device.owner_uid == "test_user_uid"
    assert new_device.device_name == "Alat Baru Saya"

def test_claim_device_wrong_pin(client, db_session):
    # Setup
    new_device = Device(device_id="WRONG_PIN_DEV", pin_code="8888")
    db_session.add(new_device)
    db_session.commit()
    
    payload = {"device_id": "WRONG_PIN_DEV", "pin_code": "0000"} # PIN SALAH
    response = client.post("/api/devices/claim", json=payload)
    
    assert response.status_code == 400
    assert "PIN Salah" in response.text


# ==========================================
# 3. TEST CONTROL RELAY (MQTT Logic)
# ==========================================
def test_control_relay_success_mqtt_publish(client, db_session, mock_mqtt):
    """
    Memastikan endpoint tidak hanya return 200, 
    tapi juga BENAR-BENAR memanggil fungsi publish MQTT.
    """
    # Setup Device milik User
    device = Device(
        device_id="MY_LAMP", 
        pin_code="1111", 
        owner_uid="test_user_uid" # HARUS MILIK USER YG LOGIN
    )
    db_session.add(device)
    db_session.commit()
    
    # Request Control ON
    params = {
        "device_id": "MY_LAMP",
        "relay_name": "relay_1", # Lampu
        "state": True # ON
    }
    response = client.post("/api/devices/control-relay", params=params)
    
    assert response.status_code == 200
    
    # VERIFIKASI MOCK: Apakah mqtt_client.publish dipanggil?
    # Ekspektasi Topik: alat/MY_LAMP/cmd/lampu
    # Ekspektasi Payload: ON
    mock_mqtt.publish.assert_called_with("alat/MY_LAMP/cmd/lampu", "ON")

def test_control_relay_not_owner(client, db_session):
    # Setup Device milik ORANG LAIN
    device = Device(
        device_id="NEIGHBOR_LAMP", 
        pin_code="1111", 
        owner_uid="other_person_uid" 
    )
    db_session.add(device)
    db_session.commit()
    
    params = {"device_id": "NEIGHBOR_LAMP", "relay_name": "relay_1", "state": True}
    response = client.post("/api/devices/control-relay", params=params)
    
    assert response.status_code == 403 # Forbidden
