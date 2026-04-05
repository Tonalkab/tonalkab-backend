from sqlalchemy import Column, Integer, DECIMAL, ForeignKey, DateTime, Boolean
from datetime import datetime
from app.db import Base

class LecturaSensores(Base):
    __tablename__ = "lectura_sensores"

    id_lectura = Column(Integer, primary_key=True, index=True)
    
    # Llave foránea que conecta esta lectura con una maceta específica
    id_maceta = Column(Integer, ForeignKey("macetas.id_maceta"), nullable=False)
    
    fecha_hora = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Mediciones de sensores
    humedad_suelo = Column(DECIMAL(5, 2), nullable=False)
    temperatura = Column(DECIMAL(5, 2), nullable=False)
    humedad_ambiental = Column(DECIMAL(5, 2), nullable=False)
    nivel_luz = Column(Integer, nullable=False)
    nivel_agua = Column(Integer, nullable=False)
    voltaje_bateria = Column(DECIMAL(5, 2), nullable=False)
