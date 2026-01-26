from fastapi import FastAPI
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

# Import komponen buatan kita
from app.mqtt.client import start_mqtt
from app.api import logs 

# --- SETTING LIFESPAN (Cara Modern Handle Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==========================
    # 1. LOGIKA SAAT STARTUP
    # ==========================
    print("🚀 System Starting Up...")
    
    # A. Nyalakan MQTT
    start_mqtt()
    print("✅ MQTT Listener Berjalan!")

    # B. Konek Redis & Init Rate Limiter
    try:
        # Gunakan "redis" karena itu nama service di docker-compose
        redis_connection = redis.from_url("redis://redis:6379", encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_connection)
        print("🛡️ Rate Limiter Activated!")
    except Exception as e:
        print(f"⚠️ Gagal Konek Redis: {e}")

    yield # <--- Di sini aplikasi berjalan melayani user

    # ==========================
    # 2. LOGIKA SAAT SHUTDOWN
    # ==========================
    print("🛑 System Shutting Down...")
    await redis_connection.close()

# --- INISIALISASI APP DENGAN LIFESPAN ---
app = FastAPI(title="PCB Backend API", lifespan=lifespan)

# --- DAFTARKAN ROUTER ---
app.include_router(logs.router, prefix="/api/logs", tags=["Sensor Logs"])

@app.get("/")
def read_root():
    return {"message": "PCB Backend is Running & Protected!"}