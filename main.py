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
# Esta línea creará las tablas definidas en sql_models.py si no existen.
sql_models.Base.metadata.create_all(bind=engine)

# --- Configuración de la API de Gemini (omitida por brevedad) ---
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("API_KEY")
    if not GEMINI_API_KEY:
        genai = None
    else:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    genai = None

# --- Modelos Pydantic para IA (omitidos por brevedad) ---
class ProfileAssistantRequest(BaseModel): user_message: str; chat_history: List[Any]
class GenerateInterestsRequest(BaseModel): bio_text: str
class SuggestIcebreakerRequest(BaseModel): user_name: str; user_interests: Optional[List[str]]; attempt_number: int
class SuggestRepliesRequest(BaseModel): last_message_text: str; own_name: str; chat_partner_name: str
class RewriteMessageRequest(BaseModel): original_message: str; rewrite_goal: str

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

# --- Endpoints de la API ---
@app.get("/")
def read_root():
    return {"message": "Bienvenido al backend de Vibrai"}

# --- Endpoints de Datos (Conectados a la Base de Datos) ---

@app.get("/api/profile", response_model=schemas.User)
def get_user_profile(db: Session = Depends(get_db)):
    user_id = "currentUser"
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario '{user_id}' no encontrado.")
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
    
    if liker_id == liked_user_id:
        raise HTTPException(status_code=400, detail="No puedes darte 'me gusta' a ti mismo.")

    crud.create_like(db, liker_id=liker_id, liked_id=liked_user_id)

    is_match = crud.check_for_match(db, user1_id=liker_id, user2_id=liked_user_id)

    if is_match:
        connection = crud.create_connection(db, user1_id=liker_id, user2_id=liked_user_id)
        match_profile = crud.get_user(db, user_id=liked_user_id)
        return schemas.LikeResponse(is_match=True, connection_id=connection.id, match_profile=match_profile)
    else:
        return schemas.LikeResponse(is_match=False)

# --- Endpoints de IA (omitidos por brevedad) ---

# --- Ejecución del Servidor ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)