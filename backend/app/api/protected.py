from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import Usuario

router = APIRouter()

@router.get("/protected")
def protected_route(current_user: Usuario = Depends(get_current_user)):
    return {
    "message": "Acceso permitido",
    "user": {
        "id": current_user.id_usuario,
        "email": current_user.email
    }
}