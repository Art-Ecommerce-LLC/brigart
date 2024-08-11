from typing import Union
from pydantic import BaseModel
from datetime import datetime
from typing import List, Union, Dict, Any

class ArtworkBase(BaseModel):
    img_label: str
    img: str
    price: str
    created_at: datetime
    updated_at: datetime

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