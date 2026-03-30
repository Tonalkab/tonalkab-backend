from fastapi import FastAPI
from app.db import engine, Base
from app.api.user import router as user_router
from app.api.auth import router as auth_router
import time

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

app.include_router(user_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Tonalkab API funcionando"}