from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class LecturaCreate(BaseModel):
    humedad_suelo: float 
    temperatura: float
    humedad_ambiental: float = 0.0
    nivel_luz: int = 0
    nivel_agua: int = 0
    voltaje_bateria: float = 0.0

class LecturaResponse(LecturaCreate):
    id_lectura: int
    id_maceta: int
    fecha_hora: datetime

    class Config:
        from_attributes = True # Permite leer desde el modelo de SQLAlchemy