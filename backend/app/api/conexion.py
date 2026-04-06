from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db
from app.models.conexion import ConexionDispositivo
from app.models.maceta import Maceta
from app.schemas.conexion import ConexionReport, ConexionResponse
from app.api.auth import get_current_user
from app.api.device import get_current_device 

router = APIRouter(tags=["Conexión y Red"])

# ==========================================
# 1. ESP32 REPORTA SU CONEXIÓN (Heartbeat)
# ==========================================
@router.post("/devices/conexion")
def reportar_conexion(
    reporte: ConexionReport,
    current_device: Maceta = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    # Buscamos si la maceta ya tiene un registro de red
    conexion = db.query(ConexionDispositivo).filter(ConexionDispositivo.id_maceta == current_device.id_maceta).first()
    
    if conexion:
        # Si ya existe, actualizamos los datos (la fecha se actualiza sola por el onupdate del modelo)
        conexion.ssid = reporte.ssid
        conexion.rssi = reporte.rssi
        conexion.ip_dispositivo = reporte.ip_dispositivo
        conexion.estado_conexion = "conectado"
    else:
        # Si es la primera vez que se conecta, creamos el registro
        conexion = ConexionDispositivo(
            id_maceta=current_device.id_maceta,
            ssid=reporte.ssid,
            rssi=reporte.rssi,
            ip_dispositivo=reporte.ip_dispositivo
        )
        db.add(conexion)
    
    # Marcamos la maceta como ACTIVA (1) en el catálogo general
    current_device.id_estado_dispositivo = 1
    
    db.commit()
    return {"status": "success", "message": "Estado de red actualizado"}

# ==========================================
# 2. APP MÓVIL CONSULTA EL ESTADO
# ==========================================
@router.get("/macetas/{id_maceta}/conexion", response_model=ConexionResponse)
def obtener_estado_conexion(
    id_maceta: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificamos que la maceta exista y sea del usuario
    maceta = db.query(Maceta).filter(Maceta.id_maceta == id_maceta, Maceta.id_usuario == current_user.id_usuario).first()
    if not maceta:
        raise HTTPException(status_code=403, detail="Maceta no encontrada o sin acceso.")

    conexion = db.query(ConexionDispositivo).filter(ConexionDispositivo.id_maceta == id_maceta).first()
    if not conexion:
        raise HTTPException(status_code=404, detail="La maceta nunca se ha conectado a la red.")

    # ⏱️ LÓGICA DE DESCONEXIÓN: Calculamos cuánto tiempo ha pasado
    ahora = datetime.utcnow()
    diferencia = ahora - conexion.ultima_conexion
    minutos_inactivos = int(diferencia.total_seconds() / 60)

    # Si pasaron más de 5 minutos sin que el ESP32 reporte nada, lo damos por muerto/desconectado
    estado_real = "conectado"
    if minutos_inactivos > 5:
        estado_real = "desconectado"
        # Actualizamos el estado general de la maceta a DESCONECTADO (2)
        if maceta.id_estado_dispositivo != 2:
            maceta.id_estado_dispositivo = 2
            db.commit()

    # Construimos la respuesta manual combinando la BD y nuestros cálculos
    return {
        "ssid": conexion.ssid,
        "rssi": conexion.rssi,
        "ip_dispositivo": conexion.ip_dispositivo,
        "id_conexion": conexion.id_conexion,
        "estado_conexion": conexion.estado_conexion,
        "ultima_conexion": conexion.ultima_conexion,
        "estado_real": estado_real,
        "minutos_desconectado": minutos_inactivos if estado_real == "desconectado" else 0
    }