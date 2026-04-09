from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime, Boolean
from datetime import datetime
from app.db import Base

class ConfiguracionMaceta(Base):
    __tablename__ = "configuracion_maceta"

    id_configuracion = Column(Integer, primary_key=True, index=True)
    id_maceta = Column(Integer, ForeignKey("macetas.id_maceta"), nullable=False)
    fecha_configuracion = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    humedad_suelo_min = Column(DECIMAL(5, 2), nullable=False)
    humedad_suelo_max = Column(DECIMAL(5, 2), nullable=False)
    tiempo_min_entre_riegos_dias = Column(Integer, nullable=False)
    
    modo_operacion = Column(String(20), nullable=False, default="edge_auto") # "edge_auto" o "manual"
    origen_configuracion = Column(String(50), nullable=False, default="sistema") # "usuario" o "sistema"
    activa = Column(Boolean, nullable=False, default=True)