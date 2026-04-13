from fastapi import FastAPI
import time
from app.db import Base, engine
from app.api.user import router as user_router
from app.api.auth import router as auth_router
from app.api import maceta
from app.api import device  # <-- 1. Importar el nuevo módulo
from app.models import tipo_planta
from app.models import lectura
from app.models import conexion 
from app.api import conexion as api_conexion
from app.models import catalogos_planta
from app.models import control_riego
from app.models import configuracion_maceta
from app.models import predicciones_ml
import asyncio
from app.core.tasks import limpiar_conexiones_inactivas
from app.api import catalogos
from app.models import alerta
from app.api import alerta as api_alerta

app = FastAPI()

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

# Registrar Routers
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(maceta.router)
app.include_router(device.router) # <-- 2. Incluir el router de dispositivos
app.include_router(api_conexion.router)
app.include_router(catalogos.router)
app.include_router(api_alerta.router)

@app.get("/")
def root():
    return {"message": "Tonalkab API funcionando"}



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