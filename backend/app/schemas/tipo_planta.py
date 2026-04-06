from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models.tipo_planta import TipoPlanta
from app.schemas.tipo_planta import TipoPlantaResponse

router = APIRouter(prefix="/tipos-plantas", tags=["Catálogo de Plantas"])

@router.get("/", response_model=List[TipoPlantaResponse])
def listar_tipos_plantas(db: Session = Depends(get_db)):
    """
    Devuelve el catálogo completo de plantas con sus umbrales y cuidados.
    """
    return db.query(TipoPlanta).all()