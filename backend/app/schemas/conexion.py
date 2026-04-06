from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Lo que envía el ESP32
class ConexionReport(BaseModel):
    ssid: str
    rssi: int
    ip_dispositivo: str

# Lo que le enviamos a la App Móvil
class ConexionResponse(ConexionReport):
    id_conexion: int
    estado_conexion: str
    ultima_conexion: datetime
    # Estos campos los calcularemos con Python en tiempo real
    estado_real: str 
    minutos_desconectado: int 

    class Config:
        from_attributes = True