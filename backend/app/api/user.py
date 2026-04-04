from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import hash_password
from app.api.auth import get_current_user  # Tu dependencia de seguridad

router = APIRouter()

# 📦 Dependencia de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# 1. ENDPOINT /me (PROTEGIDO)
# ---------------------------------------------------------
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Devuelve el perfil del usuario autenticado. 
    Gracias a UserResponse, no se filtra el password_hash.
    """
    return current_user

# ---------------------------------------------------------
# 2. ENDPOINT PROTEGIDO DE PRUEBA
# ---------------------------------------------------------
@router.get("/protected")
def test_protected(current_user: User = Depends(get_current_user)):
    """
    Endpoint simple para verificar que el JWT funciona.
    """
    return {"message": f"Hola {current_user.nombre}, estás autenticado correctamente."}

# ---------------------------------------------------------
# 3. CREAR USUARIO (REGISTRO)
# ---------------------------------------------------------
@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        nombre=user.nombre,
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ---------------------------------------------------------
# 4. LISTAR USUARIOS (SOLO PARA PRUEBAS LOCALES)
# ---------------------------------------------------------
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()