from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os

# Setup koneksi Redis buat nyimpen hitungan limit
# Kalau nanti deploy production, ganti "redis" dengan URL Redis cloud kamu
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Inisialisasi Limiter
# key_func=get_remote_address artinya kita batasi berdasarkan IP Address user
limiter = Limiter(
    key_func=get_remote_address, 
    storage_uri=REDIS_URL
)

# Ini biar kita bisa export handler-nya ke main.py
def get_limiter():
    return limiter