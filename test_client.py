import requests
import json

# --- KONFIGURASI (ISI INI DULU) ---
FIREBASE_WEB_API_KEY = "AIzaSyC0LceftkVo3HDEDhALnXtoTkxi5Oq5YNI"
BASE_URL = "http://localhost:8000"

# User Dummy yang sudah dibuat di Firebase Console
EMAIL = "bagusanardiansyah@gmail.com"
PASSWORD = "12345678"

# Data Alat (Sesuaikan dengan ESP32 kamu)
DEVICE_ID = "441D64BE2208"  # Ganti dengan ID dari Serial Monitor ESP32
PIN_CODE = "1234"        # Ganti dengan PIN di Database/Hardcode


def get_firebase_token():
    print("🔑 Sedang Login ke Firebase...")
    # URL Endpoint Login Firebase
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": EMAIL,
        "password": PASSWORD,
        "returnSecureToken": True
    }

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print("❌ Login Gagal:", response.text)
        exit()

    data = response.json()
    token = data['idToken']
    print("✅ Login Sukses! Dapat Token.")
    return token


def claim_device(token):
    print("\n📝 Mencoba Claim Device...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "device_id": DEVICE_ID,
        "pin_code": PIN_CODE
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/claim", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


def control_lamp(token, state):
    print(f"\n💡 Mengirim Perintah Lampu: {state}...")
    headers = {"Authorization": f"Bearer {token}"}

    # Perhatikan param query string (?device_id=...&state=...)
    params = {
        "device_id": DEVICE_ID,
        "state": state
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/control-relay", params=params, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


if __name__ == "__main__":
    # 1. Ambil Token
    token = get_firebase_token()

    # 2. Claim (Kalau belum pernah claim, uncomment baris bawah ini)
    # claim_device(token)

    # 3. Control Lampu
    control_lamp(token, "ON")

    # 4. Control Lampu OFF (Opsional)
    # import time
    # time.sleep(2)
    # control_lamp(token, "OFF")
