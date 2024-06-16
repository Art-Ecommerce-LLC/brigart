# app/models.py
from pydantic import BaseModel, EmailStr, Field, constr
from typing import List, Union

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
    email: EmailStr = Field(...)

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