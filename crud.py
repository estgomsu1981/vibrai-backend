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
    part1 = db.query(sql_models.Connection.user_liked_id).filter(
        sql_models.Connection.user_liking_id == user_id,
        sql_models.Connection.status == 'matched'
    )
    part2 = db.query(sql_models.Connection.user_liking_id).filter(
        sql_models.Connection.user_liked_id == user_id,
        sql_models.Connection.status == 'matched'
    )
    all_matched_ids = [r.user_liked_id for r in part1] + [r.user_liking_id for r in part2]
    
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
    existing_like = db.query(sql_models.Connection).filter(
        sql_models.Connection.user_liking_id == liked_id,
        sql_models.Connection.user_liked_id == liker_id
    ).first()

    if existing_like:
        existing_like.status = 'matched'
        
        # Opcional: crea la conexión en la otra dirección para consistencia
        # y para facilitar las consultas de 'mis conexiones'.
        reciprocal_conn = db.query(sql_models.Connection).filter(
             sql_models.Connection.user_liking_id == liker_id,
             sql_models.Connection.user_liked_id == liked_id
        ).first()
        if not reciprocal_conn:
            db.add(sql_models.Connection(user_liking_id=liker_id, user_liked_id=liked_id, status='matched'))
        else:
            reciprocal_conn.status = 'matched'
            
        db.commit()
        return True
    else:
        new_connection = sql_models.Connection(user_liking_id=liker_id, user_liked_id=liked_id, status='liked')
        db.add(new_connection)
        db.commit()
        return False