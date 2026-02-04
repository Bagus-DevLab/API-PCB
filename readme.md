# 🚀 PCB Backend API

Backend service yang handal untuk sistem IoT PCB, dibangun menggunakan **FastAPI** (Python). Proyek ini menyediakan API untuk manajemen perangkat, kontrol relay secara real-time via **MQTT**, penyimpanan log sensor, dan autentikasi pengguna yang aman.

---

## ✨ Fitur Utama

*   **⚡ High Performance API**: Dibangun di atas FastAPI (Asynchronous).
*   **🔐 Secure Authentication**: Terintegrasi penuh dengan **Firebase Auth** (Token Validation).
*   **📡 Real-time Control**: Kontrol perangkat (Lampu, Pompa, dll) menggunakan protokol **MQTT**.
*   **🗄️ Database Power**: Menggunakan **PostgreSQL** untuk data persisten yang handal.
*   **🛡️ Rate Limiting**: Perlindungan terhadap spam/brute-force menggunakan **Redis**.
*   **🐳 Dockerized**: Mudah di-deploy menggunakan Docker Compose.
*   **🤖 Auto Register**: Mekanisme pendaftaran otomatis untuk perangkat keras (ESP32) yang valid.

---

## 🛠️ Teknologi yang Digunakan

*   **Bahasa**: Python 3.11+
*   **Framework**: FastAPI + Uvicorn
*   **Database**: PostgreSQL
*   **Cache & Limiter**: Redis
*   **Messaging**: Paho MQTT
*   **Auth**: Firebase Admin SDK
*   **DevOps**: Docker & Docker Compose

---

## 📋 Prasyarat

Sebelum memulai, pastikan Anda telah menginstal:

1.  **Docker** & **Docker Compose** (Sangat Disarankan)
2.  **Git**
3.  Akun **Firebase** (untuk Authentication dan `serviceAccountKey.json`)
4.  **Python 3.11+** (Untuk Development/Testing lokal)

---

## 🚀 Instalasi & Menjalankan (Docker)

Cara termudah untuk menjalankan proyek ini adalah menggunakan Docker Compose.

### 1. Clone Repository
```bash
git clone https://github.com/username/project-ini.git
cd API-PCB
```

### 2. Konfigurasi Firebase
Simpan file kredensial Firebase Admin SDK Anda ke lokasi berikut:
```bash
app/serviceAccountKey.json
```
> **Penting**: File ini bersifat rahasia. Jangan pernah commit file ini ke repository publik!

### 3. Konfigurasi Environment Variable
Buat file `.env` di root folder dan sesuaikan isinya:

```env
# Database Credentials
DB_USER=iot_user
DB_PASSWORD=iot_password
DB_NAME=iot_db

# Redis URL (Default Docker)
REDIS_URL=redis://redis:6379/0

# (Opsional) Lainnya sesuai kebutuhan
```

### 4. Jalankan Aplikasi
```bash
docker-compose up -d --build
```
Aplikasi akan berjalan di:
*   **API**: `http://localhost:8006`
*   **Swagger Docs**: `http://localhost:8006/docs`
*   **Redoc**: `http://localhost:8006/redoc`

---

## 📡 Dokumentasi API

Seluruh endpoint membutuhkan **Header Authorization** (Bearer Token dari Firebase Client), kecuali endpoint *Auto Register*.

### 📱 1. Device Management (`/api/devices`)

| Method | Endpoint | Deskripsi | Limit Rate |
| :--- | :--- | :--- | :--- |
| `GET` | `/my-devices` | Mengambil daftar alat milik user. | 20/menit |
| `POST` | `/claim` | Mengklaim alat baru menggunakan ID & PIN. | 5/menit |
| `PUT` | `/{device_id}` | Mengubah nama alat. | 10/menit |
| `DELETE` | `/{device_id}` | Menghapus alat dari akun (Unclaim). | 5/menit |

