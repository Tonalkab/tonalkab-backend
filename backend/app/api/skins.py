from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models.skin import Skin
from app.schemas.skin import SkinBase
from app.api.auth import get_current_user

router = APIRouter(prefix="/skins", tags=["Skins"])

@router.get("/", response_model=List[SkinBase])
def get_catalogo_skins(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) # Opcional: si quieres que solo usuarios logueados vean la tienda
):
    """Devuelve todo el catálogo de skins disponibles en el sistema."""
    return db.query(Skin).all()