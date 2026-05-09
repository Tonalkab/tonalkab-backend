from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from google import genai
from google.genai import types

# Importaciones de tu ecosistema Tonalkab
from app.db import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.services.ai_bot import consultar_mis_plantas

router = APIRouter(prefix="/bot", tags=["Asistente IA"])

# Esquemas para la petición y respuesta
class BotChatRequest(BaseModel):
    mensaje: str

class BotChatResponse(BaseModel):
    respuesta: str

@router.post("/chat", response_model=BotChatResponse)
def chatear_con_bot(
    request: BotChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 🔒 SEGURIDAD: Exige token JWT válido
):
    try:
        # 1. Inicializamos el cliente
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # 2. 🛡️ EL TRUCO DE SEGURIDAD (Closure)
        # Creamos una función anónima dentro del endpoint que YA tiene "quemado" 
        # el id_usuario del JWT y la sesión de la base de datos.
        def herramienta_ver_estado_plantas() -> str:
            """Usa esta herramienta para consultar el estado actual de los sensores de las macetas del usuario."""
            return consultar_mis_plantas(current_user.id_usuario, db)

        # 3. Configuramos la personalidad y le entregamos la herramienta segura
        instrucciones = """
        Eres Tonalli, el asistente experto en botánica de Tonalkab.
        Hablas de forma amigable, tecnológica y concisa.
        SIEMPRE que el usuario pregunte por 'mis plantas', 'mis macetas' o su estado, 
        DEBES usar la herramienta 'herramienta_ver_estado_plantas' antes de responder.
        """
        
        config = types.GenerateContentConfig(
            system_instruction=instrucciones,
            tools=[herramienta_ver_estado_plantas], # Le pasamos la función segura
            temperature=0.7, # 0.7 le da un tono natural sin inventar demasiados datos
        )

        # 4. Enviamos el mensaje a Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request.mensaje,
            config=config
        )

        return BotChatResponse(respuesta=response.text)

    except Exception as e:
        print(f"Error en IA: {e}")
        raise HTTPException(status_code=500, detail="Error interno del asistente botánico.")