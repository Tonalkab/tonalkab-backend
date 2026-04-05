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