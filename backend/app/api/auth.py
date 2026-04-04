from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime  # <--- IMPORTANTE: Para el último login

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

# 🔐 Dependency: Obtener usuario autenticado (Ya lo tienes bien)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user = db.query(Usuario).filter(Usuario.id_usuario == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user

# 🔑 LOGIN TRADICIONAL (Mejorado)
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # 1. Buscar usuario por email
    user = db.query(Usuario).filter(Usuario.email == data.email).first()

    # 2. Validar existencia y contraseña
    # Usamos 401 y mensaje genérico por seguridad (evita que atacantes sepan si el email existe)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # 3. Validar estado de cuenta (Basado en tu doc: 1 = activo) 
    if user.id_estado_cuenta != 1:
        raise HTTPException(
            status_code=403, 
            detail="La cuenta no está activa. Contacte al administrador."
        )

    # 4. Actualizar rastro de actividad 
    user.ultimo_login = datetime.utcnow()
    db.commit() # Guardamos el cambio de la fecha en la DB

    # 5. Generar JWT
    access_token = create_access_token(
        data={"sub": str(user.id_usuario)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# 🌐 LOGIN CON GOOGLE (Actualizado con seguridad y ultimo_login)
@router.post("/auth/google")
def google_login(data: GoogleAuthRequest, db: Session = Depends(get_db)):
    # 🔐 1. Validar token con Google
    google_data = verify_google_token(data.id_token)

    email = google_data.get("email")
    google_id = google_data.get("sub")
    name = google_data.get("name")
    picture = google_data.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="El token de Google no contiene email")

    user = db.query(Usuario).filter(Usuario.email == email).first()

    # 🟢 Caso: Registro nuevo vía Google
    if not user:
        new_user = Usuario(
            email=email,
            nombre=name,
            foto_perfil_url=picture,
            password_hash="", 
            id_estado_cuenta=1,
            ultimo_login=datetime.utcnow()
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

    # 🟡 Caso: Usuario ya registrado
    else:
        # Validar si tiene este proveedor vinculado
        provider = db.query(AuthProvider).filter(
            AuthProvider.id_usuario == user.id_usuario,
            AuthProvider.provider == "google"
        ).first()

        if not provider:
            raise HTTPException(
                status_code=400,
                detail="Este email ya está registrado con otro método de acceso"
            )

        # Actualizar último acceso incluso en Google Login
        user.ultimo_login = datetime.utcnow()
        db.commit()

    # 🎟️ Generar Token Final
    access_token = create_access_token(
        data={"sub": str(user.id_usuario)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }