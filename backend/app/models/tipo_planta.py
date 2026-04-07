from sqlalchemy import Column, Integer, String, DECIMAL, TEXT, ForeignKey
from app.db import Base

class TipoPlanta(Base):
    __tablename__ = "tipo_planta"

    id_tipo_planta = Column(Integer, primary_key=True, index=True)
    nombre_planta = Column(String(100), nullable=False)
    
    # RANGOS AMBIENTALES
    humedad_suelo_min = Column(DECIMAL(5, 2), nullable=False)
    humedad_suelo_max = Column(DECIMAL(5, 2), nullable=False)
    humedad_ambiente_min = Column(DECIMAL(5, 2), nullable=False)
    humedad_ambiente_max = Column(DECIMAL(5, 2), nullable=False)
    temperatura_min = Column(DECIMAL(5, 2), nullable=False)
    temperatura_max = Column(DECIMAL(5, 2), nullable=False)
    
    tiempo_min_entre_riegos_dias = Column(Integer, nullable=False)
    profundidad_raiz_cm = Column(Integer, nullable=False)
    nivel_dificultad = Column(Integer, nullable=False)
    
    # LLAVES FORÁNEAS A CATÁLOGOS
    sensibilidad_luz_id = Column(Integer, ForeignKey("sensibilidad_luz.id_sensibilidad_luz"), nullable=False)
    tolerancia_exceso_agua_id = Column(Integer, ForeignKey("tolerancia_exceso_agua.id_tolerancia"), nullable=False)
    tipo_planta_categoria_id = Column(Integer, ForeignKey("tipo_planta_categoria.id_tipo_planta_cat"), nullable=False)
    tipo_suelo_id = Column(Integer, ForeignKey("tipo_suelo.id_tipo_suelo"), nullable=False)
    consumo_agua_id = Column(Integer, ForeignKey("consumo_agua.id_consumo"), nullable=False)
    
    # DESCRIPCIONES
    descripcion = Column(TEXT, nullable=True)
    origen_geografico = Column(String(100), nullable=True)
    historia = Column(TEXT, nullable=True)
    cuidados_generales = Column(TEXT, nullable=True)
    imagen_url = Column(String(255), nullable=True)