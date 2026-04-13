from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models.alerta import Alerta
from app.models.maceta import Maceta
from app.schemas.alerta import AlertaResponse
from app.api.auth import get_current_user

router = APIRouter(tags=["Alertas y Notificaciones"])

def verificar_propiedad_maceta(id_maceta: int, id_usuario: int, db: Session):
    """Función auxiliar para seguridad: verifica que la maceta sea del usuario autenticado."""
    maceta = db.query(Maceta).filter(
        Maceta.id_maceta == id_maceta, 
        Maceta.id_usuario == id_usuario
    ).first()
    if not maceta:
        raise HTTPException(status_code=403, detail="No tienes permisos o la maceta no existe.")
    return maceta

# ==========================================
# 1. OBTENER ALERTAS DE UNA MACETA
# ==========================================
@router.get("/macetas/{id_maceta}/alertas", response_model=List[AlertaResponse])
def obtener_alertas(
    id_maceta: int,
    solo_pendientes: bool = True, # Por defecto, la app solo quiere ver lo que no ha leído
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Devuelve la lista de alertas para una maceta específica.
    """
    # 1. Seguridad de propiedad
    verificar_propiedad_maceta(id_maceta, current_user.id_usuario, db)
    
    # 2. Construir la consulta
    query = db.query(Alerta).filter(Alerta.id_maceta == id_maceta)
    
    # 3. Filtrar según lo que pida la App
    if solo_pendientes:
        query = query.filter(Alerta.id_estado_alerta == 1) # 1 = Pendiente
        
    # 4. Ordenar: las más recientes primero
    alertas = query.order_by(Alerta.fecha_hora.desc()).all()
    
    return alertas

# ==========================================
# 2. MARCAR ALERTA COMO VISTA (Descartar)
# ==========================================
@router.patch("/alertas/{id_alerta}/vista")
def marcar_alerta_vista(
    id_alerta: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Permite al usuario marcar una alerta como leída desde la App.
    """
    # Hacemos un JOIN con Maceta para asegurarnos de que el usuario sea el dueño
    # de la maceta que generó esta alerta en particular.
    alerta = db.query(Alerta).join(Maceta).filter(
        Alerta.id_alerta == id_alerta,
        Maceta.id_usuario == current_user.id_usuario
    ).first()
    
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada o acceso denegado.")
        
    # Actualizamos el estado
    alerta.vista_usuario = True
    alerta.id_estado_alerta = 2 # 2 = Vista
    db.commit()
    
    return {"status": "success", "message": "Alerta marcada como vista correctamente."}