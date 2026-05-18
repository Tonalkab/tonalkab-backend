from pydantic import BaseModel
from typing import Optional

# 1. Esquema genérico para los catálogos pequeños (Luz, Suelo, etc.)
class CatalogoBase(BaseModel):
    id: int
    valor: str

    class Config:
        from_attributes = True


# 2. Esquema completo e integral para el Tipo de Planta (Ficha Botánica completa)
class TipoPlantaResponse(BaseModel):
    id_tipo_planta: int
    nombre_planta: str
    
    # 📊 RANGOS AMBIENTALES ÓPTIMOS (Mapeados como float por los DECIMAL de la BD)
    humedad_suelo_min: float
    humedad_suelo_max: float
    humedad_ambiente_min: float
    humedad_ambiente_max: float
    temperatura_min: float
    temperatura_max: float
    
    # ⚙️ ESPECIFICACIONES TÉCNICAS DE CULTIVO
    tiempo_min_entre_riegos_dias: int
    profundidad_raiz_cm: int
    nivel_dificultad: int
    
    # 🔗 LLAVES FORÁNEAS A OTROS CATÁLOGOS
    sensibilidad_luz_id: int
    tolerancia_exceso_agua_id: int
    tipo_planta_categoria_id: int
    tipo_suelo_id: int
    consumo_agua_id: int
    
    # 📖 TEXTOS LARGOS E IMÁGENES (Campos opcionales para evitar errores si están vacíos)
    descripcion: Optional[str] = None
    origen_geografico: Optional[str] = None
    historia: Optional[str] = None
    cuidados_generales: Optional[str] = None
    imagen_url: Optional[str] = None

    class Config:
        from_attributes = True  # Permite a Pydantic leer los objetos ORM de SQLAlchemy directamente