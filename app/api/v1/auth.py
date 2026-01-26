import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Skema Bearer Token (Authorization: Bearer <token>)
security = HTTPBearer()

# Variable global biar init cuma sekali
firebase_app = None

def init_firebase():
    """Inisialisasi Firebase Admin dengan Service Account"""
    global firebase_app
    
    # Path file di dalam Docker (sesuai volume mapping kita kemarin)
    cred_path = "/code/app/serviceAccountKey.json"
    
    if not os.path.exists(cred_path):
        print(f"⚠️ WARNING: File {cred_path} tidak ditemukan! Auth tidak akan jalan.")
        return

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_app = firebase_admin.initialize_app(cred)
            print("🔥 Firebase Admin Initialized!")
    except Exception as e:
        print(f"❌ Error Init Firebase: {e}")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency untuk memvalidasi Token Firebase.
    Mengembalikan UID user jika valid.
    """
    token = credentials.credentials
    try:
        # Minta Firebase verifikasi token ini valid atau palsu
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        return uid
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Expired. Silakan login ulang di HP.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Tidak Valid / Palsu.",
        )