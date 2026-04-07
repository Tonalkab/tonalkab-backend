from sqlalchemy import Column, Integer, String
from app.db import Base

class SensibilidadLuz(Base):
    __tablename__ = "sensibilidad_luz"
    id_sensibilidad_luz = Column(Integer, primary_key=True, index=True)
    valor = Column(String(50), nullable=False)

class ToleranciaExcesoAgua(Base):
    __tablename__ = "tolerancia_exceso_agua"
    id_tolerancia = Column(Integer, primary_key=True, index=True)
    valor = Column(String(50), nullable=False)

class TipoPlantaCategoria(Base):
    __tablename__ = "tipo_planta_categoria"
    id_tipo_planta_cat = Column(Integer, primary_key=True, index=True) # Renombrado para no chocar con TipoPlanta
    valor = Column(String(50), nullable=False)

class TipoSuelo(Base):
    __tablename__ = "tipo_suelo"
    id_tipo_suelo = Column(Integer, primary_key=True, index=True)
    valor = Column(String(50), nullable=False)

class ConsumoAgua(Base):
    __tablename__ = "consumo_agua"
    id_consumo = Column(Integer, primary_key=True, index=True)
    valor = Column(String(50), nullable=False)