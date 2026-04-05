from pydantic import BaseModel
from typing import Optional

class LecturaCreate(BaseModel):
    humedad_suelo: float 
    temperatura: float
    humedad_ambiental: float = 0.0
    nivel_luz: int = 0
    nivel_agua: int = 0
    voltaje_bateria: float = 0.0