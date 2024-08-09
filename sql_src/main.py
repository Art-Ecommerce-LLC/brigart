from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


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
    
@app.get("/artworks/", response_model=list[schemas.ArtworkBase])
def read_artworks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    artworks = crud.get_artworks(db, skip=skip, limit=limit)
    return artworks

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
