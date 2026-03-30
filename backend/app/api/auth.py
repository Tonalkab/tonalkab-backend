from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.core.security import verify_password

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    return {
        "message": "Login exitoso",
        "user_id": user.id_usuario
    }