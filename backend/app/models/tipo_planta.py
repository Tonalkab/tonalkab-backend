from sqlalchemy import Column, Integer, String
from app.db import Base


class TipoPlanta(Base):
    __tablename__ = "tipo_planta"

    id_tipo_planta = Column(Integer, primary_key=True, index=True)
    nombre_planta = Column(String(100), nullable=False)