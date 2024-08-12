# app/models.py
from pydantic import BaseModel
from typing import List, Union, Dict, Any
from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Union

from .postgres import Base


class Artwork(Base):
    __tablename__ = "nc_ge1h___testimgs_copy"

    id = Column(Integer, primary_key=True)
    img_label = Column(String)
    img = Column(String)
    price = Column(String)
    created_at = Column(DateTime, default=datetime)
    updated_at = Column(DateTime, default=datetime, onupdate=datetime)

class Keys(Base):
    __tablename__ = "nc_3eh7___keys"

    id = Column(Integer, primary_key=True)
    envvar = Column(String)
    envval = Column(String)
    created_at = Column(DateTime, default=datetime)
    updated_at = Column(DateTime, default=datetime, onupdate=datetime)


class Icons(Base):
    __tablename__ = "nc_sxhc___icons"

    id = Column(Integer, primary_key=True)
    img_label = Column(String)
    img = Column(String)
    created_at = Column(DateTime, default=datetime)
    updated_at = Column(DateTime, default=datetime, onupdate=datetime)

class Cookies(Base):
    __tablename__ = "nc_qng4___sessions"

    id = Column(Integer, primary_key=True)
    sessionids = Column(String)
    cookies = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)

class TitleQuantity(BaseModel):
    quantity: Union[int, str]
    title: str

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
    created_ats: List[datetime] = None
    updated_ats: List[datetime] = None

@dataclass()
class ArtObject:
    Ids: List[int]
    art_paths: List[str] = None
    titles: List[str] = None
    prices: List[Union[int, str]] = None
    data_uris: List[str] = None
    created_ats: List[datetime] = None
    updated_ats: List[datetime] = None

@dataclass()
class KeyObject:
    envvars: List[str]
    envvals: List[str]

@dataclass()
class CookieObject:
    Id : List[int]
    sessionids: List[str]
    cookies: List[Dict[str, Any]]
    created_ats: List[datetime] = None

@dataclass()
class ProductMapObject:
    Id: List[int]
    noco_product_Ids: List[int] = None
    stripe_product_ids: List[str] = None
    created_ats: List[datetime] = None
    updated_ats: List[datetime] = None

@dataclass()
class ErrorObject:
    Id: List[int]
    error: List[dict] = None
    ticket_assignment: List[str] = None
    status: List[str] = None
    created_ats: List[datetime] = None
    updated_ats: List[datetime] = None
    
@dataclass
class TableMap:
    img_table: str
    icon_table: str
    key_table: str
    cookies_table: str
    error_table: str


