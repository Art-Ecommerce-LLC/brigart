# app/models.py
from pydantic import BaseModel, EmailStr, Field, constr
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

class OrderContents(BaseModel):
    order_contents: Dict[str, Any]
    email: EmailStr = Field(...)
    
class OrderDetails(BaseModel):
    order_contents : Dict[str, Any]
    email: EmailStr = Field(...)
    
class OrderInfo(BaseModel):
    email: EmailStr = Field(...)
    phone: str = Field(..., min_length=10, max_length=15)
    cardName: str = Field(...)
    cardNumber: str = Field(..., min_length=15, max_length=16)
    expiryDate: str = Field(..., pattern=r'^\d{2}/\d{2}$')
    cvv: str = Field(..., min_length=3, max_length=4)
    fullname: str = Field(...)
    address1: str = Field(...)
    address2: str = Field(...)
    city: str = Field(...)
    state: str = Field(...)
    zip: str = Field(..., min_length=5, max_length=10)

class Credentials(BaseModel):
    username: str
    password: str

class Title(BaseModel):
    title: str


class ContactInfo(BaseModel):
    email: EmailStr = Field(...)
    phone: str = Field(..., min_length=10, max_length=15)

class PaymentInfo(BaseModel):
    cardName: str = Field(...)
    cardNumber: str = Field(..., min_length=15, max_length=16)
    expiryDate: str = Field(..., pattern=r'^\d{2}/\d{2}$')
    cvv: str = Field(..., min_length=3, max_length=4)

class BillingInfo(BaseModel):
    fullname: str = Field(...)
    address1: str = Field(...)
    address2: str = Field(...)
    city: str = Field(...)
    state: str = Field(...)
    zip: str = Field(..., min_length=5, max_length=10)

class Email(BaseModel):
    # Email can be nothing too
    email: EmailStr = Field(...)

class Confirmation(BaseModel):
    email: EmailStr = Field(...)
    line1: str = Field(...)
    line2: str = Field(...)
    city: str = Field(...)
    state: str = Field(...)
    postal_code: str = Field(...)
    country: str = Field(...)

class CheckoutInfo(BaseModel):
    email: EmailStr = Field(...)
    phone: str = Field(..., min_length=10, max_length=15)
    cardName: str = Field(...)
    cardNumber: str = Field(..., min_length=15, max_length=16)
    expiryDate: str = Field(..., pattern=r'^\d{2}/\d{2}$')
    cvv: str = Field(..., min_length=3, max_length=4)
    fullname: str = Field(...)
    address1: str = Field(...)
    address2: str = Field(...)
    city: str = Field(...)
    state: str = Field(...)
    zip: str = Field(..., min_length=5, max_length=10)
    shipFullname: str = Field(None)
    shipAddress1: str = Field(None)
    shipAddress2: str = Field(None)
    shipCity: str = Field(None)
    shipState: str = Field(None)
    shipZip: str = Field(None, min_length=5, max_length=10)

class TotalPrice(BaseModel):
    totalPrice: Union[int, str]

@dataclass()
class ShopObject:
    img: str
    title: str
    price: Union[int, str]
    logo : str

# Dataclass to turn list of strings into a list of objects
@dataclass(frozen=True)
class IconObject:
    icon_paths: List[str]
    titles: List[str]
    data_uris: List[str] = None

@dataclass(frozen=True)
class ArtObject:
    art_paths: List[str]
    titles: List[str]
    prices: List[Union[int, str]]
    Ids: List[int]
    data_uris: List[str] = None

@dataclass(frozen=True)
class KeyObject:
    envvars: List[str]
    envvals: List[str]

@dataclass(frozen=True)
class EmailObject:
    emails: List[str]

@dataclass(frozen=True)
class CookieObject:
    Id : List[int]
    sessionids: List[str]
    cookies: List[Dict[str, Any]]
    created_ats: List[str] 

@dataclass(frozen=True)
class OrderObject:
    order_numbers: List[str]
    emails : List[str]
    phones : List[str]


@dataclass(frozen=True)
class ContactObject:
    fullname: List[str]
    address1: List[str]
    address2: List[str]
    city: List[str]
    state: List[str]
    zip: List[str]
    order_number : List[str]

@dataclass(frozen=True)
class ContentObject:
    sessionids: List[str]
    payment_payloads: List[Dict[str, Any]]

@dataclass
class TableMap:
    img_table: str
    icon_table: str
    key_table: str
    email_table: str
    content_table: str
    contact_table: str
    order_table: str
    cookies_table: str
    paymentintent_table: str
    session_mapping_table: str
    final_order_table: str

@dataclass
class PaymentIntentObject:
    Ids : List[int]
    orderids: List[str]
    orderdetails: List[Dict[str, Any]]
    emails: List[str]
    amounts: List[Union[int, str]]
    intentids: List[str]

@dataclass
class SessionMapping:
    Ids: List[int]
    sessionids: List[str]
    orderids: List[Dict[str, Any]]

@dataclass
class FinalOrderObject:
    Ids: List[int]
    orderids: List[str]
    emails: List[str]
    amounts: List[Union[int, str]]
    intentids: List[str]

