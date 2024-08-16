from sqlalchemy.orm import Session
from . import models
import datetime as dt
from datetime import datetime

def get_artwork(db: Session, artwork_id: int):
    return db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

def get_artworks(db: Session, skip: int = 0, limit: int = 100):
    db.expire_all()
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

# Get by label, Use these filter functions instead of using indexing functions in Noco file
def get_icon_by_label(db: Session, img_label: str):
    return db.query(models.Icons).filter(models.Icons.img_label == img_label).first()

def get_artwork_by_label(db: Session, img_label: str):
    db.expire_all()
    return db.query(models.Artwork).filter(models.Artwork.img_label == img_label).first()

def get_cookie_by_sessionid(db: Session, sessionids: str):
    return db.query(models.Cookies).filter(models.Cookies.sessionids == sessionids).first()

def get_key_by_envvar(db: Session, envvar: str):
    return db.query(models.Keys).filter(models.Keys.envvar == envvar).first()


def create_cookie(db: Session, sessionids: str, cookies: dict):
    created_at = datetime.now(dt.timezone(dt.timedelta(hours=-8)))
    db_cookie = models.Cookies(sessionids=sessionids, cookies=cookies, created_at=created_at)
    try:
        db.add(db_cookie)
        db.commit()
        db.refresh(db_cookie)
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of an error
        print(f"Error creating cookie: {e}")
        raise  # Optionally re-raise the exception
    finally:
        db.close()  # Ensure the session is closed

def update_cookie(db: Session, cookie_id: int, sessionids: str, cookies: dict):
    updated_at = datetime.now(dt.timezone(dt.timedelta(hours=-8)))
    try:
        db_cookie = db.query(models.Cookies).filter(models.Cookies.id == cookie_id).first()
        if db_cookie:
            db_cookie.sessionids = sessionids
            db_cookie.cookies = cookies
            db_cookie.updated_at = updated_at
            db.commit()
            db.refresh(db_cookie)
        else:
            print("Cookie not found")
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of an error
        print(f"Error updating cookie: {e}")
        raise  # Optionally re-raise the exception
    finally:
        db.close()  # Ensure the session is closed

def delete_cookie_from_sessionid(db: Session, sessionids: str):
    try:
        db.query(models.Cookies).filter(models.Cookies.sessionids == sessionids).delete()
        db.commit()
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of an error
        print(f"Error deleting cookie: {e}")
        raise  # Optionally re-raise the exception
    finally:
        db.close()  # Ensure the session is closed
