import base64
import requests
from functools import lru_cache
from src.artapi.config import (
    NOCODB_XC_TOKEN, NOCODB_PATH, NOCODB_TABLE_MAP
)
from src.artapi.models import (
    ArtObject, IconObject, KeyObject, EmailObject, CookieObject, OrderObject, ContactObject, ContentObject
)
from src.artapi.logger import logger
from PIL import Image
from io import BytesIO
from typing import Union
import ast


class Noco:
    """
    Class to interact with NocoDB
    """
    
    # Store the previous state of the data
    previous_data = {
        "artwork": None,
        "icon": None,
        "key": None,
        "email": None,
        "cookie": None,
        "order": None,
        "contact": None,
        "content": None
    }

    @staticmethod
    def get_auth_headers() -> dict:
        """
        Function to return the headers for the request
        
        Returns:
            dict: The headers for the request
        """
        return {
            'xc-token': NOCODB_XC_TOKEN
        }

    @staticmethod
    def get_nocodb_path(table: str) -> str:
        """
        Function to return the path of a table in NocoDB

        Use same url for Get, Post, Patch, Delete operations
        
        Args:
            table (str): The table name
        Returns:
            str: The path of the table in NocoDB
        """
        return f"{NOCODB_PATH}/api/v2/tables/{table}/records"

    @staticmethod
    def get_nocodb_table_data(table: str) -> dict:
        """
        Function to get the data from a table in NocoDB
        
        Args:
            table (str): The table name

        Returns:
            dict: The response JSON
        """
        params = {
            "limit": 50
        }
        response = requests.get(Noco.get_nocodb_path(table), headers=Noco.get_auth_headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def post_nocodb_table_data(table: str, data: dict) -> None:
        """
        Function to post data to a table in NocoDB
        
        Args:
            table (str): The table name
            data (dict): The data to post
        """
        response = requests.post(Noco.get_nocodb_path(table), headers=Noco.get_auth_headers(), json=data)
        response.raise_for_status()

    @staticmethod
    def patch_nocodb_table_data(table: str, data: dict) -> None:
        """
        Function to patch data in a table in NocoDB
        
        Args:
            table (str): The table name
            data (dict): The data to patch
        """
        response = requests.patch(Noco.get_nocodb_path(table), headers=Noco.get_auth_headers(), json=data)
        response.raise_for_status()

    @staticmethod
    def data_has_changed(old_data: dict, new_data: dict) -> bool:
        """
        Function to check if the data has changed
        
        Args:
            old_data (dict): The old data
            new_data (dict): The new data
        Returns:
            bool: True if data has changed, False otherwise
        """
        return old_data != new_data

    @staticmethod
    def convert_paths_to_data_uris(paths: list) -> list:
        """
        Function to convert image paths to data URIs
        
        Args:
            paths (list): The list of image paths

        Returns:
            list: The list of data URIs
        """
        data_uris = []
        for path in paths:
            url_path = f"{NOCODB_PATH}/{path}"
            img_data = requests.get(url_path).content
            data_uri = Noco.convert_to_data_uri(img_data)
            data_uris.append(data_uri)

        return data_uris

    @staticmethod
    def convert_to_data_uri(image_data: bytes) -> str:
        """
        Function to convert image data to a data URI and reduce its resolution
        
        Args:
            image_data (bytes): The image data

        Returns:
            str: The data URI
        """
        with Image.open(BytesIO(image_data)) as img:
            if img.mode == 'RGBA':
                img = img.convert('RGB')  # Convert RGBA to RGB
            width, height = img.size
            new_size = (int(width * 0.4), int(height * 0.4))
            resized_img = img.resize(new_size, Image.ANTIALIAS)
            buffer = BytesIO()
            resized_img.save(buffer, format="JPEG")
            resized_img_data = buffer.getvalue()
        
        base64_data = base64.b64encode(resized_img_data).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_data}"

    @staticmethod
    @lru_cache(maxsize=128)
    def get_artwork_data() -> ArtObject:
        """
        Function to get the artwork data from NocoDB

        Returns:
            ArtObject: The artwork data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.img_table)
        art_paths = [item['img'][0]['signedPath'] for item in data['list']]
        data_uris = Noco.convert_paths_to_data_uris(art_paths)
        artwork_data = ArtObject(
            art_paths=art_paths,
            titles=[item['img_label'] for item in data['list']],
            prices=[item['price'] for item in data['list']],
            data_uris=data_uris
        )
        return artwork_data

    @staticmethod
    @lru_cache(maxsize=128)
    def get_icon_data() -> IconObject:
        """
        Function to get the icon data from NocoDB

        Returns:
            IconObject: The icon data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.icon_table)
        icon_paths = [item['img'][0]['signedPath'] for item in data['list']]
        data_uris = Noco.convert_paths_to_data_uris(icon_paths)
        icon_data = IconObject(
            icon_paths=icon_paths,
            titles=[item['img_label'] for item in data['list']],
            data_uris=data_uris
        )
        return icon_data

    @staticmethod
    @lru_cache(maxsize=128)
    def get_key_data() -> KeyObject:
        """
        Function to get the key data from NocoDB

        Returns:
            KeyObject: The key data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.key_table)
        key_data = KeyObject(
            envvars=[item['envvar'] for item in data['list']],
            envvals=[item['envval'] for item in data['list']]
        )
        return key_data

    @staticmethod
    @lru_cache(maxsize=128)
    def get_email_data() -> EmailObject:
        """
        Function to get the email data from NocoDB

        Returns:
            EmailObject: The email data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.email_table)
        email_data = EmailObject(
            emails=[item['email'] for item in data['list']]
        )
        return email_data

    @staticmethod
    @lru_cache(maxsize=128)
    def get_cookie_data() -> CookieObject:
        """
        Function to get the cookie data from NocoDB

        Returns:
            CookieObject: The cookie data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table)
        cookie_data = CookieObject(
            sessionids=[item['sessionid'] for item in data['list']],
            cookiesJson=[item['cookiesJson'] for item in data['list']],
            Id=[item['Id'] for item in data['list']]
        )
        return cookie_data
    
    @staticmethod
    def get_cookie_data_no_cache_no_object() -> list:
        """
        Function to get the cookie data from NocoDB without cache

        Returns:
            CookieObject: The cookie data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table)
        return data

    @staticmethod
    @lru_cache(maxsize=128)
    def get_order_data() -> OrderObject:
        """
        Function to get the order data from NocoDB

        Returns:
            OrderObject: The order data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.order_table)
        order_data = OrderObject(
            order_numbers=[item['order_number'] for item in data['list']],
            emails=[item['email'] for item in data['list']],
            phones=[item['phone'] for item in data['list']]
        )
        return order_data

    @staticmethod
    @lru_cache(maxsize=128)
    def get_contact_data() -> ContactObject:
        """
        Function to get the contact data from NocoDB

        Returns:
            ContactObject: The contact data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.contact_table)
        contact_data = ContactObject(
            fullname=[item['fullname'] for item in data['list']],
            address1=[item['address1'] for item in data['list']],
            address2=[item['address2'] for item in data['list']],
            city=[item['city'] for item in data['list']],
            state=[item['state'] for item in data['list']],
            zip=[item['zip'] for item in data['list']],
            order_number=[item['order_number'] for item in data['list']]
        )
        return contact_data
    
    @staticmethod
    @lru_cache(maxsize=128)
    def get_content_data() -> ContentObject:
        """
        Function to get the content data from NocoDB

        Returns:
            ContentObject: The content data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.content_table)
        content_data = ContentObject(
            order_number=[item['order_number'] for item in data['list']],
            order_content=[item['order_contents'] for item in data['list']]
        )
        return content_data
    
    @staticmethod
    def get_icon_uri_from_title(title: str) -> str:
        """
        Function to get the icon URI from the title
        
        Args:
            title (str): The title of the icon

        Returns:
            str: The URI of the icon
        """
        icon_data = Noco.get_icon_data()
        index = icon_data.titles.index(title)
        return icon_data.data_uris[index]
    
    @staticmethod
    def get_art_uri_from_title(title: str) -> str:
        """
        Function to get the artwork URI from the title
        
        Args:
            title (str): The title of the artwork

        Returns:
            str: The URI of the artwork
        """
        try:
            artwork_data = Noco.get_artwork_data()
            index = artwork_data.titles.index(title)
            return artwork_data.data_uris[index]
        except ValueError:
            return ""
    
    @staticmethod
    def get_art_price_from_title(title: str) -> str:
        """
        Function to get the price of the artwork from the title
        
        Args:
            title (str): The title of the artwork

        Returns:
            str: The price of the artwork
        """
        try:
            artwork_data = Noco.get_artwork_data()
            index = artwork_data.titles.index(title)
            return artwork_data.prices[index]
        except ValueError:
            return ""
    
    @staticmethod
    def get_art_price_from_title_and_quantity(title: str, quantity: int) -> str:
        """
        Function to get the price of an item from the title and quantity
        
        Args:
            title (str): The title of the item
            quantity (int): The quantity of the item

        Returns:
            int: The price of the item
        """
        price = Noco.get_art_price_from_title(title)
        return str(int(price) * quantity)
    
    @staticmethod
    def get_cookie_from_session_id(session_id: str) -> list:
        """
        Function to get the cookie from the session ID
        
        Args:
            session_id (str): The session ID

        Returns:
            list: The cookie
        """
        cookie_data = Noco.get_cookie_data()
        index = cookie_data.sessionids.index(session_id)
        img_quant_list = cookie_data.cookiesJson[index]['img_quantity_list']
        return img_quant_list

    @staticmethod
    def post_cookie_session_id_and_cookies(session_id: str, cookies: dict):
        """
        Function to post the session ID and cookies
        
        Args:
            session_id (str): The session ID
            cookies (str): The cookies
        """
        data = {
            "sessionid": session_id,
            "cookiesJson": cookies
        }
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)
    

    @staticmethod
    def patch_cookies_data(data: dict):
        """
        Function to patch the cookies data
        
        Args:
            data (dict): The data to patch
        """
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)

    @staticmethod
    def get_cookie_Id_from_session_id(session_id: str) -> str:
        """
        Function to get the ID of the session ID
        
        Args:
            session_id (str): The session ID

        Returns:
            str: The ID of the session ID
        """
        cookie_data = Noco.get_cookie_data()
        index = cookie_data.sessionids.index(session_id)
        return cookie_data.Id[index]
    
    @staticmethod
    def refresh_cookie_cache():
        """
        Function to refresh the cookie cache
        """
        Noco.get_cookie_data.cache_clear()