from sqlalchemy import Column, Integer, String, ForeignKey
from app.db import Base
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint

class AuthProvider(Base):
    __tablename__ = "auth_providers"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    provider = Column(String(50), nullable=False)
    provider_id = Column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="uq_provider_user"),
    )