import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No se encontró la variable de entorno DATABASE_URL. Asegúrate de que está definida.")

# La clave para la estabilidad en Render:
# pool_pre_ping=True verifica que la conexión esté viva antes de usarla.
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    # Opcional: para logs de SQL, descomenta la siguiente línea
    # echo=True 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()