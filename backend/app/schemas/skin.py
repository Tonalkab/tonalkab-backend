from pydantic import BaseModel
from typing import Optional, List

class SkinBase(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: str
    es_premium: bool

    class Config:
        from_attributes = True

class UsuarioSkinResponse(BaseModel):
    id_skin: int
    equipado: bool
    skin: SkinBase  # Anidamos la info de la skin gracias al relationship de SQLAlchemy

    class Config:
        from_attributes = True