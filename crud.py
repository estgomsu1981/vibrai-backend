# crud.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
import sql_models
import schemas

def get_user(db: Session, user_id: str):
    """
    Obtiene un único usuario por su ID, cargando sus relaciones.
    """
    return db.query(sql_models.User).options(
        joinedload(sql_models.User.achievements),
        joinedload(sql_models.User.marketplace_listings)
    ).filter(sql_models.User.id == user_id).first()

def get_discovery_profiles(db: Session, user_id: str):
    """
    Obtiene perfiles para el "discovery feed".
    Excluye:
    - El propio usuario.
    - Usuarios a los que el usuario actual ya ha dado like.
    - Usuarios con los que el usuario actual ya tiene una conexión.
    """
    liked_user_ids = db.query(sql_models.Like.liked_id).filter(sql_models.Like.liker_id == user_id).subquery()
    
    connected_user_ids_1 = db.query(sql_models.Connection.user2_id).filter(sql_models.Connection.user1_id == user_id).subquery()
    connected_user_ids_2 = db.query(sql_models.Connection.user1_id).filter(sql_models.Connection.user2_id == user_id).subquery()

    return db.query(sql_models.User).filter(
        sql_models.User.id != user_id,
        sql_models.User.id.notin_(liked_user_ids),
        sql_models.User.id.notin_(connected_user_ids_1),
        sql_models.User.id.notin_(connected_user_ids_2)
    ).all()

def get_connections_for_user(db: Session, user_id: str):
    """
    Obtiene todos los perfiles con los que un usuario tiene una conexión.
    """
    connected_user_ids = db.query(sql_models.Connection.user1_id, sql_models.Connection.user2_id).filter(
        or_(sql_models.Connection.user1_id == user_id, sql_models.Connection.user2_id == user_id)
    ).all()
    
    # Flatten the list of tuples and remove the current user's ID
    all_ids = {uid for pair in connected_user_ids for uid in pair if uid != user_id}

    if not all_ids:
        return []

    return db.query(sql_models.User).filter(sql_models.User.id.in_(all_ids)).all()

def create_like(db: Session, liker_id: str, liked_id: str):
    """
    Crea un registro de 'like' en la base de datos.
    """
    # Evita likes duplicados
    existing_like = db.query(sql_models.Like).filter(
        sql_models.Like.liker_id == liker_id,
        sql_models.Like.liked_id == liked_id
    ).first()
    if existing_like:
        return existing_like

    db_like = sql_models.Like(liker_id=liker_id, liked_id=liked_id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like

def check_for_match(db: Session, user1_id: str, user2_id: str):
    """
    Verifica si existe un like mutuo (si user2_id ya ha dado like a user1_id).
    """
    return db.query(sql_models.Like).filter(
        sql_models.Like.liker_id == user2_id,
        sql_models.Like.liked_id == user1_id
    ).first()

def create_connection(db: Session, user1_id: str, user2_id: str):
    """
    Crea un registro de 'connection' si no existe ya.
    """
    # Evita conexiones duplicadas
    existing_connection = db.query(sql_models.Connection).filter(
        or_(
            and_(sql_models.Connection.user1_id == user1_id, sql_models.Connection.user2_id == user2_id),
            and_(sql_models.Connection.user1_id == user2_id, sql_models.Connection.user2_id == user1_id)
        )
    ).first()
    if existing_connection:
        return existing_connection

    db_connection = sql_models.Connection(user1_id=user1_id, user2_id=user2_id)
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection