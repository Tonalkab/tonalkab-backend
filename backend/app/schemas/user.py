from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id_usuario: int
    nombre: str
    email: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)