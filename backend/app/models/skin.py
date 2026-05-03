from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class Skin(Base):
    __tablename__ = "skins"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    imagen_url = Column(String(255), nullable=False)
    es_premium = Column(Boolean, default=False)

    # Relaciones inversas hacia las tablas puente
    usuarios_rel = relationship("UsuarioSkin", back_populates="skin")
    macetas_rel = relationship("MacetaSkin", back_populates="skin")


class UsuarioSkin(Base):
    __tablename__ = "usuarios_skins"

    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), primary_key=True)
    id_skin = Column(Integer, ForeignKey("skins.id"), primary_key=True)
    equipado = Column(Boolean, default=False)

    # <-- ESTA ES LA LÍNEA QUE FALTABA
    skin = relationship("Skin", back_populates="usuarios_rel") 


class MacetaSkin(Base):
    __tablename__ = "macetas_skins"

    id_maceta = Column(Integer, ForeignKey("macetas.id_maceta"), primary_key=True)
    id_skin = Column(Integer, ForeignKey("skins.id"), primary_key=True)
    equipado = Column(Boolean, default=False)

    # <-- ESTA TAMBIÉN ES NECESARIA PARA LA MACETA
    skin = relationship("Skin", back_populates="macetas_rel")