### 🎛️ 2. Device Control (`/api/devices`)

| Method | Endpoint | Deskripsi | Parameter |
| :--- | :--- | :--- | :--- |
| `POST` | `/control-relay` | Mengirim perintah ON/OFF ke alat via MQTT. | `device_id`, `relay_name`, `state` (bool) |
| `POST` | `/auto-register` | (Internal) Pendaftaran otomatis oleh ESP32. | *Requires Factory Secret* |

> **Relay Mapping**:
> *   `relay_1` -> Topik `.../cmd/lampu`
> *   `relay_2` -> Topik `.../cmd/pompa_minum`
> *   `relay_3` -> Topik `.../cmd/pompa_siram`

### 📊 3. Sensor Logs (`/api/logs`)

| Method | Endpoint | Deskripsi |
| :--- | :--- | :--- |
| `GET` | `/{device_id}` | Mengambil data log sensor dari alat tertentu. |

---

## 📂 Struktur Proyek

```
API-PCB/
├── app/
│   ├── api/                # Router & Logic API per versi (v1)
│   │   └── v1/
│   │       ├── auth.py     # Helper Auth Firebase
│   │       ├── devices.py  # Endpoint Device & Control
│   │       └── logs.py     # Endpoint Logs
│   ├── core/               # Konfigurasi Database & Global
│   ├── crud/               # Operasi Database (Create, Read, etc)
│   ├── models/             # Schema Database (SQLAlchemy)
│   ├── mqtt/               # Client & Handler MQTT
│   ├── schemas/            # Validasi Data (Pydantic)
│   ├── main.py             # Entry Point Aplikasi (Lifespan, Startup)
│   └── serviceAccountKey.json # (WAJIB ADA) Kunci Firebase
├── tests/                  # 🧪 Unit Tests (Pytest)
│   ├── conftest.py         # Mock Config
│   └── test_devices.py     # Tests
├── docker-compose.yml      # Orkestrasi Container (App, DB, Redis)
├── dockerfile              # Definisi Image App
├── requirements.txt        # Dependensi Python
├── test_client.py          # Script Python untuk mencoba API manual
└── readme.md               # Dokumentasi ini
```

---

## 🧪 Testing

Proyek ini mendukung **Unit Testing Otomatis** dan **Testing Manual**.

### 🤖 1. Unit Testing (Automated)

Kami menggunakan `pytest` dengan sistem **Mocking** agar tidak perlu koneksi ke database asli, MQTT broker, atau Firebase.

#### Prasyarat
*   Python 3.11+
*   Virtual Environment

#### Cara Menjalankan
1.  **Setup Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Jalankan Test**:
    ```bash
    pytest
    ```
3.  **Hasil**:
    Anda akan melihat laporan sukses (hijau) jika seluruh fungsi berjalan normal.

#### Fitur Mock
Test ini **tidak** menyentuh production, karena:
*   **Database**: Menggunakan SQLite In-Memory.
*   **MQTT**: Dipalsukan dengan `MagicMock`.
*   **Redis/Auth**: Di-bypass menggunakan Dependency Injection Override.

### 👨‍💻 2. Testing Manual (`test_client.py`)

Terdapat script `test_client.py` untuk mencoba API secara real ke server (butuh Firebase Token asli).

1.  Pastikan `requests` terinstall: `pip install requests`
2.  Edit `test_client.py`:
    *   Masukkan `FIREBASE_WEB_API_KEY` (dari Firebase Console).
    *   Masukkan credentials user dummy (Email/Pass).
    *   Set `DEVICE_ID` target.
3.  Jalankan:
    ```bash
    python test_client.py
    ```

---

## 🤝 Kontribusi

Pull requests dipersilakan. Untuk perubahan besar, harap buka issue terlebih dahulu untuk mendiskusikan apa yang ingin Anda ubah.

---

**Happy Coding!** 🚀
