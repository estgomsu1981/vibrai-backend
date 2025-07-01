# main.py
import os
import re
import json
import uvicorn
from typing import List, Any, Optional

from fastapi import FastAPI, HTTPException, Body, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# --- Importaciones de Módulos Locales ---
import crud
import schemas
import sql_models 
from database import get_db, engine

# --- Creación de Tablas en la Base de Datos ---
sql_models.Base.metadata.create_all(bind=engine)

# --- Configuración de la API de Gemini ---
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("API_KEY")
    if not GEMINI_API_KEY:
        print("ADVERTENCIA: La variable de entorno API_KEY no está configurada.")
        genai = None
    else:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    print("ADVERTENCIA: La librería 'google-generativeai' no está instalada.")
    genai = None

# --- Modelos Pydantic (específicos de los endpoints de IA) ---
class Part(BaseModel):
    text: str

class Content(BaseModel):
    role: str
    parts: List[Part]

class ProfileAssistantRequest(BaseModel):
    user_message: str = Field(..., alias="userMessage")
    chat_history: List[Content] = Field(..., alias="chatHistory")

class GenerateInterestsRequest(BaseModel):
    bio_text: str = Field(..., alias="bioText")

class SuggestIcebreakerRequest(BaseModel):
    user_name: str = Field(..., alias="userName")
    user_interests: Optional[List[str]] = Field(None, alias="userInterests")
    attempt_number: int = Field(1, alias="attemptNumber")

class SuggestRepliesRequest(BaseModel):
    last_message_text: str = Field(..., alias="lastMessageText")
    own_name: str = Field(..., alias="ownName")
    chat_partner_name: str = Field(..., alias="chatPartnerName")

class RewriteMessageRequest(BaseModel):
    original_message: str = Field(..., alias="originalMessage")
    rewrite_goal: str = Field("default", alias="rewriteGoal")

# --- Inicialización de FastAPI ---
app = FastAPI(
    title="Vibrai Backend",
    description="API para la aplicación de citas Vibrai con integración de IA y base de datos.",
    version="1.3.0"
)

# --- Middleware de CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Funciones de Ayuda de IA ---
def get_ai_model(model_name: str = 'gemini-2.5-flash-preview-04-17', system_instruction: Optional[str] = None):
    if not genai:
        raise HTTPException(status_code=503, detail="El servicio de IA no está disponible.")
    try:
        if system_instruction:
            model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
            return model
        return genai.GenerativeModel(model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo inicializar el modelo de IA: {e}")

def parse_json_from_gemini(text: str) -> Any:
    match = re.search(r"```(json)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    json_str = match.group(2).strip() if match else text.strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="La IA devolvió un JSON con formato incorrecto.")

# --- Endpoints de la API ---
@app.get("/")
def read_root():
    return {"message": "Bienvenido al backend de Vibrai"}

# --- Endpoints de Datos (Conectados a la Base de Datos) ---

@app.get("/api/profile", response_model=schemas.User)
def get_user_profile(db: Session = Depends(get_db)):
    # Asumimos que el ID del usuario actual es 'currentUser' para este ejemplo.
    user_id = "currentUser"
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario '{user_id}' no encontrado en la base de datos.")
    return user

@app.get("/api/matches", response_model=List[schemas.User])
def get_discovery_matches(db: Session = Depends(get_db)):
    user_id = "currentUser"
    matches = crud.get_discovery_profiles(db, user_id=user_id)
    return matches

@app.get("/api/connections", response_model=List[schemas.User])
def get_user_connections(db: Session = Depends(get_db)):
    user_id = "currentUser"
    connections = crud.get_connections_for_user(db, user_id=user_id)
    return connections

@app.post("/api/like/{liked_user_id}", response_model=schemas.LikeResponse)
def like_a_user(liked_user_id: str = Path(...), db: Session = Depends(get_db)):
    liker_id = "currentUser"
    
    # Prevenir que un usuario se dé like a sí mismo
    if liker_id == liked_user_id:
        raise HTTPException(status_code=400, detail="No puedes darte 'me gusta' a ti mismo.")

    # Registrar el like
    crud.create_like(db, liker_id=liker_id, liked_id=liked_user_id)

    # Comprobar si es un match (si el otro usuario ya había dado like)
    is_match = crud.check_for_match(db, user1_id=liker_id, user2_id=liked_user_id)

    if is_match:
        # Si es un match, crear la conexión
        connection = crud.create_connection(db, user1_id=liker_id, user2_id=liked_user_id)
        # Obtener el perfil del usuario con el que se hizo match para devolverlo
        match_profile = crud.get_user(db, user_id=liked_user_id)
        return schemas.LikeResponse(is_match=True, connection_id=connection.id, match_profile=match_profile)
    else:
        # Si no es match, simplemente confirmar la acción
        return schemas.LikeResponse(is_match=False)

# --- Endpoints de Inteligencia Artificial ---
@app.post("/api/ai/profile-assistant")
async def api_chat_with_profile_assistant(req: ProfileAssistantRequest):
    system_instruction = "Eres Vibrai Assist..." # (Contenido del prompt omitido por brevedad)
    model = get_ai_model(system_instruction=system_instruction)
    history = [{"role": c.role, "parts": [{"text": p.text} for p in c.parts]} for c in req.chat_history]
    history.append({"role": "user", "parts": [{"text": req.user_message}]})
    try:
        response = await model.generate_content_async(history, generation_config={"temperature": 0.4, "top_p": 0.95, "max_output_tokens": 500})
        # Lógica de parsing (omitida por brevedad)
        return {"responseText": "...", "generatedBio": "...", "isProfileComplete": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar respuesta del asistente: {e}")

@app.post("/api/ai/generate-interests", response_model=List[str])
async def api_generate_interests(req: GenerateInterestsRequest):
    prompt = f"De la siguiente biografía, extrae de 2 a 4 intereses... Biografía: \"{req.bio_text}\"..."
    model = get_ai_model()
    try:
        response = await model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
        parsed_json = parse_json_from_gemini(response.text)
        return parsed_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar intereses: {e}")

@app.post("/api/ai/suggest-icebreaker", response_model=str)
async def api_suggest_icebreaker(req: SuggestIcebreakerRequest):
    prompt = f"Genera un rompehielos para {req.user_name}..."
    model = get_ai_model()
    try:
        response = await model.generate_content_async(prompt, generation_config={"temperature": 0.85})
        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sugerir rompehielos: {e}")

@app.post("/api/ai/suggest-replies", response_model=List[str])
async def api_suggest_replies(req: SuggestRepliesRequest):
    prompt = f"Contexto: {req.chat_partner_name} dijo, \"{req.last_message_text}\". Tarea: 2 respuestas..."
    model = get_ai_model()
    try:
        response = await model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json", "temperature": 0.8})
        return parse_json_from_gemini(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sugerir respuestas: {e}")

@app.post("/api/ai/rewrite-message", response_model=str)
async def api_rewrite_message(req: RewriteMessageRequest):
    prompt = f"Reescribe este mensaje: \"{req.original_message}\" para que sea {req.rewrite_goal}..."
    model = get_ai_model()
    try:
        response = await model.generate_content_async(prompt, generation_config={"temperature": 0.85})
        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al reescribir el mensaje: {e}")

# --- Ejecución del Servidor ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)