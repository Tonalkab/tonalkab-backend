from app.api import bot
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles 
import time
import os 
import asyncio

from app.db import Base, engine
from app.api.user import router as user_router
from app.api.auth import router as auth_router
from app.api import maceta
from app.api import device  
from app.api import conexion as api_conexion
from app.api import catalogos
from app.api import alerta as api_alerta
from app.api import skins 
from app.api import admin as api_admin

# Importar modelos para que Base.metadata.create_all los detecte
from app.models import tipo_planta
from app.models import lectura
from app.models import conexion 
from app.models import catalogos_planta
from app.models import control_riego
from app.models import configuracion_maceta
from app.models import predicciones_ml
from app.models import alerta
from app.models import skin 

from app.core.tasks import limpiar_conexiones_inactivas
from app.core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Tonalkab API", description="API Core para la plataforma de monitoreo inteligente Tonalkab")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------
# CORS CONFIGURATION
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitimos cualquier origen (incluyendo web local o produccion)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS (SKINS)
# ---------------------------------------------------------
# 1. Obtiene la ruta absoluta de la carpeta 'app' (donde vive este main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 2. Construye la ruta hacia la carpeta 'assets' que está dentro de 'app'
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# 3. Crea la ruta (apuntará correctamente a la carpeta física sin importar el OS)
os.makedirs(os.path.join(ASSETS_DIR, "skins"), exist_ok=True)

# 4. Monta los estáticos
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


# ---------------------------------------------------------
# EVENTO DE INICIO (Unificado)
# ---------------------------------------------------------
@app.on_event("startup")
def startup():
    for i in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Tablas creadas")
            break
        except Exception as e:
            print(f"⏳ Error en BD (intento {i+1}): {e}")
            time.sleep(3)
            
    asyncio.create_task(limpiar_conexiones_inactivas())
    print("🧹 Tarea de limpieza de conexiones activada")


# ---------------------------------------------------------
# REGISTRO DE ROUTERS
# ---------------------------------------------------------
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(maceta.router)
app.include_router(device.router) 
app.include_router(api_conexion.router)
app.include_router(catalogos.router)
app.include_router(api_alerta.router)
app.include_router(skins.router) 
app.include_router(api_admin.router)
app.include_router(bot.router)

@app.get("/")
def root():
    return {"message": "Tonalkab API funcionando"}