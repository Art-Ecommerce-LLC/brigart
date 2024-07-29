# app/models.py
from pydantic import BaseModel
from typing import List, Union, Dict, Any
from dataclasses import dataclass

class Url(BaseModel):
    url: str
    title1: str

class UrlQuantity(BaseModel):
    url: str
    quantity: Union[int, str]
    title2: str

class TitleQuantity(BaseModel):
    quantity: Union[int, str]
    title: str


class Credentials(BaseModel):
    username: str
    password: str

class Title(BaseModel):
    title: str

class TotalPrice(BaseModel):
    totalPrice: Union[int, str]

@dataclass()
class ShopObject:
    img: str
    title: str
    price: Union[int, str]
    logo : str

# Dataclass to turn list of strings into a list of objects
@dataclass()
class IconObject:
    Ids: List[int]
    icon_paths: List[str] = None
    titles: List[str] = None
    data_uris: List[str] = None
    created_ats: List[str] = None
    updated_ats: List[str] = None

@dataclass()
class ArtObject:
    Ids: List[int]
    art_paths: List[str] = None
    titles: List[str] = None
    prices: List[Union[int, str]] = None
    data_uris: List[str] = None
    created_ats: List[str] = None
    updated_ats: List[str] = None

@dataclass()
class KeyObject:
    envvars: List[str]
    envvals: List[str]

@dataclass()
class CookieObject:
    Id : List[int]
    sessionids: List[str]
    cookies: List[Dict[str, Any]]
    created_ats: List[str] = None

@dataclass()
class ProductMapObject:
    Id: List[int]
    noco_product_Ids: List[int] = None
    stripe_product_ids: List[str] = None
    created_ats: List[str] = None
    updated_ats: List[str] = None

@dataclass
class TableMap:
    img_table: str
    icon_table: str
    key_table: str
    cookies_table: str
    product_map_table: str
