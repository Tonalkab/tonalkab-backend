from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db

# Importamos tus modelos de base de datos
from app.models.tipo_planta import TipoPlanta
from app.models import catalogos_planta as cat_models

# Importamos los esquemas que acabamos de crear en el Paso 1
from app.schemas.botanica import CatalogoBase, TipoPlantaResponse

router = APIRouter(prefix="/catalogos", tags=["Catálogos Botánicos"])

# 🌿 Endpoint principal: Lista de Plantas
@router.get("/plantas", response_model=List[TipoPlantaResponse])
def listar_plantas(db: Session = Depends(get_db)):
    """Devuelve todas las plantas con sus parámetros ambientales."""
    return db.query(TipoPlanta).all()

# ☀️ Endpoint: Sensibilidad a la Luz
@router.get("/luz", response_model=List[CatalogoBase])
def listar_luz(db: Session = Depends(get_db)):
    resultados = db.query(cat_models.SensibilidadLuz).all()
    # Mapeamos id_sensibilidad_luz -> id
    return [{"id": r.id_sensibilidad_luz, "valor": r.valor} for r in resultados]

# 🪨 Endpoint: Tipos de Suelo
@router.get("/suelos", response_model=List[CatalogoBase])
def listar_suelos(db: Session = Depends(get_db)):
    resultados = db.query(cat_models.TipoSuelo).all()
    # Mapeamos id_tipo_suelo -> id
    return [{"id": r.id_tipo_suelo, "valor": r.valor} for r in resultados]

# 💧 Endpoint: Consumo de Agua
@router.get("/consumo-agua", response_model=List[CatalogoBase])
def listar_consumo(db: Session = Depends(get_db)):
    resultados = db.query(cat_models.ConsumoAgua).all()
    # Mapeamos id_consumo -> id
    return [{"id": r.id_consumo, "valor": r.valor} for r in resultados]