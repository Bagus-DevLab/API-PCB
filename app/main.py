from fastapi import FastAPI
import os

app = FastAPI(title="IoT Backend API")

@app.get("/")
def read_root():
    return {
        "message": "Halo Bro! Backend FastAPI + Docker sudah jalan!",
        "database_user": os.getenv("DB_USER"), # Ngetes apakah .env terbaca
        "mqtt_broker": os.getenv("MQTT_BROKER")
    }