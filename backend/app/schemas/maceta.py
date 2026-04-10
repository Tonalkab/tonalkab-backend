from pydantic import BaseModel
from datetime import datetime


class MacetaCreate(BaseModel):
    nombre_maceta: str
    id_tipo_planta: int


class MacetaResponse(BaseModel):
    id_maceta: int
    nombre_maceta: str
    id_tipo_planta: int
    id_estado_dispositivo: int
    fecha_registro: datetime

    class Config:
        from_attributes = True


class MacetaUpdatePlanta(BaseModel):
    id_tipo_planta: int

class ConfiguracionCreate(BaseModel):
    humedad_suelo_min: float
    humedad_suelo_max: float
    tiempo_min_entre_riegos_dias: int
    modo_operacion: str = "edge_auto" # Puede cambiarse a "manual" si quieres forzar a la IA a ignorar este dispositivo