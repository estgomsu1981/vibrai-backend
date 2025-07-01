from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, not_
import sql_models

def get_user(db: Session, user_id: str):
    return db.query(sql_models.User).options(
        joinedload(sql_models.User.achievements),
        joinedload(sql_models.User.marketplace_listings)
    ).filter(sql_models.User.id == user_id).first()

def get_discovery_profiles(db: Session, user_id: str):
    """
    Obtiene perfiles con los que el usuario actual no ha interactuado.
    """
    # IDs de usuarios con los que el usuario actual ya ha interactuado
    interacted_user_ids = db.query(sql_models.Connection.user_liked_id).filter(sql_models.Connection.user_liking_id == user_id)

    return db.query(sql_models.User).filter(
        sql_models.User.id != user_id,
        not_(sql_models.User.id.in_(interacted_user_ids))
    ).all()

def get_connections_for_user(db: Session, user_id: str):
    """
    Obtiene todos los perfiles con los que un usuario tiene un 'match'.
    """
    # Encuentra conexiones donde el estado es 'matched'
    matched_connections = db.query(sql_models.Connection).filter(
        and_(
            or_(sql_models.Connection.user_liking_id == user_id, sql_models.Connection.user_liked_id == user_id),
            sql_models.Connection.status == 'matched'
        )
    ).all()
    
    # Extrae los IDs de los otros usuarios en esas conexiones
    all_ids = {c.user_liking_id if c.user_liked_id == user_id else c.user_liked_id for c in matched_connections}

    if not all_ids:
        return []

    return db.query(sql_models.User).filter(sql_models.User.id.in_(all_ids)).all()

def create_or_update_connection(db: Session, liker_id: str, liked_id: str):
    """
    Registra un 'like' y comprueba si resulta en un 'match'.
    """
    # El usuario da like: crea o actualiza la acción con 'liked'
    my_like = sql_models.Connection(user_liking_id=liker_id, user_liked_id=liked_id, status='liked')
    db.merge(my_like)

    # Comprueba si el otro usuario ya había dado like
    other_like = db.query(sql_models.Connection).filter(
        sql_models.Connection.user_liking_id == liked_id,
        sql_models.Connection.user_liked_id == liker_id
    ).first()

    if other_like:
        # ¡Es un match! Actualiza ambas filas a 'matched'
        other_like.status = 'matched'
        my_like.status = 'matched' # Actualiza el objeto que estamos a punto de hacer merge
        db.merge(other_like)
        db.merge(my_like)
        db.commit()
        return True # Indica que es un match
    
    db.commit()
    return False # No es un match (todavía)