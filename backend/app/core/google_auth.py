from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "tu-client-id-aqui")

def verify_google_token(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # 🔐 Validación extra de seguridad
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid issuer")

        return idinfo

    except ValueError:
        raise HTTPException(status_code=400, detail="Token de Google inválido")