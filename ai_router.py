import os
import json
import re
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import schemas
from constants import GEMINI_TEXT_MODEL

router = APIRouter(
    prefix="/api/ai",
    tags=["IA"],
)

# --- INICIO DE LA CORRECCIÓN IMPORTANTE ---
# El error 'ImportError: cannot import name 'GoogleGenerativeAI'' se debe a que la 
# librería de Python ha cambiado. La forma correcta de inicializar es usando
# genai.configure() y luego creando un modelo con genai.GenerativeModel().

try:
    # Configura la API key a nivel de módulo
    genai.configure(api_key=os.environ["API_KEY"])
except KeyError:
    raise RuntimeError("La variable de entorno API_KEY no está configurada.")
except Exception as e:
    raise RuntimeError(f"Error al configurar el cliente de IA: {e}")

# Crea una instancia del modelo generativo que usaremos en los endpoints
model = genai.GenerativeModel(GEMINI_TEXT_MODEL)
# --- FIN DE LA CORRECCIÓN IMPORTANTE ---


# Configuración de seguridad para la IA
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def parse_json_from_response(text: str) -> list | dict:
    """Extrae un bloque de código JSON de una respuesta de texto de la IA."""
    text = text.strip()
    match = re.search(r"```(json)?\s*(.*?)\s*```", text, re.DOTALL)
    json_str = match.group(2) if match else text
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        print(f"String problemático: {json_str}")
        raise ValueError("La respuesta de la IA no contenía un JSON válido.")

@router.post("/profile-assistant", response_model=schemas.ProfileAssistantResponse)
async def profile_assistant(req: schemas.ProfileAssistantRequest):
    system_instruction = "Eres Vibrai Assist, un coach de citas experto. Tu objetivo es ayudar al usuario a crear un perfil atractivo haciéndole 5 preguntas concisas, una por una. Al final, escribe una biografía de 2-3 frases basada en TODAS las respuestas. Responde SIEMPRE en formato JSON: {\"responseText\": \"tu respuesta conversacional\", \"generatedBio\": \"biografía final (o null)\", \"isProfileComplete\": boolean}"
    
    # El historial ya viene en el formato correcto desde el frontend
    contents = req.chat_history
    contents.append({"role": "user", "parts": [{"text": req.user_message}]})
    
    chat = model.start_chat(history=contents[:-1]) # Inicia el chat con el historial previo
    chat.system_instruction = system_instruction

    try:
        response = await chat.send_message_async(
            req.user_message,
            safety_settings=SAFETY_SETTINGS
        )
        # La API de Gemini ahora puede devolver JSON directamente si se le indica
        # en el prompt, pero por seguridad lo parseamos.
        response_data = parse_json_from_response(response.text)
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el asistente de perfil: {e}")

@router.post("/generate-interests", response_model=List[str])
async def generate_interests(req: schemas.GenerateInterestsRequest):
    prompt = f"Basado en la siguiente biografía de un perfil de citas, extrae una lista de 5 a 7 intereses clave en español. Devuelve la respuesta únicamente como un array de strings en formato JSON. Biografía: '{req.bio_text}'"
    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
            safety_settings=SAFETY_SETTINGS
        )
        return parse_json_from_response(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar intereses: {e}")

# Otros endpoints de IA usando la nueva sintaxis
@router.post("/suggest-icebreaker", response_model=str)
async def suggest_icebreaker(req: schemas.SuggestIcebreakerRequest):
    prompt = f"Sugiere un rompehielos creativo y divertido para iniciar una conversación con {req.user_name}. Intereses de {req.user_name}: {', '.join(req.user_interests or [])}. Es el intento número {req.attempt_number}, sé original. Devuelve solo el texto del mensaje."
    try:
        response = await model.generate_content_async(prompt, safety_settings=SAFETY_SETTINGS)
        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sugerir rompehielos: {e}")

@router.post("/suggest-replies", response_model=List[str])
async def suggest_replies(req: schemas.SuggestRepliesRequest):
    prompt = f"Tu nombre es {req.own_name}. Estás en un chat con {req.chat_partner_name}. El último mensaje de {req.chat_partner_name} fue: '{req.last_message_text}'. Sugiere 3 respuestas cortas e ingeniosas para continuar la conversación. Devuelve un array de strings en formato JSON."
    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
            safety_settings=SAFETY_SETTINGS
        )
        return parse_json_from_response(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sugerir respuestas: {e}")

@router.post("/rewrite-message", response_model=str)
async def rewrite_message(req: schemas.RewriteMessageRequest):
    prompt = f"Reescribe el siguiente mensaje para que suene más {req.rewrite_goal} y atractivo: '{req.original_message}'. Devuelve solo el texto del mensaje reescrito."
    try:
        response = await model.generate_content_async(prompt, safety_settings=SAFETY_SETTINGS)
        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al reescribir el mensaje: {e}")