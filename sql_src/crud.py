from sqlalchemy.orm import Session

from . import models, schemas

# Get by ID or get all

def get_artwork(db: Session, artwork_id: int):
    return db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

def get_artworks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Artwork).offset(skip).limit(limit).all()

def get_key(db: Session, key_id: int):
    return db.query(models.Keys).filter(models.Keys.id == key_id).first()

def get_keys(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Keys).offset(skip).limit(limit).all()

def get_icon(db: Session, icon_id: int):
    return db.query(models.Icons).filter(models.Icons.id == icon_id).first()

def get_icons(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Icons).offset(skip).limit(limit).all()

def get_cookie(db: Session, cookie_id: int):
    return db.query(models.Cookies).filter(models.Cookies.id == cookie_id).first()

def get_cookies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cookies).offset(skip).limit(limit).all()

# Get by label
def get_icon_by_label(db: Session, img_label: str):
    return db.query(models.Icons).filter(models.Icons.img_label == img_label).first()

def get_artwork_by_label(db: Session, img_label: str):
    return db.query(models.Artwork).filter(models.Artwork.img_label == img_label).first()

def get_cookie_by_sessionid(db: Session, sessionids: str):
    return db.query(models.Cookies).filter(models.Cookies.sessionids == sessionids).first()

def get_key_by_envvar(db: Session, envvar: str):
    return db.query(models.Keys).filter(models.Keys.envvar == envvar).first()





