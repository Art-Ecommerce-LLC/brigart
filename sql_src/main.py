from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from . import crud, models, schemas
from .database import SessionLocal, engine
from .config import NOCODB_PATH, NOCODB_XC_TOKEN
import requests
import base64
from typing import List, Union
import time
import ast

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

def get_version():
    return str(int(time.time()))

@app.get("/redirectlogo")
def redirect_logo(db: Session = Depends(get_db)):
    try:
        icon = crud.get_icon_by_label(db, "brig_logo")
        data_uri = crud.convert_path_to_data_uri(icon.img)
        return {"data_uri": data_uri}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    try:
        artworks = crud.get_art_uris(db, 0, 100)
        art_table = crud.get_artworks(db, 0, 100)

        data_uris = []
        titles = []
        for i, art in enumerate(artworks):
            data_uris.append(art.data_uri)
            titles.append(art_table[i].img_label)

        icon = crud.get_icon_by_label(db, "brig_logo")
        img_path = ast.literal_eval(icon.img)[0]["path"]
        logo_uri = crud.convert_path_to_data_uri(img_path)

        

        context = {
            "art_uris": data_uris,
            "art_titles": titles,
            "brig_logo": logo_uri,
            "version": get_version()
        }

        return templates.TemplateResponse(request=request, name="index.html", context=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

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
