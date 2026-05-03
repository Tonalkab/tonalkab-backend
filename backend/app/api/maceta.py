from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

# Dependencias y Modelos principales
from app.db import get_db
from app.api.auth import get_current_user
from app.core.security import generate_device_token, hash_device_token

from app.models.maceta import Maceta
from app.models.lectura import LecturaSensores
from app.models.configuracion_maceta import ConfiguracionMaceta
from app.models.tipo_planta import TipoPlanta
from app.models.skin import UsuarioSkin, MacetaSkin

# Esquemas (Pydantic) - IMPORTACIÓN ACTUALIZADA
from app.schemas.maceta import MacetaCreate, MacetaResponse, MacetaCreateResponse, MacetaUpdatePlanta, ConfiguracionCreate
from app.schemas.device import LecturaResponse 

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
# ENDPOINT: Crear Maceta (Unificado y Seguro)
# ==========================================
@router.post("/", response_model=MacetaCreateResponse) # <-- SE USA EL NUEVO ESQUEMA
def registrar_maceta(
    maceta_data: MacetaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Registra una maceta, genera su token de hardware y le asigna la skin por defecto."""
    
    # 1. Generar token plano y su hash
    token_plano = generate_device_token()
    token_hash = hash_device_token(token_plano)

    # 2. Crear registro de la maceta
    db_maceta = Maceta(
        id_usuario=current_user.id_usuario,
        nombre_maceta=maceta_data.nombre_maceta,
        token_hash=token_hash,
        id_tipo_planta=maceta_data.id_tipo_planta,
        id_estado_dispositivo=2,
        fecha_registro=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_maceta)
    db.flush() 

    # 3. Asignar y equipar la skin predefinida (ID 1)
    skin_inicial = MacetaSkin(
        id_maceta=db_maceta.id_maceta,
        id_skin=1, 
        equipado=True 
    )
    db.add(skin_inicial)
    
    # 4. Guardar en base de datos
    db.commit()
    db.refresh(db_maceta)
    
    # 5. Forzar la carga de la relación para que Pydantic no devuelva "null"
    _ = db_maceta.skins_maceta 

    # 6. INYECTAR EL TOKEN PLANO para que el esquema lo devuelva al usuario
    db_maceta.token = token_plano

    return db_maceta

# ==========================================
# ENDPOINT: Listar Macetas
# ==========================================
@router.get("/", response_model=List[MacetaResponse])
def listar_macetas(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Retorna todas las macetas que pertenecen al usuario autenticado."""
    macetas = db.query(Maceta).filter(
        Maceta.id_usuario == current_user.id_usuario
    ).all()
    
    return macetas

# ==========================================
# ENDPOINT: Lectura Actual (Tiempo Real)
# ==========================================
@router.get("/{id_maceta}/lecturas/actual", response_model=LecturaResponse)
def obtener_lectura_actual(
    id_maceta: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    lectura = db.query(LecturaSensores)\
                .filter(LecturaSensores.id_maceta == id_maceta)\
                .order_by(LecturaSensores.fecha_hora.desc())\
                .first()

    if not lectura:
        raise HTTPException(status_code=404, detail="Aún no hay lecturas para esta maceta.")

    return lectura

# ==========================================
# ENDPOINT: Historial de Lecturas
# ==========================================
@router.get("/{id_maceta}/lecturas/historial", response_model=List[LecturaResponse])
def obtener_historial_lecturas(
    id_maceta: int,
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (YYYY-MM-DDTHH:MM:SS)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (YYYY-MM-DDTHH:MM:SS)"),
    limit: int = Query(50, ge=1, le=1000, description="Cantidad máxima de registros"),
    offset: int = Query(0, ge=0, description="Registros a omitir (paginación)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    query = db.query(LecturaSensores).filter(LecturaSensores.id_maceta == id_maceta)

    if fecha_inicio:
        query = query.filter(LecturaSensores.fecha_hora >= fecha_inicio)
    if fecha_fin:
        query = query.filter(LecturaSensores.fecha_hora <= fecha_fin)

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
    maceta = verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    nueva_planta = db.query(TipoPlanta).filter(TipoPlanta.id_tipo_planta == datos.id_tipo_planta).first()
    if not nueva_planta:
        raise HTTPException(status_code=404, detail="El tipo de planta no existe en el catálogo.")

    maceta.id_tipo_planta = datos.id_tipo_planta
    
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
    verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == id_maceta,
        ConfiguracionMaceta.activa == True
    ).update({"activa": False})

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

# ==========================================
# ENDPOINT: Equipar Skin en la Maceta
# ==========================================
@router.post("/{id_maceta}/skins/{id_skin}/equipar")
def cambiar_skin_maceta(
    id_maceta: int, 
    id_skin: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    maceta = verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)

    skin_desbloqueada = db.query(UsuarioSkin).filter(
        UsuarioSkin.id_usuario == current_user.id_usuario,
        UsuarioSkin.id_skin == id_skin
    ).first()

    if not skin_desbloqueada:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Primero debes desbloquear esta skin para poder usarla en tus macetas"
        )

    skin_maceta = db.query(MacetaSkin).filter(
        MacetaSkin.id_maceta == id_maceta,
        MacetaSkin.id_skin == id_skin
    ).first()

    if not skin_maceta:
        skin_maceta = MacetaSkin(id_maceta=id_maceta, id_skin=id_skin, equipado=False)
        db.add(skin_maceta)

    db.query(MacetaSkin).filter(
        MacetaSkin.id_maceta == id_maceta
    ).update({"equipado": False})

    skin_maceta.equipado = True
    db.commit()

    return {"message": f"Skin actualizada exitosamente para la maceta {maceta.nombre_maceta}"}