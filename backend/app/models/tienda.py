from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class ProductoTienda(Base):
    __tablename__ = "productos_tienda"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    tipo = Column(String(50), nullable=False) # 'semilla' o 'suscripcion'
    cantidad_semillas = Column(Integer, default=0) 
    precio_moneda_local = Column(Float, nullable=False) 
    icono = Column(String(10), default="🌱")
    recomendado = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)

class PromocionSkin(Base):
    __tablename__ = "promociones_skins"

    id = Column(Integer, primary_key=True, index=True)
    id_skin = Column(Integer, ForeignKey("skins.id", ondelete="CASCADE"), nullable=False)
    precio_oferta = Column(Integer, nullable=False)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    
    skin = relationship("Skin")
