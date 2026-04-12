from pydantic import BaseModel
from typing import Optional

# 1. Esquema genérico para los catálogos pequeños (Luz, Suelo, etc.)
class CatalogoBase(BaseModel):
    id: int
    valor: str

    class Config:
        from_attributes = True

# 2. Esquema completo para el Tipo de Planta
class TipoPlantaResponse(BaseModel):
    id_tipo_planta: int
    nombre_planta: str
    humedad_suelo_min: float
    humedad_suelo_max: float
    temperatura_min: float
    temperatura_max: float
    tiempo_min_entre_riegos_dias: int
    nivel_dificultad: int
    
    # Textos y fotos que le sirven a la App
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None

    class Config:
        from_attributes = True