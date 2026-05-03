from pydantic import BaseModel
from datetime import datetime
from typing import Optional 

# Importamos el esquema de la Skin
from app.schemas.skin import SkinBase

class MacetaCreate(BaseModel):
    nombre_maceta: str
    id_tipo_planta: int


class MacetaResponse(BaseModel):
    id_maceta: int
    nombre_maceta: str
    id_tipo_planta: int
    id_estado_dispositivo: int
    fecha_registro: datetime
    
    # Campo para incluir la skin activa de la maceta
    skin_activa: Optional[SkinBase] = None

    class Config:
        from_attributes = True

# --- NUEVO ESQUEMA ---
class MacetaCreateResponse(MacetaResponse):
    token: str  # Se devuelve el token plano solo al crear

class MacetaUpdatePlanta(BaseModel):
    id_tipo_planta: int


class ConfiguracionCreate(BaseModel):
    humedad_suelo_min: float
    humedad_suelo_max: float
    tiempo_min_entre_riegos_dias: int
    modo_operacion: str = "edge_auto"