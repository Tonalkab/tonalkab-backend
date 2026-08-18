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
    from app.models.tienda import ProductoTienda, PromocionSkin
    from datetime import datetime

    todas_skins = db.query(Skin).all()
    mis_skins = db.query(UsuarioSkin).filter(UsuarioSkin.id_usuario == current_user.id_usuario).all()
    dict_mis_skins = {item.id_skin: item.equipado for item in mis_skins}
    
    # Evaluar promociones activas
    now = datetime.utcnow()
    promos = db.query(PromocionSkin).filter(PromocionSkin.fecha_inicio <= now, PromocionSkin.fecha_fin >= now).all()
    dict_promos = {p.id_skin: p.precio_oferta for p in promos}

    items = []
    for s in todas_skins:
        desbloqueada = s.id in dict_mis_skins
        en_uso = dict_mis_skins.get(s.id, False)
        
        # Aplicar promo
        en_promo = s.id in dict_promos
        precio_final = dict_promos[s.id] if en_promo else (s.precio_monedas or 0)
        
        items.append(SkinTiendaItem(
            id=s.id,
            nombre=s.nombre,
            descripcion=s.descripcion,
            imagen_url=s.imagen_url,
            es_premium=s.es_premium,
            precio_monedas=precio_final,
            precio_original=s.precio_monedas or 0,
            en_promocion=en_promo,
            categoria=s.categoria,
            desbloqueada=desbloqueada,
            en_uso=en_uso
        ))
        
    # Obtener productos de semillas y suscripciones
    productos_db = db.query(ProductoTienda).filter(ProductoTienda.activo == True).all()
    prods = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "tipo": p.tipo,
            "cantidad_semillas": p.cantidad_semillas,
            "precio_moneda_local": p.precio_moneda_local,
            "icono": p.icono,
            "recomendado": p.recomendado
        } for p in productos_db
    ]

    return {
        "saldo_monedas": current_user.monedas or 0,
        "skins": items,
        "productos": prods
    }


@router.post("/{id_skin}/comprar")
def comprar_o_desbloquear_skin(
    id_skin: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permite al usuario adquirir una skin evaluando promociones.
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
            "message": "Ya tienes esta skin en tu coleccin",
            "id_skin": id_skin,
            "saldo_monedas": usuario.monedas
        }
        
    precio = skin.precio_monedas or 0
    from app.models.tienda import PromocionSkin
    from datetime import datetime
    now = datetime.utcnow()
    promo = db.query(PromocionSkin).filter(PromocionSkin.id_skin == id_skin, PromocionSkin.fecha_inicio <= now, PromocionSkin.fecha_fin >= now).first()
    if promo:
        precio = promo.precio_oferta

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
        "message": f"Skin '{skin.nombre}' desbloqueada exitosamente!",
        "id_skin": id_skin,
        "saldo_monedas": usuario.monedas
    }
