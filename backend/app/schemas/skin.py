from pydantic import BaseModel
from typing import Optional, List

class SkinBase(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: str
    es_premium: bool
    precio_monedas: int = 0

    class Config:
        from_attributes = True

class SkinTiendaItem(SkinBase):
    desbloqueada: bool = False
    en_uso: bool = False

class SkinTiendaResponse(BaseModel):
    saldo_monedas: int
    skins: List[SkinTiendaItem]

class UsuarioSkinResponse(BaseModel):
    id_skin: int
    equipado: bool
    skin: SkinBase  # Anidamos la info de la skin gracias al relationship de SQLAlchemy

    class Config:
        from_attributes = True