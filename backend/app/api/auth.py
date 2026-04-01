from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.core.security import verify_password, create_access_token, verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()

# Esquema de seguridad
security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.id_usuario == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    access_token = create_access_token(
        data={"sub": str(user.id_usuario)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }