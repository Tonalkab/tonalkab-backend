from fastapi import FastAPI
import time
from app.db import Base, engine
from app.api.user import router as user_router
from app.api.auth import router as auth_router
from app.api import maceta
from app.api import device  # <-- 1. Importar el nuevo módulo
from app.models import tipo_planta
from app.models import lectura

app = FastAPI()

@app.on_event("startup")
def startup():
    for i in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Tablas creadas")
            break
        except Exception as e:
            print(f"⏳ Esperando MySQL... intento {i+1}")
            time.sleep(3)

# Registrar Routers
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(maceta.router)
app.include_router(device.router) # <-- 2. Incluir el router de dispositivos

@app.get("/")
def root():
    return {"message": "Tonalkab API funcionando"}