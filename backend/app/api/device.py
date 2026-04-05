from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.maceta import Maceta
from app.core.security import hash_device_token
from app.schemas.device import LecturaCreate

# Creamos el router específico para la API del hardware
router = APIRouter(prefix="/devices", tags=["Dispositivos IoT (ESP32)"])

# Definimos el header que el ESP32 deberá enviar en sus peticiones
api_key_header = APIKeyHeader(name="X-Device-Token", auto_error=True)

# ==============================
# DEPENDENCIA DE AUTENTICACIÓN IoT
# ==============================
def get_current_device(
    token: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """
    Valida el token enviado por el ESP32.
    """
    # 1. Hashear el token plano recibido [cite: 262]
    token_hash = hash_device_token(token)

    # 2. Buscar en la base de datos la maceta con ese hash [cite: 146]
    maceta = db.query(Maceta).filter(Maceta.token_hash == token_hash).first()

    # 3. Si no existe o no coincide, rechazar la conexión
    if not maceta:
        raise HTTPException(
            status_code=401, 
            detail="Token de dispositivo inválido o maceta no encontrada"
        )

    # Opcional: Validar si está dada de baja o en estado "eliminado"
    # if maceta.id_estado_dispositivo == X: ...

    return maceta

# ==============================
# ENDPOINT 1: PRUEBA DE AUTH
# ==============================
@router.post("/auth")
def auth_device(current_device: Maceta = Depends(get_current_device)):
    """
    Endpoint para que el ESP32 verifique que su token es válido al arrancar.
    """
    # Si llega aquí, el token es válido
    # Pasamos el estado de la maceta a 1 (activo)
    # (Podrías hacer el db.commit() aquí si deseas actualizar el estado real)
    
    return {
        "message": "Dispositivo autenticado",
        "id_maceta": current_device.id_maceta,
        "nombre": current_device.nombre_maceta
    }

# ==============================
# ENDPOINT 2: RECIBIR LECTURAS
# ==============================
@router.post("/lecturas")
def receive_lecturas(
    lectura: LecturaCreate,
    current_device: Maceta = Depends(get_current_device)
):
    """
    Simulación de recepción de datos del ESP32.
    """
    # Aquí en el futuro guardarás en la tabla 'LecturaSensores'
    
    # Por ahora, simplemente imprimimos en consola
    print(f"📡 [DATA] Maceta: {current_device.nombre_maceta} (ID: {current_device.id_maceta})")
    print(f"💧 Humedad: {lectura.humedad}% | 🌡️ Temperatura: {lectura.temperatura}°C")

    return {
        "message": "Datos recibidos correctamente",
        "id_maceta": current_device.id_maceta,
        "registrado": {
            "humedad": lectura.humedad,
            "temperatura": lectura.temperatura
        }
    }