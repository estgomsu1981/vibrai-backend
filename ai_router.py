import os
import json
from fastapi import APIRouter, Depends, HTTPException
from google.generativeai import GoogleGenerativeAI
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import schemas
from constants import GEMINI_TEXT_MODEL

router = APIRouter(
    prefix="/api/ai",
    tags=["IA"],
)

# Configuración de seguridad para la IA
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

try:
    ai = GoogleGenerativeAI(api_key=os.environ["API_KEY"])
except KeyError:
    raise RuntimeError("La variable de entorno API_KEY no está configurada.")
except Exception as e:
    raise RuntimeError(f"Error al inicializar el cliente de IA: {e}")

def parse_json_from_response(text: str) -> list | dict:
    """Extrae un bloque de código JSON de una respuesta de texto."""
    text = text.strip()
    match = re.search(r"```(json)?\n?(.*?)\n?```", text, re.S)
    if match:
        json_str = match.group(2).strip()
    else:
        json_str = text

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        print(f"String problemático: {json_str}")
        raise ValueError("La respuesta de la IA no contenía un JSON válido.")

@router.post("/profile-assistant")
async def profile_assistant(req: schemas.ProfileAssistantRequest):
    system_instruction = (
        "Eres Vibrai Assist, un coach de citas experto y amigable para una app llamada Vibrai. "
        "Tu objetivo es ayudar al usuario a crear un perfil atractivo haciéndole 5 preguntas concisas, una por una. "
        "Debes ser breve, casual y alentador. No reveles que eres un modelo de IA. "
        "Cuando respondas a la quinta pregunta, finaliza la conversación con un mensaje de despedida y, "
        "en el campo 'generatedBio' del JSON, escribe una biografía de 2-3 frases basada en TODAS las respuestas del usuario. "
        "Las 5 preguntas son: "
        "1. ¿Qué te encanta hacer en tu tiempo libre? "
        "2. ¿Cuál es tu mayor pasión o algo que te ilumina los ojos al hablar de ello? "
        "3. ¿Cómo te describirían tus amigos en tres palabras? "
        "4. ¿Qué buscas en una conexión con alguien (amistad, algo serio, etc.)? "
        "5. Si tuvieras un superpoder, ¿cuál sería y por qué? "
        "Estructura tu respuesta SIEMPRE en formato JSON: {\"responseText\": \"tu respuesta conversacional\", \"generatedBio\": \"biografía final (o null)\", \"isProfileComplete\": boolean}"
    )
    
    contents = [{"role": "system", "parts": [{"text": system_instruction}]}]
    contents.extend(req.chat_history)
    contents.append({"role": "user", "parts": [{"text": req.user_message}]})

    try:
        response = await ai.models.generateContent(
            model=GEMINI_TEXT_MODEL,
            contents=contents,
            config={"responseMimeType": "application/json"},
            safety_settings=SAFETY_SETTINGS,
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud con IA: {e}")


@router.post("/generate-interests", response_model=List[str])
async def generate_interests(req: schemas.GenerateInterestsRequest):
    prompt = (
        "Basado en la siguiente biografía de un perfil de citas, extrae una lista de 5 a 7 intereses clave. "
        "Devuelve la respuesta únicamente como un array de strings en formato JSON. Biografía: "
        f"'{req.bio_text}'"
    )
    try:
        response = await ai.models.generateContent(
            model=GEMINI_TEXT_MODEL,
            contents=prompt,
            config={"responseMimeType": "application/json"},
            safety_settings=SAFETY_SETTINGS,
        )
        # El modelo debería devolver JSON directamente
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar intereses con IA: {e}")


@router.post("/suggest-icebreaker", response_model=str)
async def suggest_icebreaker(req: schemas.SuggestIcebreakerRequest):
    prompt = (
        f"Actúa como un experto en citas. Sugiere un rompehielos creativo y divertido para iniciar una conversación con {req.user_name}. "
        f"Si están disponibles, basa la sugerencia en sus intereses: {', '.join(req.user_interests or [])}. "
        f"Este es el intento número {req.attempt_number}, intenta que sea diferente a los anteriores. "
        "Sé breve y directo. Devuelve solo el texto del mensaje, sin comillas ni saludos."
    )
    try:
        response = await ai.models.generateContent(
            model=GEMINI_TEXT_MODEL, contents=prompt, safety_settings=SAFETY_SETTINGS
        )
        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sugerir rompehielos: {e}")

@router.post("/suggest-replies", response_model=List[str])
async def suggest_replies(req: schemas.SuggestRepliesRequest):
    prompt = (
        f"Estás en un chat de citas. Tu nombre es {req.own_name} y hablas con {req.chat_partner_name}. "
        f"El último mensaje que recibiste de {req.chat_partner_name} fue: '{req.last_message_text}'. "
        "Sugiere 3 respuestas cortas, ingeniosas y que inviten a continuar la conversación. "
        "Devuelve las sugerencias como un array de strings en formato JSON."
    )
    try:
        response = await ai.models.generateContent(
            model=GEMINI_TEXT_MODEL,
            contents=prompt,
            config={"responseMimeType": "application/json"},
            safety_settings=SAFETY_SETTINGS,
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sugerir respuestas: {e}")

@router.post("/rewrite-message", response_model=str)
async def rewrite_message(req: schemas.RewriteMessageRequest):
    prompt = f"Reescribe el siguiente mensaje para un chat de citas para que suene más amigable y atractivo. Mensaje original: '{req.original_message}'"
    try:
        response = await ai.models.generateContent(
            model=GEMINI_TEXT_MODEL, contents=prompt, safety_settings=SAFETY_SETTINGS
        )
        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al reescribir el mensaje: {e}")