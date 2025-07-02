import os
import uvicorn
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

import crud, schemas, sql_models
from database import SessionLocal, engine
from ai_router import router as ai_router

app = FastAPI(
    title="Vibrai Backend",
    description="API para la aplicación de citas Vibrai con integración de IA y base de datos.",
    version="2.0.0"
)

# --- Evento de Arranque ---
@app.on_event("startup")
def on_startup():
    print("Iniciando aplicación...")
    try:
        sql_models.Base.metadata.create_all(bind=engine)
        print("Tablas verificadas/creadas con éxito.")
    except Exception as e:
        print(f"Error crítico al crear las tablas: {e}")
        raise e

    db = SessionLocal()
    try:
        if db.query(sql_models.User).count() == 0:
            print("Base de datos vacía. Poblando con datos de ejemplo...")
            users_data = [
                {
                    "id": "currentUser", "name": "Alex", "age": 28, "bio": "Explorando cafés y senderos.",
                    "photos": ["https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=1887&auto=format&fit=crop"], 
                    "primary_photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=1887&auto=format&fit=crop",
                    "interests": ["Café", "Senderismo", "Hornear", "Viajar", "Música Indie"], 
                    "occupation": "Ingeniero de Software", "country": "España",
                    "latitude": 40.416775, "longitude": -3.703790, "is_premium": True,
                    "gender_identities": ["No Binario"], "seeking_gender_identities": ["Todos"],
                    "responsiveness_level": "high",
                },
                {
                    "id": "match1", "name": "Sofía", "age": 26, "bio": "Amante del arte, la música y los atardeceres en la playa.",
                    "photos": ["https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=1887&auto=format&fit=crop"], 
                    "primary_photo_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=1887&auto=format&fit=crop",
                    "interests": ["Arte", "Música", "Playa", "Yoga", "Cocina Vegana"], 
                    "occupation": "Diseñadora Gráfica", "country": "México",
                    "latitude": 19.432608, "longitude": -99.133209, "is_premium": False,
                    "gender_identities": ["Femenino"], "seeking_gender_identities": ["Masculino", "No Binario"],
                    "responsiveness_level": "medium",
                },
                {
                    "id": "match2", "name": "Carlos", "age": 32, "bio": "Entusiasta de la tecnología, el deporte y las buenas conversaciones.",
                    "photos": ["https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?q=80&w=1887&auto=format&fit=crop"], 
                    "primary_photo_url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?q=80&w=1887&auto=format&fit=crop",
                    "interests": ["Deporte", "Tecnología", "F1", "Cine de Ciencia Ficción"], 
                    "occupation": "Atleta", "country": "Colombia",
                    "latitude": 4.710989, "longitude": -74.072092, "is_premium": True,
                    "gender_identities": ["Masculino"], "seeking_gender_identities": ["Femenino"],
                    "responsiveness_level": "high",
                }
            ]
            for user_data in users_data:
                db.add(sql_models.User(**user_data))
            db.commit()
            print(f"Base de datos poblada con {len(users_data)} usuarios.")
    finally:
        db.close()
    print("Preparación de la aplicación completa.")


# --- Middlewares ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, deberías restringir esto a tu dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependencias ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Rutas de API Principales ---
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenido al backend de Vibrai v2.0.0"}

@app.get("/api/profile", response_model=schemas.User, tags=["Perfiles"])
def get_user_profile(db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id="currentUser")
    if not user:
        raise HTTPException(status_code=404, detail="Usuario 'currentUser' no encontrado.")
    return user

@app.get("/api/matches", response_model=List[schemas.User], tags=["Perfiles"])
def get_discovery_matches(db: Session = Depends(get_db)):
    return crud.get_discovery_profiles(db, user_id="currentUser")

@app.get("/api/connections", response_model=List[schemas.User], tags=["Conexiones"])
def get_user_connections(db: Session = Depends(get_db)):
    return crud.get_connections_for_user(db, user_id="currentUser")

@app.post("/api/like/{liked_user_id}", response_model=schemas.LikeResponse, tags=["Conexiones"])
def like_a_user(liked_user_id: str = Path(...), db: Session = Depends(get_db)):
    liker_id = "currentUser"
    if liker_id == liked_user_id:
        raise HTTPException(status_code=400, detail="No puedes darte 'me gusta' a ti mismo.")
    
    liked_user = crud.get_user(db, user_id=liked_user_id)
    if not liked_user:
        raise HTTPException(status_code=404, detail=f"El usuario con ID '{liked_user_id}' no fue encontrado.")

    is_match = crud.create_or_update_connection(db, liker_id=liker_id, liked_id=liked_user_id)

    if is_match:
        match_profile = crud.get_user(db, user_id=liked_user_id)
        return schemas.LikeResponse(is_match=True, match_profile=match_profile)
    else:
        return schemas.LikeResponse(is_match=False)

# --- Incluir el router de IA ---
app.include_router(ai_router)

# --- Ejecución para desarrollo local ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)