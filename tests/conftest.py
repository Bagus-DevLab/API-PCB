import os
from dotenv import load_dotenv

# Load env first before importing app modules that rely on os.getenv
load_dotenv()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import App Utama & Component
from app.main import app
from app.core.database import Base, get_db
from app.api.v1.auth import get_current_user
from app.mqtt.client import mqtt_client  # Kita akan mock object ini

# --- 1. SETUP TEST DATABASE (SQLite Memory) ---
# Menggunakan check_same_thread=False karena SQLite akan diakses oleh thread berbeda di test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixture untuk membuat tabel & menghapus setelah test selesai (Clean State)
@pytest.fixture(scope="function")
def db_session():
    # Create Tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop Tables biar test isolasi
        Base.metadata.drop_all(bind=engine)

# --- 2. OVERRIDE DEPENDENCIES ---
# Override get_db agar App pakai SQLite Memory, bukan Postgres Produksi
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override Auth (Bypass Firebase)
# Kita anggap semua request datang dari "test_user_uid"
def override_get_current_user():
    return "test_user_uid"

# Apply Overrides
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


# --- 3. MOCKING MQTT (Biar gak konek ke Broker beneran) ---
from unittest.mock import MagicMock, patch

# --- 3. MOCKING MQTT (Biar gak konek ke Broker beneran) ---
from unittest.mock import MagicMock, patch, AsyncMock

# --- 3. MOCKING MQTT (Biar gak konek ke Broker beneran) ---
from unittest.mock import MagicMock, patch, AsyncMock

@pytest.fixture(autouse=True)
def mock_external_services():
    """
    Mock semua service eksternal: MQTT, Redis, Firebase, RateLimiter
    agar test berjalan isolasi tanpa butuh koneksi asli.
    """
    # Mock RateLimiter call agar awaitable
    # PENTING: Harus match signature asli agar FastAPI Dependency Injection jalan benar!
    from fastapi import Request, Response
    async def mock_limiter_call(self, request: Request, response: Response): 
        return None

    with patch("app.main.start_mqtt"), \
         patch("app.main.init_firebase"), \
         patch("fastapi_limiter.depends.RateLimiter.__call__", side_effect=mock_limiter_call, autospec=True), \
         patch("app.main.redis.from_url") as mock_redis:
        
        # Setup Redis Mock to be AsyncMock so await close() works
        mock_conn = AsyncMock()
        mock_redis.return_value = mock_conn
        
        yield

@pytest.fixture(autouse=True)
def mock_mqtt():
    # Helper specific for app.mqtt.client if needed, 
    # but app.main.start_mqtt patch above handles the connection/startup.
    # This fixture handles the usage of mqtt_client in the code (publish)
    
    # Kita ganti object 'mqtt_client' asli dengan Mock
    # Jadi setiap kali kode panggil mqtt_client.publish(), itu cuma dicatat di memory mock
    original_publish = mqtt_client.publish
    mqtt_client.publish = MagicMock()
    
    # Mock tls_set incase it is called elsewhere (though start_mqtt is patched)
    original_tls_set = mqtt_client.tls_set
    mqtt_client.tls_set = MagicMock()

    yield mqtt_client
    
    # Balikin lagi
    mqtt_client.publish = original_publish
    mqtt_client.tls_set = original_tls_set



# --- 4. TEST CLIENT FIXTURE ---
@pytest.fixture(scope="function")
def client(db_session):
    # Kita butuh db_session di sini cuma buat pastikan tabel udah dibuat
    # Karena override sudah di-set global di atas
    with TestClient(app) as c:
        yield c
