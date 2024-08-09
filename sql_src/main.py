from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from . import crud, models, schemas
from .database import SessionLocal, engine
from .config import NOCODB_PATH
import requests
import base64
from typing import List, Union

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Get path of where the file is running
script_path = os.path.abspath(__file__)

# Get the directory where the script is located
script_dir = os.path.dirname(script_path)

# Static files and templates
static_dir = os.path.join(script_dir, "static")
templates_dir = os.path.join(script_dir, "templates")


# Static files and templates
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/artwork/{artwork_id}", response_model=schemas.ArtworkBase)
def read_artwork(artwork_id: int, db: Session = Depends(get_db)):
    try:
        db_artwork = crud.get_artwork(db, artwork_id)
        if db_artwork is None:
            raise HTTPException(status_code=404, detail="Artwork not found")
        return db_artwork
    except Exception as e:
        print(e)
        return {"error": "An error occurred"}
    
def convert_image_to_data_uri(image_path: str) -> str:
    # Fetch the image from NocoDB or file system
    response = requests.get(image_path)
    if response.status_code == 200:
        # Encode the image to Base64 and create a Data URI
        image_data = base64.b64encode(response.content).decode('utf-8')
        mime_type = response.headers.get('Content-Type', 'image/jpeg')  # Adjust according to your needs
        return f"data:{mime_type};base64,{image_data}"
    else:
        raise ValueError("Unable to fetch image from path")


@app.get("/artworks/", response_model=List[Union[schemas.ArtworkBase, models.ArtUriObject]])
def read_artworks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Retrieve artworks from the database
    try:
        artwork_payload = crud.get_artworks(db, skip=skip, limit=limit)

        # # Convert the image paths to Data URIs
        art_uri_object = [ 
            models.ArtUriObject(
                Id=artwork.id,
                ImgLabel=artwork.img_label,
                ArtUri=convert_image_to_data_uri(artwork.img[0]["path"]),
                Price=artwork.price,
                CreatedAt=artwork.created_at,
                UpdatedAt=artwork.updated_at
            ) for artwork in artwork_payload
        ]
        return art_uri_object
    
    except Exception as e:
        print(e)
        return {"error": "An error occurred"}
@app.get("/keys/{key_id}", response_model=schemas.KeysBase)
def read_key(key_id: int, db: Session = Depends(get_db)):
    db_key = crud.get_key(db, key_id)
    if db_key is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return db_key

@app.get("/keys/", response_model=list[schemas.KeysBase])
def read_keys(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    keys = crud.get_keys(db, skip=skip, limit=limit)
    return keys

@app.get("/icons/{icon_id}", response_model=schemas.IconsBase)
def read_icon(icon_id: int, db: Session = Depends(get_db)):
    db_icon = crud.get_icon(db, icon_id)
    if db_icon is None:
        raise HTTPException(status_code=404, detail="Icon not found")
    return db_icon

@app.get("/icons/", response_model=list[schemas.IconsBase])
def read_icons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    icons = crud.get_icons(db, skip=skip, limit=limit)
    return icons

@app.get("/cookies/{cookie_id}", response_model=schemas.CookiesBase)
def read_cookie(cookie_id: int, db: Session = Depends(get_db)):
    db_cookie = crud.get_cookie(db, cookie_id)
    if db_cookie is None:
        raise HTTPException(status_code=404, detail="Cookie not found")
    return db_cookie

@app.get("/cookies/", response_model=list[schemas.CookiesBase])
def read_cookies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cookies = crud.get_cookies(db, skip=skip, limit=limit)
    return cookies


# @app.get("/", response_class=HTMLResponse)
# async def homepage(request: Request, db: Session = Depends(get_db)):
#     try:
#         context = {
#             "art_uris": crud.get_artwork_data_with_cache(db).data_uris,
#             "art_titles": crud.get_artwork_data_with_cache(db).titles,
#             "brig_logo": crud.get_icon_uri_from_title(db, "brig_logo"),
#             "version": crud.get_version(db)
#         }
#         return templates.TemplateResponse(request=request, name="index.html", context=context)
#     except Exception as e:
#         print(f"Error in homepage: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
