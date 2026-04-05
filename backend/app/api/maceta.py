from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db
from app.models.maceta import Maceta
from app.schemas.maceta import MacetaCreate
from app.core.security import generate_device_token, hash_device_token
from app.api.auth import get_current_user



router = APIRouter(prefix="/macetas", tags=["Macetas"])


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