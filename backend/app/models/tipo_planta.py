from sqlalchemy import Column, Integer, String, DECIMAL, TEXT
from app.db import Base

class TipoPlanta(Base):
    __tablename__ = "tipo_planta"

    id_tipo_planta = Column(Integer, primary_key=True, index=True)
    nombre_planta = Column(String(100), nullable=False)
    
    # Umbrales técnicos para el sistema de riego 
    humedad_min_recomendada = Column(DECIMAL(5, 2), nullable=False)
    humedad_max_recomendada = Column(DECIMAL(5, 2), nullable=False)
    tiempo_min_entre_riegos = Column(Integer, nullable=False) # En minutos 
    luz_recomendada = Column(Integer, nullable=False) # En lux 
    temperatura_recomendada = Column(DECIMAL(5, 2), nullable=False)
    tolerancia_exceso_agua = Column(Integer, nullable=False) # Escala 0-100 
    
    # Información descriptiva para la App móvil 
    descripcion = Column(TEXT, nullable=True)
    origen_geografico = Column(String(100), nullable=True)
    historia = Column(TEXT, nullable=True)
    cuidados_generales = Column(TEXT, nullable=True)
    nivel_dificultad = Column(String(20), nullable=False) # ej: "facil", "medio" 
    imagen_url = Column(String(255), nullable=True)