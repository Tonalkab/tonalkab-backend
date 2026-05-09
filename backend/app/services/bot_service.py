# Archivo: app/services/bot_service.py
from sqlalchemy.orm import Session
from app.models.maceta import Maceta
from app.models.lectura import LecturaSensores
from app.models.tipo_planta import TipoPlanta
import google.generativeai as genai
import os

def obtener_estado_mis_plantas(id_usuario: int, db: Session) -> str:
    """
    Esta es la HERRAMIENTA que usará Gemini. 
    Busca todas las macetas del usuario y su última lectura de sensores.
    """
    macetas = db.query(Maceta).filter(Maceta.id_usuario == id_usuario).all()
    
    if not macetas:
        return "El usuario no tiene ninguna maceta registrada."

    reporte = []
    for maceta in macetas:
        # Obtenemos la información botánica
        planta = db.query(TipoPlanta).filter(TipoPlanta.id_tipo_planta == maceta.id_tipo_planta).first()
        
        # Obtenemos la última lectura de sensores
        ultima_lectura = db.query(LecturaSensores).filter(
            LecturaSensores.id_maceta == maceta.id_maceta
        ).order_by(LecturaSensores.fecha_hora.desc()).first()

        estado = f"- Maceta: {maceta.nombre_maceta} (Planta: {planta.nombre_planta if planta else 'Desconocida'})"
        if ultima_lectura:
            estado += f" | Humedad del suelo: {ultima_lectura.humedad_suelo}% | Temperatura: {ultima_lectura.temperatura}°C | Nivel de agua: {ultima_lectura.nivel_agua}%"
        else:
            estado += " | Sin lecturas recientes de sensores."
            
        reporte.append(estado)

    # Devolvemos un texto estructurado que Gemini pueda leer e interpretar
    return "\n".join(reporte)



# Configuramos la API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Definimos el System Prompt (La personalidad de tu bot)
instrucciones_bot = """
Eres el asistente virtual experto en botánica y tecnología de la aplicación 'Tonalkab'.
Tu objetivo es ayudar a los usuarios con el cuidado de sus plantas.
Tienes acceso a una herramienta para ver el estado actual de los sensores de las macetas del usuario.
Sé amable, conciso y utiliza emojis. Explica las cosas de forma sencilla.
"""

# Inicializamos el modelo Gemini 3 Flash
modelo_tonalkab = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # Usamos la versión Flash para latencia baja
    system_instruction=instrucciones_bot,
    tools=[obtener_estado_mis_plantas] # ¡Aquí le pasamos tu función!
)