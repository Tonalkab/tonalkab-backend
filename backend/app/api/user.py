from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import hash_password
from app.api.auth import get_current_user 

# Nuevas importaciones para las Skins
from app.models.skin import UsuarioSkin
from app.schemas.skin import UsuarioSkinResponse

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
    """Devuelve el perfil del usuario autenticado."""
    return current_user

# ---------------------------------------------------------
# 2. ENDPOINT PROTEGIDO DE PRUEBA
# ---------------------------------------------------------
@router.get("/protected")
def test_protected(current_user: User = Depends(get_current_user)):
    """Verifica que el JWT funciona correctamente."""
    return {"message": f"Hola {current_user.nombre}, estás autenticado correctamente."}

# ---------------------------------------------------------
# 3. CREAR USUARIO (REGISTRO + STARTER PACK)
# ---------------------------------------------------------
@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario y le asigna automáticamente 
    la skin 'Botánica Clásica' (ID 1) como equipada.
    """
    # 1. Crear la instancia del usuario
    db_user = User(
        nombre=user.nombre,
        email=user.email,
        password_hash=hash_password(user.password),
        id_estado_cuenta=1  # Estado 'activo' por defecto
    )
    db.add(db_user)
    
    # flush() sincroniza con la BD para obtener el id_usuario sin cerrar la transacción
    db.flush() 

    # 2. Asignar la Skin inicial (ID 1)
    starter_skin = UsuarioSkin(
        id_usuario=db_user.id_usuario,
        id_skin=1,
        equipado=True
    )
    db.add(starter_skin)

    # 3. Confirmar cambios en una sola transacción
    db.commit()
    db.refresh(db_user)
    return db_user

# ---------------------------------------------------------
# 4. LISTAR USUARIOS (SOLO PARA PRUEBAS LOCALES)
# ---------------------------------------------------------
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# ---------------------------------------------------------
# 5. OBTENER SKINS DEL USUARIO
# ---------------------------------------------------------
@router.get("/me/skins", response_model=List[UsuarioSkinResponse])
def get_mis_skins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Devuelve el inventario de skins desbloqueadas por el usuario."""
    return db.query(UsuarioSkin).filter(
        UsuarioSkin.id_usuario == current_user.id_usuario
    ).all()

# ---------------------------------------------------------
# 6. EQUIPAR UNA SKIN
# ---------------------------------------------------------
@router.post("/me/skins/{id_skin}/equipar")
def equipar_skin(
    id_skin: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca una skin como equipada y desactiva las demás para este usuario."""
    # Verificar posesión de la skin
    skin_usuario = db.query(UsuarioSkin).filter(
        UsuarioSkin.id_usuario == current_user.id_usuario,
        UsuarioSkin.id_skin == id_skin
    ).first()

    if not skin_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes esta skin desbloqueada en tu inventario."
        )

    # Desequipar todas las skins del usuario (Lógica de limpieza)
    db.query(UsuarioSkin).filter(
        UsuarioSkin.id_usuario == current_user.id_usuario
    ).update({"equipado": False})

    # Activar la skin deseada
    skin_usuario.equipado = True
    
    db.commit()
    return {"message": "Skin equipada exitosamente", "id_skin_equipada": id_skin}