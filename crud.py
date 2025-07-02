from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, not_
import sql_models, schemas

def get_user(db: Session, user_id: str) -> sql_models.User | None:
    """
    Obtiene un usuario por su ID, cargando de forma eficiente sus logros
    y publicaciones del marketplace para evitar consultas N+1.
    """
    return db.query(sql_models.User).options(
        joinedload(sql_models.User.achievements),
        joinedload(sql_models.User.marketplace_listings)
    ).filter(sql_models.User.id == user_id).first()

def get_discovery_profiles(db: Session, user_id: str) -> list[sql_models.User]:
    """
    Obtiene perfiles para el feed de "Descubrir".
    Excluye al propio usuario y a aquellos con los que ya hay una conexión.
    """
    # IDs de usuarios con los que ya hay una conexión (liked, matched, blocked)
    connected_user_ids = db.query(sql_models.Connection.user_liked_id).filter(
        sql_models.Connection.user_liking_id == user_id
    )

    return db.query(sql_models.User).options(
        joinedload(sql_models.User.achievements),
        joinedload(sql_models.User.marketplace_listings)
    ).filter(
        sql_models.User.id != user_id,
        not_(sql_models.User.id.in_(connected_user_ids))
    ).order_by(sql_models.User.created_at.desc()).limit(20).all()

def get_connections_for_user(db: Session, user_id: str) -> list[sql_models.User]:
    """
    Obtiene las conexiones de un usuario (matches mutuos).
    """
    # IDs de usuarios con los que se ha hecho match
    matched_user_ids_query = db.query(sql_models.Connection.user_liked_id).filter(
        and_(
            sql_models.Connection.user_liking_id == user_id,
            sql_models.Connection.status == 'matched'
        )
    )
    
    # También se necesita la otra dirección del match
    user_has_liked_me_ids_query = db.query(sql_models.Connection.user_liking_id).filter(
        and_(
            sql_models.Connection.user_liked_id == user_id,
            sql_models.Connection.status == 'matched'
        )
    )

    all_matched_ids = [row[0] for row in matched_user_ids_query.all()] + \
                      [row[0] for row in user_has_liked_me_ids_query.all()]
    
    if not all_matched_ids:
        return []

    return db.query(sql_models.User).options(
        joinedload(sql_models.User.achievements),
        joinedload(sql_models.User.marketplace_listings)
    ).filter(sql_models.User.id.in_(all_matched_ids)).all()


def create_or_update_connection(db: Session, liker_id: str, liked_id: str) -> bool:
    """
    Crea o actualiza una conexión. Devuelve True si se produce un match.
    """
    # 1. Comprobar si el usuario que recibe el like ya había dado like antes.
    existing_like_from_other_user = db.query(sql_models.Connection).filter(
        and_(
            sql_models.Connection.user_liking_id == liked_id,
            sql_models.Connection.user_liked_id == liker_id
        )
    ).first()

    if existing_like_from_other_user:
        # ¡Es un match! Actualizamos la conexión existente a 'matched'.
        existing_like_from_other_user.status = 'matched'
        db.commit()
        
        # Opcional: Crear también la conexión en la otra dirección para consistencia
        reciprocal_connection = sql_models.Connection(
            user_liking_id=liker_id,
            user_liked_id=liked_id,
            status='matched'
        )
        db.add(reciprocal_connection)
        db.commit()
        return True
    else:
        # No hay match todavía. Creamos una nueva conexión con estado 'liked'.
        new_connection = sql_models.Connection(
            user_liking_id=liker_id,
            user_liked_id=liked_id,
            status='liked'
        )
        db.add(new_connection)
        db.commit()
        return False