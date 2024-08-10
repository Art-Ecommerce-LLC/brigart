from typing import Union
from pydantic import BaseModel, validator
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

class TitleQuantity(BaseModel):
    quantity: Union[int, str]
    title: str

class Title(BaseModel):
    title: str

class TotalPrice(BaseModel):
    totalPrice: Union[int, str]

class ImageData(BaseModel):
    img: str
    title: str
    price: Union[int, str]
    logo: str

class DisplayUris(BaseModel):
    Id: int
    tableid: int
    data_uri: str

