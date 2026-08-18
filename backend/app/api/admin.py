import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models.user import User
from app.models.skin import Skin
from app.models.tipo_planta import TipoPlanta
from app.models.maceta import Maceta
from app.models.tienda import ProductoTienda, PromocionSkin
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import text
from app.api.auth import get_current_admin_user
from app.schemas.skin import SkinBase

router = APIRouter(prefix="/admin", tags=["Administración"])

# Directorio base para activos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SKINS_DIR = os.path.join(ASSETS_DIR, "skins")
PLANTAS_DIR = os.path.join(ASSETS_DIR, "plantas")

os.makedirs(SKINS_DIR, exist_ok=True)
os.makedirs(PLANTAS_DIR, exist_ok=True)


# ==========================================
# 📊 ESTADÍSTICAS DEL SISTEMA
# ==========================================
@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Retorna un resumen de métricas del sistema para el panel de administración."""
    total_usuarios = db.query(User).count()
    total_macetas = db.query(Maceta).count()
    total_skins = db.query(Skin).count()
    total_plantas = db.query(TipoPlanta).count()

    return {
        "total_usuarios": total_usuarios,
        "total_macetas": total_macetas,
        "total_skins": total_skins,
        "total_plantas": total_plantas,
        "admin_nombre": admin.nombre
    }


# ==========================================
# 🎨 SUBIDA DE NUEVAS SKINS
# ==========================================
@router.post("/skins", response_model=SkinBase)
def crear_skin_admin(
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None),
    es_premium: bool = Form(False),
    precio_monedas: int = Form(0),
    categoria: str = Form("comun"),
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Permite al administrador subir un diseño de skin (archivo PNG/JPG) 
    y registrarlo directamente en la base de datos sin ejecutar SQL manual.
    """
    # 1. Validar extensión de imagen
    ext = os.path.splitext(imagen.filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagen inválido. Solo se admiten archivos PNG, JPG, WEBP o SVG."
        )

    # 2. Generar nombre único para el archivo físico
    safe_filename = f"{uuid.uuid4().hex[:12]}_{imagen.filename.replace(' ', '_')}"
    filepath = os.path.join(SKINS_DIR, safe_filename)

    # 3. Guardar el archivo en el disco
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la imagen en el servidor: {str(e)}"
        )

    # 4. Crear registro en la tabla Skin
    imagen_url = f"/assets/skins/{safe_filename}"
    nueva_skin = Skin(
        nombre=nombre.strip(),
        descripcion=descripcion.strip() if descripcion else None,
        imagen_url=imagen_url,
        es_premium=es_premium,
        precio_monedas=precio_monedas,
        categoria=categoria.strip()
    )

    db.add(nueva_skin)
    db.commit()
    db.refresh(nueva_skin)

    return nueva_skin


