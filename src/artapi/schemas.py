from typing import Union
from pydantic import BaseModel
from datetime import datetime
from typing import List, Union, Dict, Any

class ArtworkBase(BaseModel):
    img_label: str
    img: str
    price: str
    uri: str = None
    height: str
    width: str
    sort_order: int = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ArtworkOrder(BaseModel):
    title: str
    sortOrder: int

class KeysBase(BaseModel):
    envvar: str
    envval: str
    created_at: datetime
    updated_at: datetime

class IconsBase(BaseModel):
    img_label: str
    img: str
    created_at: datetime
    updated_at: datetime

class CookiesBase(BaseModel):
    sessionids: str
    cookies: dict
    created_at: datetime
    updated_at: datetime