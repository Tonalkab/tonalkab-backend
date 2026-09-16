import os
from dotenv import load_dotenv

# Cargar las variables del .env
load_dotenv()

print('--- MODELOS DE GEMINI (GOOGLE) ---')
try:
    from google import genai
    api_key_gemini = os.getenv('GEMINI_API_KEY')
    if api_key_gemini:
        client = genai.Client(api_key=api_key_gemini)
        # client.models.list() retorna un iterador
        modelos_gemini = client.models.list()
        for m in modelos_gemini:
            print(f' - {m.name}')
    else:
        print('No se encontró GEMINI_API_KEY en el .env')
except ImportError:
    print('Librería google-genai no instalada')
except Exception as e:
    print(f'Error al conectar con Gemini: {e}')

print('\n--- MODELOS DE GROQ (LLAMA) ---')
try:
    from groq import Groq
    api_key_groq = os.getenv('GROQ_API_KEY')
    if api_key_groq:
        client = Groq(api_key=api_key_groq)
        modelos_groq = client.models.list().data
        for m in modelos_groq:
            print(f' - {m.id}')
    else:
        print('No se encontró GROQ_API_KEY en el .env')
except ImportError:
    print('Librería groq no instalada')
except Exception as e:
    print(f'Error al conectar con Groq: {e}')
