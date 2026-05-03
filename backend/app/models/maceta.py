from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship  # <-- 1. Importar relationship
from datetime import datetime
from app.db import Base
from app.models.tipo_planta import TipoPlanta


class Maceta(Base):
    __tablename__ = "macetas"

    id_maceta = Column(Integer, primary_key=True, index=True)
    
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    
    nombre_maceta = Column(String(100), nullable=False)
    
    token_hash = Column(String(255), nullable=False)
    
    id_tipo_planta = Column(Integer, ForeignKey("tipo_planta.id_tipo_planta"), nullable=False)
    
    id_estado_dispositivo = Column(Integer, nullable=False, default=2)  # 2 = desconectado
    
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # ---------------------------------------------------------
    # RELACIONES Y PROPIEDADES DINÁMICAS (Skins)
    # ---------------------------------------------------------
    
    # 2. Relación con la tabla puente de skins
    skins_maceta = relationship("MacetaSkin", backref="maceta")

    # 3. Propiedad dinámica para que Pydantic pueda extraer la skin activa en el response
    @property
    def skin_activa(self):
        """Busca entre las skins de esta maceta la que está equipada y devuelve sus datos"""
        for relacion in self.skins_maceta:
            if relacion.equipado:
                return relacion.skin # Retorna el objeto Skin (id, nombre, imagen_url, etc)
        return None