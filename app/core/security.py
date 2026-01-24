import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# 1. Inisialisasi Firebase Admin (Cuma boleh sekali)
if not firebase_admin._apps:
    # Pastikan path ini sesuai dengan tempat kamu taruh file JSON tadi
    cred_path = "app/serviceAccountKey.json"
    
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print("⚠️ PERINGATAN: serviceAccountKey.json tidak ditemukan! Auth tidak akan jalan.")

# 2. Skema Security (Bearer Token)
security = HTTPBearer()

# 3. Fungsi Validasi Token (Dependency)
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    try:
        # Minta Firebase cek apakah token ini asli?
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        return uid
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Kadaluarsa. Silakan login ulang.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # --- TAMBAHAN: PRINT ERROR ASLI KE TERMINAL ---
        print(f"❌ ERROR VERIFIKASI TOKEN: {str(e)}") 
        # ----------------------------------------------
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token Error: {str(e)}", # Tampilkan detail error ke response biar kelihatan di script python
            headers={"WWW-Authenticate": "Bearer"},
        )