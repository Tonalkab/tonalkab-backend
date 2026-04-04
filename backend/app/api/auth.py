from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.user import User as Usuario
from app.models.auth_provider import AuthProvider

from app.schemas.auth import LoginRequest, GoogleAuthRequest

from app.core.security import verify_password, create_access_token, verify_token
from app.core.google_auth import verify_google_token

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()

# 🔐 Esquema de seguridad
security = HTTPBearer()


# 📦 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔐 Usuario autenticado
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(Usuario).filter(Usuario.id_usuario == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user


# 🔑 LOGIN TRADICIONAL
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == data.email).first()

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


# 🌐 LOGIN CON GOOGLE
@router.post("/auth/google")
def google_login(data: GoogleAuthRequest, db: Session = Depends(get_db)):

    # 🔐 1. Validar token con Google
    google_data = verify_google_token(data.id_token)

    # 📦 2. Extraer datos
    email = google_data.get("email")
    google_id = google_data.get("sub")
    name = google_data.get("name")
    picture = google_data.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Email not available")

    # 🔍 3. Buscar usuario
    user = db.query(Usuario).filter(Usuario.email == email).first()

    # 🟢 CASO 1 — Usuario nuevo
    if not user:
        new_user = Usuario(
            email=email,
            nombre=name,
            foto_perfil_url=picture,
            password_hash="",  # No aplica para Google
            id_estado_cuenta=1
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        auth_provider = AuthProvider(
            id_usuario=new_user.id_usuario,
            provider="google",
            provider_id=google_id
        )

        db.add(auth_provider)
        db.commit()

        user = new_user

    # 🟡 / 🟢 Usuario existente
    else:
        provider = db.query(AuthProvider).filter(
            AuthProvider.id_usuario == user.id_usuario,
            AuthProvider.provider == "google"
        ).first()

        # 🔴 CASO 3 — No tiene Google → bloquear
        if not provider:
            raise HTTPException(
                status_code=400,
                detail="Account exists with different authentication method"
            )

        # 🟢 CASO 2 — Validar Google ID
        if provider.provider_id != google_id:
            raise HTTPException(
                status_code=400,
                detail="Google account mismatch"
            )

    # ⚠️ FASE 3: aquí irá el JWT
    access_token = create_access_token(
        data={"sub": str(user.id_usuario)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }