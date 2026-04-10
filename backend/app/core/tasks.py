# Archivo: app/core/tasks.py
import asyncio
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models.conexion import ConexionDispositivo
from app.models.maceta import Maceta

async def limpiar_conexiones_inactivas():
    """
    Se ejecuta en bucle mientras el servidor esté vivo.
    Busca macetas que no han reportado en los últimos 5 minutos.
    """
    # Esperamos 10 segundos antes de la primera ejecución para dar tiempo a que la DB inicie
    await asyncio.sleep(10) 
    
    while True:
        db = SessionLocal() # Abrimos una sesión de BD exclusiva para esta tarea
        try:
            ahora = datetime.utcnow()
            limite_tiempo = ahora - timedelta(minutes=5)

            # 1. Buscar conexiones que se quedaron en "conectado" pero ya pasó su límite
            conexiones_muertas = db.query(ConexionDispositivo).filter(
                ConexionDispositivo.ultima_conexion < limite_tiempo,
                ConexionDispositivo.estado_conexion == "conectado"
            ).all()

            if conexiones_muertas:
                for conexion in conexiones_muertas:
                    # Marcamos la conexión local como desconectada
                    conexion.estado_conexion = "desconectado"
                    
                    # Buscamos la maceta global para apagarla también
                    maceta = db.query(Maceta).filter(Maceta.id_maceta == conexion.id_maceta).first()
                    if maceta and maceta.id_estado_dispositivo != 2:
                        maceta.id_estado_dispositivo = 2 # 2 = Desconectado
                
                db.commit()
                print(f"🧹 Limpiador: {len(conexiones_muertas)} maceta(s) marcada(s) como desconectada(s) por inactividad.")

        except Exception as e:
            print(f"⚠️ Error en el limpiador de conexiones: {e}")
            db.rollback()
        finally:
            db.close() # Siempre cerramos la sesión para no saturar MySQL

        # Dormir la tarea por 2 minutos (120 segundos) antes de volver a barrer
        await asyncio.sleep(120)

        