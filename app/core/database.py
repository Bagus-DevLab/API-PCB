from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base # <--- Perubahan disini (pindah ke .orm)
import os

# Ambil config dari env
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Buat URL Koneksi
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Buat Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Buat Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Buat Base Model (Inilah yang tadi dicari-cari tapi hilang)
Base = declarative_base()

# Dependency Injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()