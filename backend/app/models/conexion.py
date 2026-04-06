from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.db import Base

class ConexionDispositivo(Base):
    __tablename__ = "conexion_dispositivo"

    id_conexion = Column(Integer, primary_key=True, index=True)
    id_maceta = Column(Integer, ForeignKey("macetas.id_maceta"), nullable=False)
    
    ssid = Column(String(100), nullable=False)
    rssi = Column(Integer, nullable=False) # Intensidad de la señal Wi-Fi
    ip_dispositivo = Column(String(45), nullable=False)
    tipo_red = Column(String(20), default="wifi")
    estado_conexion = Column(String(20), default="conectado")
    
    fecha_inicio_conexion = Column(DateTime, default=datetime.utcnow)
    # onupdate hace que esta fecha cambie sola cada vez que modifiquemos el registro
    ultima_conexion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)