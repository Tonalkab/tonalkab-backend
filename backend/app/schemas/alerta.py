from pydantic import BaseModel
from datetime import datetime

class AlertaResponse(BaseModel):
    id_alerta: int
    id_maceta: int
    id_tipo_alerta: int
    mensaje: str
    fecha_hora: datetime
    id_estado_alerta: int
    id_prioridad_alerta: int
    vista_usuario: bool

    class Config:
        from_attributes = True # Permite leer desde SQLAlchemy