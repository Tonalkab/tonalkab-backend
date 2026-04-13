from sqlalchemy import Column, Integer, String, TEXT, ForeignKey, DateTime, Boolean
from datetime import datetime
from app.db import Base

# --- CATÁLOGOS DE SOPORTE ---

class TipoAlerta(Base):
    """
    1: baja_humedad, 2: bateria_baja, 3: desconexion, 4: nivel_agua_bajo
    """
    __tablename__ = "tipo_alerta"
    id_tipo_alerta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)

class PrioridadAlerta(Base):
    """
    1: baja, 2: media, 3: alta
    """
    __tablename__ = "prioridad_alerta"
    id_prioridad_alerta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)

class EstadoAlerta(Base):
    """
    1: pendiente, 2: vista, 3: resuelta
    """
    __tablename__ = "estado_alerta"
    id_estado_alerta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)

# --- ENTIDAD PRINCIPAL ---

class Alerta(Base):
    __tablename__ = "alerta"

    id_alerta = Column(Integer, primary_key=True, index=True)
    id_maceta = Column(Integer, ForeignKey("macetas.id_maceta"), nullable=False)
    
    id_tipo_alerta = Column(Integer, ForeignKey("tipo_alerta.id_tipo_alerta"), nullable=False)
    mensaje = Column(TEXT, nullable=False)
    
    fecha_hora = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    id_estado_alerta = Column(Integer, ForeignKey("estado_alerta.id_estado_alerta"), nullable=False, default=1) # 1 = pendiente
    id_prioridad_alerta = Column(Integer, ForeignKey("prioridad_alerta.id_prioridad_alerta"), nullable=False)
    
    vista_usuario = Column(Boolean, default=False, nullable=False)