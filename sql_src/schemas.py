from typing import Union
from pydantic import BaseModel, validator
from datetime import datetime
from typing import List, Union, Dict, Any
import json


# Assuming this is your utility function to evaluate strings
def evaluate_string_as_list(value: str) -> List[Dict[str, Union[str, int]]]:
    try:
        # Convert the string to a list of dictionaries
        return json.loads(value)
    except json.JSONDecodeError:
        raise ValueError("Invalid format for img. Expected a JSON string representing a list of dictionaries.")

class ArtworkBase(BaseModel):
    img_label: str
    img: Union[str, List[Dict[str, Union[str, int]]]]
    price: str
    created_at: datetime
    updated_at: datetime

    @validator('img', pre=True)
    def parse_img(cls, value: Union[str, List[Dict[str, Union[str, int]]]]) -> List[Dict[str, Union[str, int]]]:
        if isinstance(value, str):
            return evaluate_string_as_list(value)  # Parse JSON string into a list of dictionaries
        return value  # If already a list, just return it

    class Config:
        from_attributes = True 

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