# ==========================================
# 🌿 SUBIDA DE NUEVAS ESPECIES DE PLANTAS
# ==========================================
@router.post("/plantas")
def crear_planta_admin(
    nombre_planta: str = Form(...),
    humedad_suelo_min: float = Form(...),
    humedad_suelo_max: float = Form(...),
    humedad_ambiente_min: float = Form(...),
    humedad_ambiente_max: float = Form(...),
    temperatura_min: float = Form(...),
    temperatura_max: float = Form(...),
    tiempo_min_entre_riegos_dias: int = Form(...),
    profundidad_raiz_cm: int = Form(...),
    nivel_dificultad: int = Form(1),
    sensibilidad_luz_id: int = Form(1),
    tolerancia_exceso_agua_id: int = Form(1),
    tipo_planta_categoria_id: int = Form(1),
    tipo_suelo_id: int = Form(1),
    consumo_agua_id: int = Form(1),
    descripcion: Optional[str] = Form(None),
    origen_geografico: Optional[str] = Form(None),
    historia: Optional[str] = Form(None),
    cuidados_generales: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Permite al administrador agregar una nueva ficha botánica con sus parámetros 
    de riego y foto opcional, quedando disponible para todos los usuarios.
    """
    imagen_url = None
    if imagen and imagen.filename:
        ext = os.path.splitext(imagen.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            safe_filename = f"planta_{uuid.uuid4().hex[:8]}_{imagen.filename.replace(' ', '_')}"
            filepath = os.path.join(PLANTAS_DIR, safe_filename)
            try:
                with open(filepath, "wb") as buffer:
                    shutil.copyfileobj(imagen.file, buffer)
                imagen_url = f"/assets/plantas/{safe_filename}"
            except Exception as e:
                print(f"Error guardando foto de planta: {e}")

    nueva_planta = TipoPlanta(
        nombre_planta=nombre_planta.strip(),
        humedad_suelo_min=humedad_suelo_min,
        humedad_suelo_max=humedad_suelo_max,
        humedad_ambiente_min=humedad_ambiente_min,
        humedad_ambiente_max=humedad_ambiente_max,
        temperatura_min=temperatura_min,
        temperatura_max=temperatura_max,
        tiempo_min_entre_riegos_dias=tiempo_min_entre_riegos_dias,
        profundidad_raiz_cm=profundidad_raiz_cm,
        nivel_dificultad=nivel_dificultad,
        sensibilidad_luz_id=sensibilidad_luz_id,
        tolerancia_exceso_agua_id=tolerancia_exceso_agua_id,
        tipo_planta_categoria_id=tipo_planta_categoria_id,
        tipo_suelo_id=tipo_suelo_id,
        consumo_agua_id=consumo_agua_id,
        descripcion=descripcion.strip() if descripcion else None,
        origen_geografico=origen_geografico.strip() if origen_geografico else None,
        historia=historia.strip() if historia else None,
        cuidados_generales=cuidados_generales.strip() if cuidados_generales else None,
        imagen_url=imagen_url
    )

    db.add(nueva_planta)
    db.commit()
    db.refresh(nueva_planta)

    return {
        "message": f"Planta '{nueva_planta.nombre_planta}' agregada exitosamente al catálogo.",
        "id_tipo_planta": nueva_planta.id_tipo_planta
    }


# ==========================================
# 👥 GESTIÓN DE USUARIOS Y BILLETERA DE MONEDAS
# ==========================================
from pydantic import BaseModel, Field

class OtorgarMonedasRequest(BaseModel):
    cantidad: int = Field(..., description="Cantidad de monedas a transferir")

@router.get("/usuarios")
def buscar_usuarios_admin(
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Permite al administrador buscar usuarios por nombre o correo electrónico."""
    q = db.query(User).filter(User.deleted_at == None)
    if query and query.strip():
        search_term = f"%{query.strip()}%"
        q = q.filter((User.email.ilike(search_term)) | (User.nombre.ilike(search_term)))
    
    usuarios = q.order_by(User.id_usuario.desc()).limit(30).all()
    return [
        {
            "id_usuario": u.id_usuario,
            "nombre": u.nombre,
            "email": u.email,
            "foto_perfil_url": u.foto_perfil_url,
            "monedas": u.monedas or 0,
            "es_admin": u.es_admin
        }
        for u in usuarios
    ]


@router.post("/usuarios/{id_usuario}/monedas")
def otorgar_monedas_admin(
    id_usuario: int,
    data: OtorgarMonedasRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Permite al administrador añadir o transferir monedas a la cuenta de cualquier usuario."""
    usuario = db.query(User).filter(User.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.cantidad == 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser diferente de 0")

    saldo_anterior = usuario.monedas or 0
    nuevo_saldo = max(0, saldo_anterior + data.cantidad)
    usuario.monedas = nuevo_saldo

    db.commit()
    db.refresh(usuario)

    return {
        "message": f"Se han {'acreditado' if data.cantidad > 0 else 'descontado'} {abs(data.cantidad)} monedas a {usuario.nombre}.",
        "id_usuario": usuario.id_usuario,
        "email": usuario.email,
        "saldo_anterior": saldo_anterior,
        "saldo_nuevo": usuario.monedas
    }



# ==========================================
# 🔄 ACTUALIZAR IMAGEN DE UNA SKIN
# ==========================================
@router.put("/skins/{skin_id}/imagen")
def actualizar_imagen_skin(
    skin_id: int,
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    skin = db.query(Skin).filter(Skin.id == skin_id).first()
    if not skin:
        raise HTTPException(status_code=404, detail="Skin no encontrada.")

    # 1. Validar extensión de imagen
    ext = os.path.splitext(imagen.filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="Formato de imagen inválido.")

    # 2. Generar nombre único y guardar
    safe_filename = f"{uuid.uuid4().hex[:12]}_{imagen.filename.replace(' ', '_')}"
    new_filepath = os.path.join(SKINS_DIR, safe_filename)

    try:
        with open(new_filepath, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la imagen: {str(e)}")

    # 3. Eliminar la imagen anterior si existe físicamente (Opcional, pero buena práctica)
    if skin.imagen_url:
        old_filename = os.path.basename(skin.imagen_url)
        old_filepath = os.path.join(SKINS_DIR, old_filename)
        if os.path.exists(old_filepath):
            try:
                os.remove(old_filepath)
            except:
                pass

    # 4. Actualizar la base de datos
    skin.imagen_url = f"/assets/skins/{safe_filename}"
    db.commit()
    db.refresh(skin)

    return {"message": "Imagen actualizada exitosamente", "imagen_url": skin.imagen_url}


# ==========================================
# 🏪 GESTIÓN DE TIENDA (PRODUCTOS)
# ==========================================

class ProductoTiendaUpdate(BaseModel):
    nombre: str
    descripcion: str | None = None
    tipo: str
    cantidad_semillas: int
    precio_moneda_local: float
    icono: str
    recomendado: bool | None = False
    activo: bool | None = True

@router.get("/tienda/productos")
def listar_productos_tienda(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return db.query(ProductoTienda).all()

@router.put("/tienda/productos/{id}")
def actualizar_producto_tienda(id: int, producto: ProductoTiendaUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    prod = db.query(ProductoTienda).filter(ProductoTienda.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    prod.nombre = producto.nombre
    prod.descripcion = producto.descripcion
    prod.tipo = producto.tipo
    prod.cantidad_semillas = producto.cantidad_semillas
    prod.precio_moneda_local = producto.precio_moneda_local
    prod.icono = producto.icono
    prod.recomendado = producto.recomendado
    prod.activo = producto.activo
    
    db.commit()
    return {"message": "Producto actualizado"}

# ==========================================
# ⏱️ PROMOCIONES DE SKINS
# ==========================================

class PromocionCreate(BaseModel):
    precio_oferta: int
    fecha_inicio: datetime
    fecha_fin: datetime

@router.get("/skins/promociones")
def listar_promociones(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return db.query(PromocionSkin).all()

@router.post("/skins/{id}/promocion")
def crear_promocion_skin(id: int, promo: PromocionCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    # Eliminar promo anterior si existe
    db.query(PromocionSkin).filter(PromocionSkin.id_skin == id).delete()
    
    nueva_promo = PromocionSkin(
        id_skin=id,
        precio_oferta=promo.precio_oferta,
        fecha_inicio=promo.fecha_inicio,
        fecha_fin=promo.fecha_fin
    )
    db.add(nueva_promo)
    db.commit()
    return {"message": "Promoción creada"}

@router.delete("/skins/promocion/{id}")
def eliminar_promocion(id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    db.query(PromocionSkin).filter(PromocionSkin.id == id).delete()
    db.commit()
    return {"message": "Promoción eliminada"}

# Inicializador rápido de tablas
@router.post("/tienda/init")
def init_tienda_tables(db: Session = Depends(get_db)):
    db.execute(text("""
    CREATE TABLE IF NOT EXISTS productos_tienda (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        descripcion VARCHAR(255) NULL,
        tipo VARCHAR(50) NOT NULL,
        cantidad_semillas INT DEFAULT 0,
        precio_moneda_local FLOAT NOT NULL,
        icono VARCHAR(10) DEFAULT '🌱',
        recomendado BOOLEAN DEFAULT FALSE,
        activo BOOLEAN DEFAULT TRUE
    );
    """))
    db.execute(text("""
    CREATE TABLE IF NOT EXISTS promociones_skins (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_skin INT NOT NULL,
        precio_oferta INT NOT NULL,
        fecha_inicio DATETIME NOT NULL,
        fecha_fin DATETIME NOT NULL,
        FOREIGN KEY (id_skin) REFERENCES skins(id) ON DELETE CASCADE
    );
    """))
    db.execute(text("""
    INSERT IGNORE INTO productos_tienda (id, nombre, tipo, cantidad_semillas, precio_moneda_local, icono, recomendado) VALUES
    (1, 'Paquete Basico', 'semilla', 500, 0.99, '🌱', FALSE),
    (2, 'Paquete Medio', 'semilla', 1200, 1.99, '🌿', FALSE),
    (3, 'Paquete Avanzado', 'semilla', 3000, 3.99, '🌳', TRUE),
    (4, 'Paquete Experto', 'semilla', 8000, 8.99, '🌍', FALSE),
    (5, 'Club Tonalkab Premium', 'suscripcion', 1000, 4.99, '⭐', FALSE);
    """))
    db.commit()
    return {"message": "Tablas creadas e inicializadas."}
