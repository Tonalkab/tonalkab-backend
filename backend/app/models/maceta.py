from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.db import Base
from app.models.tipo_planta import TipoPlanta


class Maceta(Base):
    __tablename__ = "macetas"

    id_maceta = Column(Integer, primary_key=True, index=True)
    
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    
    nombre_maceta = Column(String(100), nullable=False)
    
    token_hash = Column(String(255), nullable=False)
    
    id_tipo_planta = Column(Integer, ForeignKey("tipo_planta.id_tipo_planta"), nullable=False)
    
    id_estado_dispositivo = Column(Integer, nullable=False, default=2)  # 2 = desconectado
    
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)