from pydantic import BaseModel
from typing import Optional, List

class SkinBase(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: str
    es_premium: bool
    precio_monedas: int = 0
    categoria: str = "comun"

    class Config:
        from_attributes = True

class SkinTiendaItem(SkinBase):
    desbloqueada: bool = False
    en_uso: bool = False
    en_promocion: bool = False
    precio_original: int = 0

class SkinTiendaResponse(BaseModel):
    saldo_monedas: int
    skins: List[SkinTiendaItem]
    productos: list = []

class UsuarioSkinResponse(BaseModel):
    id_skin: int
    equipado: bool
    skin: SkinBase  # Anidamos la info de la skin gracias al relationship de SQLAlchemy

    class Config:
        from_attributes = True