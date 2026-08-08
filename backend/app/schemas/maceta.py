from pydantic import BaseModel
from datetime import datetime
from typing import Optional 

# Importamos los esquemas relacionados
from app.schemas.skin import SkinBase
from app.schemas.botanica import TipoPlantaResponse
from app.schemas.device import LecturaResponse
from app.schemas.conexion import ConexionResponse

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

# --- ESQUEMA UNIFICADO DE DASHBOARD (ELIMINA N+1 QUERIES) ---
class MacetaDashboardResponse(BaseModel):
    id_maceta: int
    nombre_maceta: str
    id_tipo_planta: int
    id_estado_dispositivo: int
    fecha_registro: datetime
    skin_activa: Optional[SkinBase] = None
    tipo_planta: Optional[TipoPlantaResponse] = None
    lectura: Optional[LecturaResponse] = None
    conexion: Optional[ConexionResponse] = None

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

# --- ESQUEMA PARA FORZAR RIEGO (NUEVO) ---
class ForzarRiegoEdgeRequest(BaseModel):
    segundos: Optional[int] = None