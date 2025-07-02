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
    version="1.8.0"
)

# --- Evento de Arranque ---
@app.on_event("startup")
def on_startup():
    print("Iniciando aplicación...")
    
    # Intenta crear las tablas. Si ya existen, no hace nada.
    # En un entorno de producción, se usarían migraciones (ej. Alembic).
    try:
        sql_models.Base.metadata.create_all(bind=engine)
        print("Tablas verificadas/creadas con éxito.")
    except Exception as e:
        print(f"Error al crear las tablas: {e}")
        # Considera detener la aplicación si la BD es crucial
        # raise e

    # Poblar la base de datos si está vacía
    db = SessionLocal()
    try:
        user_count = db.query(sql_models.User).count()
        if user_count == 0:
            print("Base de datos vacía. Poblando con datos de ejemplo...")
            # Datos de ejemplo mejorados con los nuevos campos
            users_data = [
                 {
                    "id": "currentUser", "name": "Alex", "age": 28, "bio": "Explorando cafés y senderos.",
                    "photos": ["https://picsum.photos/seed/alex1/400/600"], "primary_photo_url": "https://picsum.photos/seed/alex1/400/600",
                    "interests": ["Café", "Senderismo", "Hornear"], "occupation": "Ingeniero/a de Software", "country": "España",
                    "latitude": 40.416775, "longitude": -3.703790, "is_premium": False,
                    "gender_identities": ["No Binario"], "seeking_gender_identities": ["Todos"]
                },
                {
                    "id": "match1", "name": "Jaime", "age": 30, "bio": "Amante del arte y la música.",
                    "photos": ["https://picsum.photos/seed/jaime1/400/600"], "primary_photo_url": "https://picsum.photos/seed/jaime1/400/600",
                    "interests": ["Arte", "Música", "Cocina"], "occupation": "Diseñador/a Gráfico/a", "country": "España",
                    "latitude": 41.385063, "longitude": 2.173404, "is_premium": True,
                    "gender_identities": ["Masculino"], "seeking_gender_identities": ["Femenino", "No Binario"]
                },
                {
                    "id": "match2", "name": "Alexia", "age": 26, "bio": "Fan del cine y los juegos de mesa.",
                    "photos": ["https://picsum.photos/seed/alexia1/400/600"], "primary_photo_url": "https://picsum.photos/seed/alexia1/400/600",
                    "interests": ["Películas", "Juegos de Mesa", "Perros"], "occupation": "Especialista en Marketing", "country": "México",
                    "latitude": 19.432608, "longitude": -99.133209, "is_premium": False,
                    "gender_identities": ["Femenino"], "seeking_gender_identities": ["Masculino"]
                },
            ]
            for user_data in users_data:
                user = sql_models.User(**user_data)
                db.add(user)
            
            db.commit()
            print(f"Base de datos poblada con {len(users_data)} usuarios de prueba.")
        else:
            print(f"La base de datos ya contiene {user_count} usuarios.")
            
    finally:
        db.close()
    print("Preparación de la aplicación completa.")


# --- Middlewares ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, deberías restringir esto
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
    return {"message": "Bienvenido al backend de Vibrai"}

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