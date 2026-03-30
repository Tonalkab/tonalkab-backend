from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db import Base

class User(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)

    foto_perfil_url = Column(String(255), nullable=True)
    id_estado_cuenta = Column(Integer, nullable=False, default=1)

    ultimo_login = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)