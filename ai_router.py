import asyncio
from fastapi import APIRouter
from typing import List

import schemas

router = APIRouter(
    prefix="/api/ai",
    tags=["IA (Placeholder)"],
)

# --- NOTA: Funcionalidad de IA reemplazada por placeholders ---
# Las siguientes funciones simulan las respuestas de la IA para
# permitir el desarrollo del frontend sin una API key de IA activa.

@router.post("/profile-assistant", response_model=schemas.ProfileAssistantResponse)
async def profile_assistant(req: schemas.ProfileAssistantRequest):
    """
    Simula la conversación con el asistente de perfil.
    Responde a preguntas y genera una biografía de ejemplo al final.
    """
    await asyncio.sleep(0.5) # Simula la latencia de la red
    num_user_messages = len([msg for msg in req.chat_history if msg.get('role') == 'user'])

    questions = [
        "¡Hola! Soy Vibrai Assist (simulado). Te haré 5 preguntas para crear un buen perfil. Primero, ¿qué te encanta hacer en tu tiempo libre?",
        "¡Genial! Segunda pregunta: ¿Cuál es tu mayor pasión o algo que te ilumina los ojos al hablar de ello?",
        "Interesante. Tercera pregunta: ¿Cómo te describirían tus amigos en tres palabras?",
        "Ya casi terminamos. Cuarta pregunta: ¿Qué buscas en una conexión con alguien (amistad, algo serio, etc.)?",
        "Última pregunta: Si tuvieras un superpoder, ¿cuál sería y por qué?"
    ]

    if num_user_messages < len(questions):
        # Devuelve la siguiente pregunta de la lista
        return {
            "responseText": questions[num_user_messages],
            "generatedBio": None,
            "isProfileComplete": False,
        }
    else:
        # Después de la última pregunta, genera una biografía de ejemplo
        return {
            "responseText": "¡Perfecto! He creado una biografía de ejemplo para ti basada en tus respuestas. ¡Puedes editarla si quieres!",
            "generatedBio": "Aventurero/a apasionado/a por el senderismo y la fotografía. Mis amigos dicen que soy leal y divertido/a. Busco una conexión genuina para compartir risas y explorar el mundo. Mi superpoder sería volar para viajar a cualquier lugar al instante.",
            "isProfileComplete": True,
        }

@router.post("/generate-interests", response_model=List[str])
async def generate_interests(req: schemas.GenerateInterestsRequest):
    """Simula la generación de intereses a partir de una biografía."""
    await asyncio.sleep(0.5)
    return ["Viajes", "Fotografía", "Senderismo", "Cocina", "Música Indie", "Cine de Autor"]

@router.post("/suggest-icebreaker", response_model=str)
async def suggest_icebreaker(req: schemas.SuggestIcebreakerRequest):
    """Simula la sugerencia de un rompehielos."""
    await asyncio.sleep(0.5)
    interest = req.user_interests[0] if req.user_interests and req.user_interests[0] else "viajar"
    return f"¡Hola {req.user_name}! He visto que te interesa '{interest}', ¡a mí también! ¿Cuál es tu mejor recuerdo relacionado con eso?"

@router.post("/suggest-replies", response_model=List[str])
async def suggest_replies(req: schemas.SuggestRepliesRequest):
    """Simula la sugerencia de respuestas de chat."""
    await asyncio.sleep(0.5)
    return [
        "¡Jaja, qué bueno!",
        "¿En serio? Cuéntame más sobre eso.",
        "Y tú, ¿qué opinas al respecto?",
    ]

@router.post("/rewrite-message", response_model=str)
async def rewrite_message(req: schemas.RewriteMessageRequest):
    """Simula la reescritura de un mensaje."""
    await asyncio.sleep(0.5)
    return f"{req.original_message} (versión simulada más amigable)"