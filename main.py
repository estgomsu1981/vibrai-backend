import os
import uvicorn
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

import crud, schemas, sql_models
from database import SessionLocal, engine

app = FastAPI(
    title="Vibrai Backend",
    description="API para la aplicación de citas Vibrai con integración de IA y base de datos.",
    version="1.7.0" # Versión con Reseteo en Cascada
)

@app.on_event("startup")
def on_startup():
    print("Iniciando aplicación. Forzando reseteo de la base de datos...")
    
    # --- RESETEA LA BASE DE DATOS EN CADA ARRANQUE (MÉTODO ROBUSTO) ---
    # Esto soluciona errores de dependencia al borrar tablas.
    with engine.connect() as connection:
        # Usamos una transacción para ejecutar estos comandos DDL.
        with connection.begin():
             connection.execute(text("DROP SCHEMA public CASCADE;"))
             connection.execute(text("CREATE SCHEMA public;"))
    print("Schema de la base de datos reseteado.")

    # Crear todas las tablas de nuevo en el schema limpio.
    sql_models.Base.metadata.create_all(bind=engine)
    print("Tablas creadas con éxito.")
    
    # Poblar la base de datos con datos de prueba.
    db = SessionLocal()
    try:
        print("Poblando la base de datos con datos de ejemplo...")
        users_data = [
            {
                "id": "currentUser", "name": "Alex", "age": 28, "bio": "Explorando cafés y senderos.",
                "photos": ["https://picsum.photos/seed/alex1/400/600"], "primary_photo_url": "https://picsum.photos/seed/alex1/400/600",
                "interests": ["Café", "Senderismo", "Hornear"], "occupation": "Ingeniero/a de Software", "country": "España",
                "latitude": 40.416775, "longitude": -3.703790
            },
            {
                "id": "match1", "name": "Jaime", "age": 30, "bio": "Amante del arte y la música.",
                "photos": ["https://picsum.photos/seed/jaime1/400/600"], "primary_photo_url": "https://picsum.photos/seed/jaime1/400/600",
                "interests": ["Arte", "Música", "Cocina"], "occupation": "Diseñador/a Gráfico/a", "country": "España",
                "latitude": 41.385063, "longitude": 2.173404
            },
            {
                "id": "match2", "name": "Alexia", "age": 26, "bio": "Fan del cine y los juegos de mesa.",
                "photos": ["https://picsum.photos/seed/alexia1/400/600"], "primary_photo_url": "https://picsum.photos/seed/alexia1/400/600",
                "interests": ["Películas", "Juegos de Mesa", "Perros"], "occupation": "Especialista en Marketing", "country": "México",
                "latitude": 19.432608, "longitude": -99.133209
            },
            {
                "id": "match3", "name": "Sofía", "age": 29, "bio": "Viajera, foodie y amante de los gatos.",
                "photos": ["https://picsum.photos/seed/sofia1/400/600"], "primary_photo_url": "https://picsum.photos/seed/sofia1/400/600",
                "interests": ["Viajar", "Gatos", "Comida"], "occupation": "Doctora", "country": "Argentina"
            },
            {
                "id": "match4", "name": "Carlos", "age": 32, "bio": "Atleta, desarrollador y entusiasta de la F1.",
                "photos": ["https://picsum.photos/seed/carlos1/400/600"], "primary_photo_url": "https://picsum.photos/seed/carlos1/400/600",
                "interests": ["Deporte", "Programación", "F1"], "occupation": "Atleta", "country": "Colombia"
            }
        ]
        
        for user_data in users_data:
            user = sql_models.User(**user_data)
            db.add(user)
        
        db.commit()
        print("Base de datos poblada con 5 usuarios de prueba.")
    finally:
        db.close()
    print("Preparación de la base de datos completa. La aplicación está lista.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root(): return {"message": "Bienvenido al backend de Vibrai"}

@app.get("/api/profile", response_model=schemas.User)
def get_user_profile(db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id="currentUser")
    if not user: raise HTTPException(status_code=404, detail="Usuario 'currentUser' no encontrado.")
    return user

@app.get("/api/matches", response_model=List[schemas.User])
def get_discovery_matches(db: Session = Depends(get_db)):
    return crud.get_discovery_profiles(db, user_id="currentUser")

@app.get("/api/connections", response_model=List[schemas.User])
def get_user_connections(db: Session = Depends(get_db)):
    return crud.get_connections_for_user(db, user_id="currentUser")

@app.post("/api/like/{liked_user_id}", response_model=schemas.LikeResponse)
def like_a_user(liked_user_id: str = Path(...), db: Session = Depends(get_db)):
    liker_id = "currentUser"
    if liker_id == liked_user_id: raise HTTPException(status_code=400, detail="No puedes darte 'me gusta' a ti mismo.")
    
    liked_user = crud.get_user(db, user_id=liked_user_id)
    if not liked_user:
        raise HTTPException(status_code=404, detail=f"El usuario con ID '{liked_user_id}' no fue encontrado.")

    is_match = crud.create_or_update_connection(db, liker_id=liker_id, liked_id=liked_user_id)

    if is_match:
        match_profile = crud.get_user(db, user_id=liked_user_id)
        return schemas.LikeResponse(is_match=True, match_profile=match_profile)
    else:
        return schemas.LikeResponse(is_match=False)

# (Los endpoints de IA no son necesarios para esta corrección)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)