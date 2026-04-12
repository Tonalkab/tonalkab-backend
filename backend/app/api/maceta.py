from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.db import get_db
from app.models.maceta import Maceta
from app.models.lectura import LecturaSensores
from app.schemas.maceta import MacetaCreate
from app.schemas.device import LecturaResponse 
from app.core.security import generate_device_token, hash_device_token
from app.api.auth import get_current_user

from app.models.configuracion_maceta import ConfiguracionMaceta
from app.models.tipo_planta import TipoPlanta
from app.schemas.maceta import MacetaUpdatePlanta, ConfiguracionCreate

router = APIRouter(prefix="/macetas", tags=["Macetas"])

# ==========================================
# FUNCIÓN AUXILIAR DE SEGURIDAD
# ==========================================
def verificar_propiedad_maceta(id_maceta: int, id_usuario: int, db: Session):
    """Verifica que la maceta exista y pertenezca al usuario autenticado"""
    maceta = db.query(Maceta).filter(
        Maceta.id_maceta == id_maceta, 
        Maceta.id_usuario == id_usuario
    ).first()
    
    if not maceta:
        raise HTTPException(
            status_code=403, 
            detail="No tienes permisos para acceder a esta maceta o no existe."
        )
    return maceta

# ==========================================
# ENDPOINT: Crear Maceta
# ==========================================
@router.post("/")
def create_maceta(
    maceta_data: MacetaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1. Generar token plano
    token = generate_device_token()

    # 2. Hashear token
    token_hash = hash_device_token(token)

    # 3. Crear maceta
    nueva_maceta = Maceta(
        id_usuario=current_user.id_usuario,
        nombre_maceta=maceta_data.nombre_maceta,
        token_hash=token_hash,
        id_tipo_planta=maceta_data.id_tipo_planta,
        id_estado_dispositivo=2,
        fecha_registro=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(nueva_maceta)
    db.commit()
    db.refresh(nueva_maceta)

    # 4. Retornar token SOLO UNA VEZ
    return {
        "id_maceta": nueva_maceta.id_maceta,
        "token": token
    }

# ==========================================
# ENDPOINT: Lectura Actual (Tiempo Real)
# ==========================================
@router.get("/{id_maceta}/lecturas/actual", response_model=LecturaResponse)
def obtener_lectura_actual(
    id_maceta: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)):
    # 1. Validar propiedad
    verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    # 2. Obtener solo la última lectura
    lectura = db.query(LecturaSensores)\
                .filter(LecturaSensores.id_maceta == id_maceta)\
                .order_by(LecturaSensores.fecha_hora.desc())\
                .first()

    if not lectura:
        raise HTTPException(status_code=404, detail="Aún no hay lecturas para esta maceta.")

    return lectura

# ==========================================
# ENDPOINT: Historial de Lecturas (Paginado y Filtrado)
# ==========================================
@router.get("/{id_maceta}/lecturas/historial", response_model=List[LecturaResponse])
def obtener_historial_lecturas(
    id_maceta: int,
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (YYYY-MM-DDTHH:MM:SS)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (YYYY-MM-DDTHH:MM:SS)"),
    limit: int = Query(50, ge=1, le=1000, description="Cantidad máxima de registros"),
    offset: int = Query(0, ge=0, description="Registros a omitir (paginación)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)):
    # 1. Validar propiedad
    verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    # 2. Construir la consulta base
    query = db.query(LecturaSensores).filter(LecturaSensores.id_maceta == id_maceta)

    # 3. Aplicar filtros de fecha dinámicamente
    if fecha_inicio:
        query = query.filter(LecturaSensores.fecha_hora >= fecha_inicio)
    if fecha_fin:
        query = query.filter(LecturaSensores.fecha_hora <= fecha_fin)

    # 4. Ordenar descendente, aplicar paginación y ejecutar
    lecturas = query.order_by(LecturaSensores.fecha_hora.desc())\
                    .offset(offset)\
                    .limit(limit)\
                    .all()

    return lecturas

# ==========================================
# ENDPOINT: Cambiar Tipo de Planta
# ==========================================
@router.patch("/{id_maceta}/planta")
def cambiar_planta_maceta(
    id_maceta: int,
    datos: MacetaUpdatePlanta,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Permite al usuario indicar que sembró una planta distinta en su maceta.
    """
    # 1. Validar que la maceta es del usuario
    maceta = verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    # 2. Validar que la nueva planta exista en el catálogo
    nueva_planta = db.query(TipoPlanta).filter(TipoPlanta.id_tipo_planta == datos.id_tipo_planta).first()
    if not nueva_planta:
        raise HTTPException(status_code=404, detail="El tipo de planta especificado no existe en el catálogo.")

    # 3. Actualizar la maceta
    maceta.id_tipo_planta = datos.id_tipo_planta
    
    # 4. LIMPIEZA: Si el usuario cambia de planta, desactivamos cualquier configuración manual 
    # vieja para que la nueva planta respire con su biología natural por defecto.
    db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == id_maceta,
        ConfiguracionMaceta.activa == True
    ).update({"activa": False})

    db.commit()

    return {
        "status": "success", 
        "message": f"Maceta actualizada. Nueva planta: {nueva_planta.nombre_planta}",
        "id_tipo_planta": maceta.id_tipo_planta
    }

# ==========================================
# ENDPOINT: Forzar Configuración Manual
# ==========================================
@router.post("/{id_maceta}/configuracion")
def establecer_configuracion_manual(
    id_maceta: int,
    config: ConfiguracionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Permite al usuario anular la biología de la planta y establecer sus propios umbrales desde la App.
    """
    # 1. Validar propiedad
    verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    # 2. Desactivar la configuración anterior (Solo puede haber UNA activa por maceta)
    db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == id_maceta,
        ConfiguracionMaceta.activa == True
    ).update({"activa": False})

    # 3. Crear la nueva configuración
    nueva_config = ConfiguracionMaceta(
        id_maceta=id_maceta,
        humedad_suelo_min=config.humedad_suelo_min,
        humedad_suelo_max=config.humedad_suelo_max,
        tiempo_min_entre_riegos_dias=config.tiempo_min_entre_riegos_dias,
        modo_operacion=config.modo_operacion,
        origen_configuracion="usuario",
        activa=True
    )

    db.add(nueva_config)
    db.commit()
    db.refresh(nueva_config)

    return {
        "status": "success", 
        "message": "Configuración manual establecida. El ESP32 la descargará en su próximo ciclo.",
        "id_configuracion": nueva_config.id_configuracion
    }

# app/api/maceta.py

@router.get("/", response_model=List[MacetaResponse])
def listar_macetas(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retorna todas las macetas que pertenecen al usuario autenticado. [cite: 65, 114]
    """
    macetas = db.query(Maceta).filter(
        Maceta.id_usuario == current_user.id_usuario
    ).all()
    
    return macetas