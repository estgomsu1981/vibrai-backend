# crud.py
from sqlalchemy.orm import Session
import sql_models

def get_user(db: Session, user_id: str):
    """
    Obtiene un único usuario por su ID desde la base de datos.
    Carga automáticamente sus logros y publicaciones de marketplace relacionadas.
    """
    return db.query(sql_models.User).filter(sql_models.User.id == user_id).first()

def get_all_users_except(db: Session, user_id_to_exclude: str, skip: int = 0, limit: int = 100):
    """
    Obtiene una lista de todos los usuarios excepto uno específico (el usuario actual).
    Se usa para poblar la lista de "matches".
    """
    return db.query(sql_models.User).filter(sql_models.User.id != user_id_to_exclude).offset(skip).limit(limit).all()