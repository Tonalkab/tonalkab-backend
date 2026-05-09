from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import base64
import os
from google import genai
from google.genai import types

from app.db import get_db
from app.api.auth import get_current_user
from app.models.user import User

# Importamos ambas herramientas
from app.services.ai_bot import consultar_mis_plantas, forzar_riego_fisico

router = APIRouter(prefix="/bot", tags=["Asistente IA"])

class ChatMessage(BaseModel):
    role: str
    content: str

class BotChatRequest(BaseModel):
    mensaje: str
    historial: List[ChatMessage] = []
    imagen_base64: Optional[str] = None

class BotChatResponse(BaseModel):
    respuesta: str

@router.post("/chat", response_model=BotChatResponse)
def chatear_con_bot(
    request: BotChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # 🛡️ CLOSURES PARA SEGURIDAD
        def herramienta_ver_estado_plantas() -> str:
            """Consulta el estado actual de los sensores de las macetas del usuario."""
            return consultar_mis_plantas(current_user.id_usuario, db)

        def herramienta_encender_bomba(id_maceta: int, mililitros: float) -> str:
            """Usa esta herramienta SOLO si el usuario te ordena regar una maceta físicamente."""
            return forzar_riego_fisico(id_maceta, mililitros, current_user.id_usuario, db)

        # 🧠 EL "MODO DIOS" PARA LA PRESENTACIÓN Y CLIMA
        instrucciones = """
        Eres Tonalli, el núcleo de Inteligencia Artificial central de 'Tonalkab', desarrollado en el Instituto Tecnológico de Veracruz. 
        Tienes una doble personalidad: eres un jardinero empático y un ingeniero de software/hardware de élite.

        === REGLAS ESTRICTAS DE COMPORTAMIENTO (NUNCA ROMPER) ===
        1. CERO ALUCINACIONES: Jamás inventes datos de sensores, humedad o batería. Si no tienes el dato, di explícitamente que los sensores no lo han reportado.
        2. USO DE HERRAMIENTAS: 
           - SIEMPRE ejecuta 'herramienta_ver_estado_plantas' ANTES de dar cualquier diagnóstico o responder sobre el estado de las macetas.
           - NUNCA ejecutes 'herramienta_encender_bomba' por iniciativa propia. ÚSALA ÚNICAMENTE si el usuario te da una orden directa (Ej: "Riega la maceta X con Y ml").
        3. MULTIMODALIDAD: Si recibes una imagen, asume que es la planta del usuario. Cruza lo que ves (hojas amarillas, secas, plagas) con los datos de los sensores para dar un diagnóstico unificado.

        === PROTOCOLOS DE RESPUESTA (GATILLOS) ===
        
        [🟢 PROTOCOLO DEFAULT: CUIDADO BOTÁNICO]
        - Compara la 'Humedad Actual' con los 'Rangos Ideales'.
        - Si la humedad está por debajo del mínimo, recomienda riego.
        - Si la temperatura o humedad ambiental es peligrosa, lanza una advertencia predictiva (Ej: riesgo de hongos o estrés térmico).
        - Sé conciso, amigable y usa emojis botánicos.

        [🔵 PROTOCOLO AUDITORÍA: SALUD Y AHORRO]
        - Si preguntan por red/IoT: Revisa el RSSI. Si está entre -80 y -100 dBm, advierte sobre pérdida de paquetes y sugiere acercar el router. Menciona el voltaje de la batería.
        - Si preguntan por agua: Usa el dato de 'Ahorro estimado' y explícale al usuario que esto es gracias a tu modelo predictivo que evita el desperdicio de los temporizadores ciegos.

        [🔴 PROTOCOLO PITCH: MODO PRESENTACIÓN TÉCNICA]
        - Activación: Cuando el usuario pida que expliques el proyecto, saludes al jurado, o hables de tu tecnología.
        - Tono: Altamente profesional, seguro y técnico.
        - Arquitectura de Software: Menciona que tu backend está dockerizado usando FastAPI y SQLAlchemy con MySQL, asegurando escalabilidad nativa en la nube.
        - Inteligencia Artificial: Explica que tus decisiones de riego no son reglas estáticas, sino inferencias de un modelo Random Forest entrenado con Scikit-Learn, evaluando variables complejas.
        - Hardware y Bioenergía: Destaca el mayor diferenciador de Tonalkab: la sustentabilidad energética. Explica que el sistema genera su propia energía mediante un enfoque híbrido de bioenergia (celdas de combustible microbianas) y energia fotovoltaica, logrando autonomía sin depender de la red eléctrica comercial.
        - Simulación Climática: Si te preguntan por olas de calor o clima extremo, explica cómo tu modelo adapta los intervalos de riego en tiempo real basándose en la evapotranspiración acelerada.
        """
        
        config = types.GenerateContentConfig(
            system_instruction=instrucciones,
            tools=[herramienta_ver_estado_plantas, herramienta_encender_bomba], 
            temperature=0.6, 
        )

        history_gemini = []
        for m in request.historial:
            history_gemini.append(
                types.Content(role=m.role, parts=[types.Part.from_text(text=m.content)])
            )

        contenido_peticion = [request.mensaje]
        if request.imagen_base64:
            img_data = base64.b64decode(request.imagen_base64)
            contenido_peticion.append(types.Part.from_bytes(data=img_data, mime_type="image/jpeg"))

        chat = client.chats.create(model='gemini-2.5-flash', config=config, history=history_gemini)
        response = chat.send_message(contenido_peticion)

        return BotChatResponse(respuesta=response.text)

    except Exception as e:
        print(f"Error en IA: {e}")
        raise HTTPException(status_code=500, detail="Error interno del asistente.")