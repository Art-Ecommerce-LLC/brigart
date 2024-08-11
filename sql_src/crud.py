from sqlalchemy.orm import Session

from . import models, schemas
from typing import List, Union
# Get by ID or get all
import requests
import base64
from .config import NOCODB_PATH
import ast
from PIL import Image
from io import BytesIO


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



def convert_path_to_data_uri(img_path: str) -> str:
    url_path = f"{NOCODB_PATH}/{img_path}"
    img_data = requests.get(url_path).content
    data_uri = convert_to_data_uri(img_data)
    return data_uri

def convert_to_data_uri(image_data: bytes) -> str:
    """
        Convert image data to a data URI
        
        Arguments:
            image_data (bytes): The image data to convert
        
        Returns:
            str: The data URI of the image data
        
        Raises:
            Exception: If there is an error converting the image data to a data URI
    """
    try:
        with Image.open(BytesIO(image_data)) as img:
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            width, height = img.size
            new_size = (int(width * 0.7), int(height * 0.7))
            resized_img = img.resize(new_size, Image.ANTIALIAS)
            buffer = BytesIO()
            resized_img.save(buffer, format="JPEG")
            resized_img_data = buffer.getvalue()
        base64_data = base64.b64encode(resized_img_data).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_data}"
    except Exception as e:
        print(f"Error in convert_to_data_uri: {e}")

def get_artworks_with_uri(db: Session, skip: int = 0, limit: int = 100):
    try:
        artwork_payload = get_artworks(db, skip=skip, limit=limit)

        results = []
        for each in artwork_payload:
            img_path = ast.literal_eval(each.img)[0]["path"]
            img_uri = convert_path_to_data_uri(img_path)

            result = schemas.DisplayUris(
                Id=each.id,
                tableid=each.id,
                data_uri=img_uri
            )
            results.append(result)

        return results

    except Exception as e:
        print(f"Error in get_artworks_with_uri: {e}")
        return []




def get_art_uris(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.DisplayUris]:
    return db.query(models.DisplayUris).offset(skip).limit(limit).all()


def sync_art_and_display(db: Session):
    try:
        art_payload = get_artworks_with_uri(db)
        db.query(models.DisplayUris).delete()
        db.commit()
        db.bulk_save_objects(art_payload)
        db.commit()
    except Exception as e:
        print(f"Error in sync_art_and_display: {e}")