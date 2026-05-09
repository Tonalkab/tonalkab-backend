from google import genai
from sqlalchemy.orm import Session
from app.models.maceta import Maceta
from app.models.lectura import LecturaSensores
from app.models.tipo_planta import TipoPlanta
import os

# 🛠️ Función que el Bot usará para "ver" tus plantas
def consultar_mis_plantas(id_usuario: int, db: Session):
    """
    Busca en la base de datos de Tonalkab el estado actual 
    de todas las macetas del usuario.
    """
    macetas = db.query(Maceta).filter(Maceta.id_usuario == id_usuario).all()
    
    if not macetas:
        return "El usuario aún no tiene macetas registradas."

    datos = []
    for m in macetas:
        # Buscamos la última lectura de humedad y temperatura
        lectura = db.query(LecturaSensores).filter(
            LecturaSensores.id_maceta == m.id_maceta
        ).order_by(LecturaSensores.fecha_hora.desc()).first()
        
        estado = f"Maceta '{m.nombre_maceta}': "
        if lectura:
            estado += f"Humedad {lectura.humedad_suelo}%, Temp {lectura.temperatura}°C."
        else:
            estado += "Sin datos de sensores aún."
        datos.append(estado)
    
    return "\n".join(datos)

# 🤖 Configuración del Chat
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Instrucciones de personalidad
SYSTEM_PROMPT = """
Eres el experto botánico de Tonalkab. Tu tono es tecnológico pero amigable. 
Ayuda al usuario a entender cómo están sus plantas usando los datos de sus sensores.
Si el usuario pregunta algo general de botánica, responde con tu conocimiento.
Si pregunta por sus plantas, usa la herramienta 'consultar_mis_plantas'.
"""