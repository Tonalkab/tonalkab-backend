from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.maceta import Maceta
from app.models.lectura import LecturaSensores
from app.core.security import hash_device_token
from app.schemas.device import LecturaCreate

# Configuración del Router y Seguridad
router = APIRouter(prefix="/devices", tags=["Dispositivos IoT (ESP32)"])

# Definimos el header que el ESP32 debe enviar
api_key_header = APIKeyHeader(name="X-Device-Token", auto_error=True)

# ==========================================
# DEPENDENCIA: Autenticación del Dispositivo
# ==========================================
def get_current_device(
    token: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """
    Valida el token plano enviado por el hardware.
    """
    token_hash = hash_device_token(token)
    maceta = db.query(Maceta).filter(Maceta.token_hash == token_hash).first()

    if not maceta:
        raise HTTPException(
            status_code=401, 
            detail="Token de dispositivo inválido o maceta no encontrada"
        )

    return maceta

# ==========================================
# ENDPOINT: Verificación de Conexión (Auth)
# ==========================================
@router.post("/auth")
def auth_device(current_device: Maceta = Depends(get_current_device)):
    """
    Endpoint para que el ESP32 valide su llave al arrancar.
    """
    return {
        "message": "Dispositivo autenticado correctamente",
        "id_maceta": current_device.id_maceta,
        "nombre": current_device.nombre_maceta
    }

# ==========================================
# ENDPOINT: Recepción de Lecturas Sensores
# ==========================================
@router.post("/lecturas")
def receive_lecturas(
    lectura: LecturaCreate,
    current_device: Maceta = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Recibe los datos del ESP32 y los guarda en la tabla lectura_sensores.
    """
    # 1. LOGS CORREGIDOS: Accedemos a .humedad_suelo en lugar de .humedad
    print(f"📡 [DATA] Maceta: {current_device.nombre_maceta} (ID: {current_device.id_maceta})")
    print(f"🌱 Humedad Suelo: {lectura.humedad_suelo}% | 🌡️ Temp: {lectura.temperatura}°C")

    # 2. CREACIÓN DEL OBJETO (Mapeo directo)
    nueva_lectura = LecturaSensores(
        id_maceta=current_device.id_maceta,
        humedad_suelo=lectura.humedad_suelo,
        temperatura=lectura.temperatura,
        humedad_ambiental=lectura.humedad_ambiental,
        nivel_luz=lectura.nivel_luz,
        nivel_agua=lectura.nivel_agua,
        voltaje_bateria=lectura.voltaje_bateria,
        lluvia_detectada=lectura.lluvia_detectada
    )

    # 3. GUARDADO EN DB
    db.add(nueva_lectura)
    db.commit()
    db.refresh(nueva_lectura)

    return {
        "status": "success", 
        "id_lectura": nueva_lectura.id_lectura,
        "registrado": {
            "humedad_suelo": lectura.humedad_suelo,
            "humedad_ambiental": lectura.humedad_ambiental,
            "temperatura": lectura.temperatura
        }
    }