from sqlalchemy import Column, Integer, DECIMAL, ForeignKey, DateTime, String
from datetime import datetime
from app.db import Base

# --- NUEVOS CATÁLOGOS FALTANTES ---
class TipoActivacion(Base):
    __tablename__ = "tipo_activacion"
    id_tipo_activacion = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)

class EstadoRegistro(Base):
    __tablename__ = "estado_registro"
    id_estado_registro = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)

# --- TU CLASE ACTUAL ---
class ControlRiego(Base):
    __tablename__ = "control_riego"

    id_riego = Column(Integer, primary_key=True, index=True)
    id_maceta = Column(Integer, ForeignKey("macetas.id_maceta"), nullable=False)
    
    fecha_inicio_riego = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_fin_riego = Column(DateTime, nullable=True)
    
    humedad_antes = Column(DECIMAL(5, 2), nullable=False)
    humedad_despues = Column(DECIMAL(5, 2), nullable=False)
    incremento_humedad = Column(DECIMAL(5, 2), nullable=False)
    humedad_objetivo_en_momento = Column(DECIMAL(5, 2), nullable=False)
    
    cantidad_agua_ml = Column(DECIMAL(6, 2), nullable=False)
    duracion_bomba = Column(Integer, nullable=False)
    
    temperatura_en_momento = Column(DECIMAL(5, 2), nullable=False)
    luz_en_momento = Column(Integer, nullable=False)
    
    id_tipo_activacion = Column(Integer, ForeignKey("tipo_activacion.id_tipo_activacion"), nullable=False)
    id_prediccion_ml = Column(Integer, ForeignKey("predicciones_ml.id_prediccion"), nullable=True)
    id_estado_registro = Column(Integer, ForeignKey("estado_registro.id_estado_registro"), nullable=False)
    resultado_riego = Column(String(50), nullable=False, default="exitoso")