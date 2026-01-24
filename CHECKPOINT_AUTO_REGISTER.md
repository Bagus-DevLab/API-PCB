# 🚩 Checkpoint: IoT Auto-Provisioning & Stable Docker

**Status:** ✅ STABLE MVP  
**Last Updated:** 24 Jan 2026  
**Features:** Auto-Register ESP32, MQTT Control, Docker Healthcheck

---

## 1. Arsitektur Saat Ini

Sistem sudah berjalan otomatis. ESP32 mendaftarkan diri sendiri, User tinggal klaim.

### Alur Pendaftaran (Auto-Provisioning)

1. **ESP32 Booting** → Connect WiFi
2. **ESP32 ambil MAC Address**, buang titik dua (`:`), jadi ID unik (misal: `441D64BE2208`)
3. **ESP32 kirim** `POST /auto-register` ke Backend bawa `factory_secret`
4. **Backend validasi** secret → Simpan ke DB PostgreSQL
5. **User (Flutter)** masukkan ID `441D64BE2208` → Claim Berhasil

---

## 2. File "Emas" (Golden Files)

Ini adalah kode final yang sudah kita perbaiki dari error-error tadi.

### A. Docker Compose (`docker-compose.yml`)

**Fix:** Race Condition (FastAPI crash karena DB belum siap)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: iot_postgres
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    ports:
      - "5432:5432"
    # HEALTHCHECK: Memastikan DB siap sebelum Backend jalan
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user_pcb -d iot_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: iot_redis
    restart: always
    ports:
      - "6379:6379"

  web:
    build: .
    container_name: iot_fastapi
    restart: always
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./app:/code/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    # DEPENDS_ON: Menunggu DB "Healthy", bukan cuma "Started"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

volumes:
  postgres_data:
```

### B. Firmware ESP32 (`AutoRegister.ino`)

**Fix:** ID Mismatch (Sinkronisasi ID Database vs MQTT)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

extern const char* API_URL;
extern const char* FACTORY_SECRET;
extern const char* DEVICE_PIN;

void registerDeviceToBackend() {
  if(WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");

  // JURUS FIX ID: Ambil MAC Address murni
  String mac = WiFi.macAddress();
  mac.replace(":", ""); 
  String finalID = mac;

  String jsonPayload = "{";
  jsonPayload += "\"device_id\": \"" + finalID + "\",";
  jsonPayload += "\"pin_code\": \"" + String(DEVICE_PIN) + "\",";
  jsonPayload += "\"factory_secret\": \"" + String(FACTORY_SECRET) + "\"";
  jsonPayload += "}";

  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) {
    Serial.print("✅ ID TERDAFTAR: ");
    Serial.println(finalID);
  }
  http.end();
}
```

### C. Backend Python (`app/api/v1/devices.py`)

**Fix:** Error 422 (Pemisahan Schema User vs Alat)

```python
# Schema User (Cuma ID & PIN)
class UserClaimSchema(BaseModel):
    device_id: str
    pin_code: str

# Schema Alat (Ada Factory Secret)
class AutoRegisterSchema(BaseModel):
    device_id: str
    pin_code: str
    factory_secret: str

# Endpoint Claim (Pakai UserClaimSchema)
@router.post("/claim")
def claim_device(request: Request, claim_data: UserClaimSchema, ...):
    # Logic Claim...

# Endpoint Auto Register (Pakai AutoRegisterSchema)
@router.post("/auto-register")
def auto_register_device(request: Request, data: AutoRegisterSchema, ...):
    # Logic Register...
```

---

## 3. Masalah yang Sudah Diatasi (Troubleshooting Log)

### Backend Crash saat Startup
- **Penyebab:** Race Condition (Backend jalan duluan sebelum DB siap)
- **Solusi:** Menambahkan `healthcheck` di Postgres dan `condition: service_healthy` di Backend

### Error 422 Unprocessable Entity (Flutter)
- **Penyebab:** Flutter mengirim JSON tanpa `factory_secret`, tapi Backend memaksa harus ada
- **Solusi:** Memisahkan Pydantic Model menjadi `UserClaimSchema` dan `AutoRegisterSchema`

### ID Tidak Cocok (Control Gagal)
- **Penyebab:** AutoRegister pakai ID pendek (BE64...), MQTT pakai ID panjang (441D...)
- **Solusi:** Menggunakan `WiFi.macAddress()` dan menghapus colons (`:`) agar ID seragam di semua tempat

### Error 401 Token Too Early
- **Penyebab:** Jam Docker drift (tertinggal) dari jam host
- **Solusi:** Restart WSL (`wsl --shutdown`)

---

## 4. Cara Menjalankan (Reset Bersih)

Jika ingin mengulang dari 0 bersih:

### Backend

```bash
docker-compose down -v  # Hapus volume database lama
docker-compose up --build
```

### ESP32

1. Tekan tombol **RESET** di board
2. Tunggu Serial Monitor: `✅ ID TERDAFTAR: XXXXXXXXXXXX`

### Flutter

1. Masukkan ID dari Serial Monitor
2. **Claim** → Sukses
3. **Control** → Lampu Nyala

---

## ✅ Mission Accomplished