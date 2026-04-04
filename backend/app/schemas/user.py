from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# ==============================
# SCHEMA PARA CREACIÓN (INPUT)
# ==============================
class UserCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)

# ==============================
# SCHEMA PARA RESPUESTA (OUTPUT)
# ==============================
class UserResponse(BaseModel):
    id_usuario: int
    nombre: str
    email: EmailStr
    foto_perfil_url: Optional[str] = None
    ultimo_login: Optional[datetime] = None
    created_at: datetime  # Corresponde a la fecha de registro en tu modelo

    class Config:
        from_attributes = True # Permite que Pydantic lea modelos de SQLAlchemy [cite: 65]