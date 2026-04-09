from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime
from datetime import datetime
from app.db import Base

class PrediccionesML(Base):
    __tablename__ = "predicciones_ml"

    id_prediccion = Column(Integer, primary_key=True, index=True)
    id_maceta = Column(Integer, ForeignKey("macetas.id_maceta"), nullable=False)
    # Puede ser nulo si la predicción no se basa en una sola lectura, sino en una ventana de tiempo
    id_lectura_base = Column(Integer, ForeignKey("lectura_sensores.id_lectura"), nullable=True) 
    
    fecha_generacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    tipo_prediccion = Column(String(50), nullable=False) # Ej: "dosis_riego", "humedad_futura"
    valor_predicho = Column(DECIMAL(8, 2), nullable=False)
    valor_real = Column(DECIMAL(8, 2), nullable=True) # Para calcular el error de tu modelo después
    unidad_medida = Column(String(20), nullable=False) # Ej: "ml", "%"
    
    periodo_pronostico = Column(Integer, nullable=False) # Minutos hacia el futuro
    confianza_modelo = Column(DECIMAL(5, 2), nullable=False) # Porcentaje de seguridad de tu modelo
    version_modelo = Column(String(50), nullable=False)
    error_prediccion = Column(DECIMAL(8, 2), nullable=True)