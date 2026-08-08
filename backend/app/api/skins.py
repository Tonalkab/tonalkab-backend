from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models.skin import Skin, UsuarioSkin
from app.models.user import User
from app.schemas.skin import SkinBase, SkinTiendaResponse, SkinTiendaItem
from app.api.auth import get_current_user

router = APIRouter(prefix="/skins", tags=["Skins"])

@router.get("/", response_model=List[SkinBase])
def get_catalogo_skins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Devuelve todo el catálogo de skins disponibles en el sistema."""
    return db.query(Skin).all()

@router.get("/tienda", response_model=SkinTiendaResponse)
def get_tienda_skins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve todas las skins con el estado de posesión para el usuario 
    actual y su saldo disponible de monedas.
    """
    todas_skins = db.query(Skin).all()
    mis_skins = db.query(UsuarioSkin).filter(UsuarioSkin.id_usuario == current_user.id_usuario).all()
    
    dict_mis_skins = {item.id_skin: item.equipado for item in mis_skins}
    
    items = []
    for s in todas_skins:
        desbloqueada = s.id in dict_mis_skins
        en_uso = dict_mis_skins.get(s.id, False)
        items.append(SkinTiendaItem(
            id=s.id,
            nombre=s.nombre,
            descripcion=s.descripcion,
            imagen_url=s.imagen_url,
            es_premium=s.es_premium,
            precio_monedas=s.precio_monedas or 0,
            desbloqueada=desbloqueada,
            en_uso=en_uso
        ))
        
    return SkinTiendaResponse(
        saldo_monedas=current_user.monedas or 0,
        skins=items
    )

@router.post("/{id_skin}/comprar")
def comprar_o_desbloquear_skin(
    id_skin: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permite al usuario adquirir una skin:
    - Si es gratis (precio_monedas == 0), la desbloquea sin costo.
    - Si tiene costo en monedas, valida saldo suficiente, descuenta y desbloquea.
    """
    skin = db.query(Skin).filter(Skin.id == id_skin).first()
    if not skin:
        raise HTTPException(status_code=404, detail="La skin solicitada no existe")
        
    usuario = db.query(User).filter(User.id_usuario == current_user.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Verificar si ya la tiene
    ya_obtenida = db.query(UsuarioSkin).filter(
        UsuarioSkin.id_usuario == usuario.id_usuario,
        UsuarioSkin.id_skin == id_skin
    ).first()
    
    if ya_obtenida:
        return {
            "message": "Ya tienes esta skin en tu colección",
            "id_skin": id_skin,
            "saldo_monedas": usuario.monedas
        }
        
    precio = skin.precio_monedas or 0
    if precio > 0:
        if (usuario.monedas or 0) < precio:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente. Requieres {precio} monedas y tienes {usuario.monedas}."
            )
        usuario.monedas -= precio
        
    nueva_skin_usuario = UsuarioSkin(
        id_usuario=usuario.id_usuario,
        id_skin=id_skin,
        equipado=False
    )
    db.add(nueva_skin_usuario)
    db.commit()
    db.refresh(usuario)
    
    return {
        "message": f"¡Skin '{skin.nombre}' desbloqueada exitosamente!",
        "id_skin": id_skin,
        "saldo_monedas": usuario.monedas
    }