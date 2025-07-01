# main.py
import os
import re
import json
import uvicorn
from typing import List, Any, Optional

from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# --- Importaciones de Módulos Locales ---
import crud
import schemas
import sql_models 
from database import get_db, engine

# --- Creación de Tablas en la Base de Datos ---
# Esta línea creará las tablas definidas en sql_models.py si no existen.
# Es seguro ejecutarlo cada vez; no recreará tablas existentes.
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
    version="1.2.0"
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

@app.get("/api/profile", response_model=schemas.User)
def get_user_profile(db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id="currentUser")
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario 'currentUser' no encontrado en la base de datos.")
    return user

@app.get("/api/matches", response_model=List[schemas.User])
def get_matches(db: Session = Depends(get_db)):
    matches = crud.get_all_users_except(db, user_id_to_exclude="currentUser")
    return matches

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