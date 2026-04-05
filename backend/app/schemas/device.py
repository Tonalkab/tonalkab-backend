from pydantic import BaseModel

class LecturaCreate(BaseModel):
    humedad: float
    temperatura: float
    # Puedes añadir más campos futuros aquí (ej. nivel_agua, bateria)