import base64
import requests
from functools import lru_cache
from src.artapi.config import (
    NOCODB_XC_TOKEN, NOCODB_PATH, NOCODB_TABLE_MAP
)
from src.artapi.models import (
    ArtObject, IconObject, KeyObject, EmailObject, CookieObject, OrderObject, ContactObject, ContentObject, PaymentIntentObject,
    SessionMapping
)
from src.artapi.logger import logger
from PIL import Image
from io import BytesIO
from typing import Union
import uuid

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
        "content": None,
        "paymentintent": None,
        "session_mapping": None,
        "finalpayment" : None,

    }

    def get_auth_headers() -> dict:
        """
        Function to return the headers for the request
        
        Returns:
            dict: The headers for the request
        """
        return {
            'xc-token': NOCODB_XC_TOKEN
        }
    
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

    def get_storage_upload_path() -> str:
        """
        Function to get the upload path
        
        Returns:
            str: The upload path
        """
        return f"{NOCODB_PATH}/api/v2/storage/upload"
    
    
    def get_nocodb_table_data(table: str) -> dict:
        """
        Function to get the data from a table in NocoDB
        
        Args:
            table (str): The table name

        Returns:
            dict: The response JSON
        """
        params = {
            "limit": 200
        }
        response = requests.get(Noco.get_nocodb_path(table), headers=Noco.get_auth_headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def delete_nocodb_table_data(table: str, Id: int) -> None:
        """
        Function to delete data from a table in NocoDB
        
        Args:
            table (str): The table name
            Id (int): The ID of the data to delete
        """
        body = {
            "Id": Id
        }
        response = requests.delete(f"{Noco.get_nocodb_path(table)}", headers=Noco.get_auth_headers(), json=body)
        response.raise_for_status
    
    def post_nocodb_table_data(table: str, data: dict) -> None:
        """
        Function to post data to a table in NocoDB
        
        Args:
            table (str): The table name
            data (dict): The data to post
        """
        response = requests.post(Noco.get_nocodb_path(table), headers=Noco.get_auth_headers(), json=data)
        response.raise_for_status()

    def patch_nocodb_table_data(table: str, data: dict) -> None:
        """
        Function to patch data in a table in NocoDB
        
        Args:
            table (str): The table name
            data (dict): The data to patch
        """
        response = requests.patch(Noco.get_nocodb_path(table), headers=Noco.get_auth_headers(), json=data)
        response.raise_for_status()

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
            data_uris=data_uris,
            Ids=[item['Id'] for item in data['list']]
        )
        return artwork_data
        
    def get_payment_intent_data() -> PaymentIntentObject:
        """
        Function to get the payment intent data from NocoDB

        Returns:
            PaymentIntentObject: The payment intent data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.paymentintent_table)
        payment_intent_data = PaymentIntentObject(
            Ids=[item['Id'] for item in data['list']],
            orderids=[item['orderids'] for item in data['list']],
            orderdetails=[item['orderdetails'] for item in data['list']],
            emails=[item['emails'] for item in data['list']],
            amounts=[item['amounts'] for item in data['list']],
            intentids = [item['intentids'] for item in data['list']]
        )
        return payment_intent_data
    
    def post_final_order_data(orderid:str, orderdetail: dict, email: str, amount: str, intentid: str) -> None:
        """
        Function to post the final order data
        
        Args:
            orderid (str): The order ID
            orderdetail (dict): The order detail
            email (str): The email
            amount (str): The amount
            intentid (str): The intent ID
        """
        data = {
            "orderids": orderid,
            "orderdetails": orderdetail,
            "emails": email,
            "amounts": amount,
            "intentids": intentid
        }
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.final_order_table, data)

    def get_session_mapping_data() -> SessionMapping:
        """
        Function to get the session mapping data from NocoDB

        Returns:
            SessionMapping: The session mapping data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.session_mapping_table)
        session_mapping_data = SessionMapping(
            Ids = [item['Id'] for item in data['list']],
            sessionids=[item['sessionids'] for item in data['list']],
            orderids=[item['orderids'] for item in data['list']],
        )
        return session_mapping_data
    
    def post_session_mapping_data(sessionid: str, orderid: str) -> None:
        """
        Function to post the session mapping data
        
        Args:
            sessionid (str): The session ID
            orderid (str): The order ID
        """
        data = {
            "sessionids": sessionid,
            "orderids": orderid
        }
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.session_mapping_table, data)
    
    def get_session_mapping_Id_from_sessionid(sessionid: str) -> int:
        """
        Function to get the session mapping ID from the session ID
        
        Args:
            sessionid (str): The session ID

        Returns:
            int: The session mapping ID
        """
        session_mapping_data = Noco.get_session_mapping_data()
        index = session_mapping_data.sessionids.index(sessionid)
        return session_mapping_data.Ids[index]

    def wipe_session_data_from_sessionid(sessionid: str) -> None:
        """
        Function to wipe the session data from the session ID
        
        Args:
            sessionid (str): The session ID
        """
        session_mapping_data = Noco.get_session_mapping_data()
        index = session_mapping_data.sessionids.index(sessionid)
        Noco.delete_nocodb_table_data(NOCODB_TABLE_MAP.paymentintent_table, Noco.get_payment_intent_Id_from_orderid(Noco.get_orderid_from_sessionid(sessionid)))
        Noco.delete_nocodb_table_data(NOCODB_TABLE_MAP.session_mapping_table, session_mapping_data.Ids[index])
        Noco.delete_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, Noco.get_cookie_Id_from_session_id(sessionid))
    
    def get_payment_intent_from_orderid(orderid: str) -> dict:
        """
        Function to get the payment intent row from the order ID
        
        Args:
            orderid (str): The order ID

        Returns:
            dict: The payment intent row
        """
        payment_intent_data = Noco.get_payment_intent_data()
        index = payment_intent_data.orderids.index(orderid)
        return {
            "Id": payment_intent_data.Ids[index],
            "orderid": payment_intent_data.orderids[index],
            "orderdetail": payment_intent_data.orderdetails[index],
            "email": payment_intent_data.emails[index],
            "amount": payment_intent_data.amounts[index],
            "intentid": payment_intent_data.intentids[index]
        }

    
    def patch_session_mapping_data(sessionid: str, orderid: str, intentid: str, ordercontent: dict) -> None:
        """
        Function to patch the session mapping data
        
        Args:
            sessionid (str): The session ID
            orderid (str): The order ID
        """
        data = {
            "Id": Noco.get_session_mapping_Id_from_sessionid(sessionid),
            "sessionid": sessionid,
            "orderid": orderid,
            "intentid": intentid,
            "ordercontent": ordercontent
        }
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.session_mapping_table, data)

    def patch_email_to_payment_intent(sessionid: str, email: str) -> None:
        """
        Function to patch the email to the payment intent. Index for payment intent data is found by getting the orderid of the index of the sessionid in the session mapping data and then indexing that orderid to the payment intent data

        Args:
            sessionid (str): The session ID
            email (str): The email

        Returns:
            str: The payment intent ID
        """
        session_mapping_data = Noco.get_session_mapping_data()
        index = session_mapping_data.sessionids.index(sessionid)
        order_id = session_mapping_data.orderids[index]
        payment_intent_data = Noco.get_payment_intent_data()
        index = payment_intent_data.orderids.index(order_id)
        data = {
            "Id": payment_intent_data.Ids[index],
            "orderids": payment_intent_data.orderids[index],
            "orderdetails": payment_intent_data.orderdetails[index],
            "emails": email,
            "amounts": payment_intent_data.amounts[index],
            "intentids": payment_intent_data.intentids[index]
        }
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.paymentintent_table, data)

    def patch_payment_intent_data(orderid: str, orderdetail : dict, email : str, amount : Union[str,int], intentid: Union[str,int]) -> None:
        """
        Function to patch the payment intent data
        
        Args:
            sessionid (str): The session ID
            orderid (str): The order ID
            orderdetail (dict): The order detail
            email (str): The email
            amount (str): The amount
            intentid (str): The intent ID
        """
        data = {
            "Id": Noco.get_payment_intent_Id_from_orderid(orderid),
            "orderids": orderid,
            "orderdetails": orderdetail,
            "emails": email,
            "amounts": amount,
            "intentids": intentid
        }
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.paymentintent_table, data)

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

    def get_cookie_data() -> CookieObject:
        """
        Function to get the cookie data from NocoDB

        Returns:
            CookieObject: The cookie data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table)
        cookie_data = CookieObject(
            Id=[item['Id'] for item in data['list']],
            sessionids=[item['sessionids'] for item in data['list']],
            cookies=[item['cookies'] for item in data['list']],
            created_ats=[item['CreatedAt'] for item in data['list']]
        )
        return cookie_data
    
    def get_cookie_data_no_cache_no_object() -> list:
        """
        Function to get the cookie data from NocoDB without cache

        Returns:
            CookieObject: The cookie data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table)
        return data

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
    
    @lru_cache(maxsize=128)
    def get_content_data() -> ContentObject:
        """
        Function to get the content data from NocoDB

        Returns:
            ContentObject: The content data
        """
        data = Noco.get_nocodb_table_data(NOCODB_TABLE_MAP.content_table)
        content_data = ContentObject(
            sessionids=[item['sessionid'] for item in data['list']],
            payment_payloads=[item['payment_payload'] for item in data['list']]
        )
        return content_data
    
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
            logger.error(f"Artwork with title {title} not found")
            return ""
    
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
            logger.error(f"Artwork with title {title} not found")
            raise ValueError(f"Artwork with title {title} not found")
    
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
    
    def get_full_cookie_from_session_id(session_id: str) -> dict:
        """
        Function to get the full cookie from the session ID
        
        Args:
            session_id (str): The session ID

        Returns:
            dict: The full cookie
        """
        cookie_data = Noco.get_cookie_data()
        index = cookie_data.sessionids.index(session_id)
        return cookie_data.cookies[index]
    


    def get_email_from_session_id(session_id: str) -> str:
        """
        Function to get the email from the session ID, order id is at the same index as session id in the session mapping table and that same order id has the same index as the email in tehe [payment intent table]
        
        Args:
            session_id (str): The session ID

        Returns:
            str: The email
        """
        try:
            session_mapping_data = Noco.get_session_mapping_data()
            index = session_mapping_data.sessionids.index(session_id)
            order_id = session_mapping_data.orderids[index]
            payment_intent_data = Noco.get_payment_intent_data()
            index = payment_intent_data.orderids.index(order_id)
            return payment_intent_data.emails[index]
        except ValueError:
            logger.error(f"Session ID {session_id} not found in session mapping data")
            return ""

    def get_cookie_from_session_id(session_id: str) -> list:
        """
        Function to get the cookie from the session ID
        
        Args:
            session_id (str): The session ID

        Returns:
            list: The cookie
        """
        try:
            cookie_data = Noco.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            img_quant_list = cookie_data.cookies[index]["img_quantity_list"]
            return img_quant_list
        except ValueError:
            logger.error(f"Session ID {session_id} not found")
            return []
        # If the session ID is not found, return an empty list

    def delete_session_cookie(session_id: str) -> None:
        """
        Function to delete the session cookie
        
        Args:
            session_id (str): The session ID
        """
        cookie_data = Noco.get_cookie_data()
        index = cookie_data.sessionids.index(session_id)
        Noco.delete_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, cookie_data.Id[index])
    
    def get_order_cookie_from_session_id(session_id: str) -> dict:
        """
        Function to get the order cookie from the session ID
        
        Args:
            session_id (str): The session ID

        Returns:
            dict: The order cookie
        """
        cookie_data = Noco.get_cookie_data()
        index = cookie_data.sessionids.index(session_id)
        order_cookie = cookie_data.cookiesJson[index]['billing_info']
        return order_cookie
    
    def get_contact_cookie_from_session_id(session_id: str) -> dict:
        """
        Function to get the contact cookie from the session ID
        
        Args:
            session_id (str): The session ID

        Returns:
            dict: The contact cookie
        """

        cookie_data = Noco.get_cookie_data()
        index = cookie_data.sessionids.index(session_id)
        contact_cookie = cookie_data.cookiesJson[index]['contact_info']
        return contact_cookie
    
    def patch_order_cookie(session_id: str, cookiesJson: dict, Id: int) -> None:
        """
        Function to post the order cookie
        
        Args:
            session_id (str): The session ID
            order_cookie (dict): The order cookie
        """

        data = {
            "Id": Noco.get_cookie_Id_from_session_id(session_id),
            "sessionid": session_id,
            "cookiesJson": cookiesJson
        }
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)

    def post_cookie_session_id_and_cookies(sessionid: str, cookies: dict):
        """
        Function to post the session ID and cookies
        
        Args:
            session_id (str): The session ID
            cookies (str): The cookies
        """
        data = {
            "sessionids": sessionid,
            "cookies": cookies
        }
        try:
            Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)
        except Exception as e:
            logger.error(f"Error in posting cookies: {e}")
    
    def post_email(email: str):
        """
        Function to post the email
        
        Args:
            email (str): The email
        """
        data = {
            "email": email
        }
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.email_table, data)

    def patch_cookies_data(data: dict):
        """
        Function to patch the cookies data
        
        Args:
            data (dict): The data to patch
        """
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)

    def get_cookie_Id_from_session_id(session_id: str) -> str:
        """
        Function to get the ID of the session ID
        
        Args:
            session_id (str): The session ID

        Returns:
            str: The ID of the session ID
        """
        try:
            cookie_data = Noco.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            return cookie_data.Id[index]
        except ValueError:
            logger.info(f"ID {session_id} not found from Id")
            return ""
    


    def get_artwork_Id_from_title(title: str) -> Union[int,None]:
        """
        Function to get the ID of the artwork from the title
        
        Args:
            title (str): The title of the artwork

        Returns:
            int: The Id of the artwork
        """
        artwork_data = Noco.get_artwork_data()
        index = artwork_data.titles.index(title)
        return artwork_data.Ids[index]
    
    def upload_image(file_to_upload: dict, path :str ) -> dict:
        """
        Function to upload an image
        
        Args:
            file_to_upload (dict): The file to upload
            path (str): The path to upload the file to

        Returns:
            dict: The response JSON
        """
        params = {
            "path": path
        }
        response = requests.post(Noco.get_storage_upload_path(), headers=Noco.get_auth_headers(), files=file_to_upload, params=params)
        response.raise_for_status()
        return response.json()
    

    def get_last_art_Id() -> int:
        """
        Function to get the last artwork ID
        
        Returns:
            int: The last artwork ID
        """
        artwork_data = Noco.get_artwork_data()
        return artwork_data.Ids[-1]
    
    def post_image(data: dict) -> None:
        """
        Function to post an image
        
        Args:
            data (dict): The data to post
        """
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.img_table, data)

    def patch_image(data: dict) -> None:
        """
        Function to patch an image
        
        Args:
            data (dict): The data to patch
        """
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.img_table, data)  

    def post_order_data(data: dict) -> None:
        """
        Function to post order data
        
        Args:
            data (dict): The order data
        """
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.order_table, data)

    def generate_unique_order_number():
        """
        Function to generate a unique number to index the order details in the database.
        Uses UUID4 to ensure the uniqueness of the order number.
        """
        return str(uuid.uuid4())

    def post_contact_data(data: dict) -> None:
        """
        Function to post contact data
        
        Args:
            data (dict): The contact data
        """
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.contact_table, data)

    def get_order_cookie_data(order_number: str) -> dict:
        """
        Function to get the cookie data for an order
        
        Args:
            order_number (str): The order number

        Returns:
            dict: The cookie data
        """
        cookie_data = Noco.get_contact_data()
        index = cookie_data.order_number.index(order_number)
        return {
            "fullname": cookie_data.fullname[index],
            "address1": cookie_data.address1[index],
            "address2": cookie_data.address2[index],
            "city": cookie_data.city[index],
            "state": cookie_data.state[index],
            "zip": cookie_data.zip[index],
            "order_number": cookie_data.order_number[index]
        }
    
    def refresh_artwork_cache():
        """
        Function to refresh the artwork cache
        """
        Noco.get_artwork_data.cache_clear()
    
    def delete_user_session_after_payment(session_id: str) -> None:
        """
        Function to delete the user session after payment
        
        Args:
            session_id (str): The session ID
        """
        cookie_data = Noco.get_cookie_data()
        index = cookie_data.sessionids.index(session_id)
        Noco.delete_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, cookie_data.Id[index])
        
    def post_order_contents(order_payload : dict) -> None:
        """
        Function to post order contents
        
        Args:
            order_payload (dict): The order payload
        """
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.content_table, order_payload)

    def get_session_mapping_intent_id(session_id: str) -> str:
        """
        Function to get the inteid from the paymentintent object where the orderid in the session mapping table is the indexed value you get from the session id and then when you index the order id to the paymentintenttable you can get the intentid from that index
        
        Args:
            session_id (str): The session ID

        Returns:
            str: The session mapping intent
        """
        try:
            session_mapping_data = Noco.get_session_mapping_data()
            index = session_mapping_data.sessionids.index(session_id)
            order_id = session_mapping_data.orderids[index]
            payment_intent_data = Noco.get_payment_intent_data()
            index = payment_intent_data.orderids.index(order_id)
            return payment_intent_data.intentids[index]
        except ValueError:
            logger.error(f"Session ID {session_id} not found in session mapping data")
            return ""
        
    def get_order_contents_from_session_id(session_id: str) -> dict:
        """
        Function to get the order contents from the session ID
        
        Args:
            session_id (str): The session ID

        Returns:
            dict: The order contents
        """
        content_data = Noco.get_cookie_data()
        index = content_data.sessionids.index(session_id)
        return content_data.cookies[index]
    
    def get_order_contents_from_order_number(order_number: str) -> dict:
        """
        Function to get the order contents from the order number
        
        Args:
            order_number (str): The order number

        Returns:
            dict: The order contents
        """
        content_data = Noco.get_content_data()
        index = content_data.order_number.index(order_number)
        return content_data.order_content[index]
    
    def get_total_price_from_order_contents(order_contents: dict) -> int:
        """
        Function to get the total price from the order contents
        
        Args:
            order_contents (dict): The order contents

        Returns:
            int: The total price
        """
        # For each title in img_quantity_list, get the quantity and title
        img_quantity_list = order_contents['img_quantity_list']

        for each in img_quantity_list:
            title = each['title']
            quantity = each['quantity']
            price = Noco.get_art_price_from_title_and_quantity(title, quantity)
            each['price'] = price
        total_price = sum([int(each['price']) for each in img_quantity_list])
        return total_price
    
    def get_last_cookie_Id() -> int:
        """
        Function to get the last cookie ID
        
        Returns:
            int: The last cookie ID
        """
        cookie_data = Noco.get_cookie_data()
        return cookie_data.Id[-1]

    
    def post_payment_intent_data(orderid: str, orderdetail: dict, email: str, amount: str, intentid: Union[str,int]) -> None:
        """
        Function to post the payment intent data
        
        Args:
            orderid (str): The order ID
            orderdetail (dict): The order detail
            email (str): The email
        """
        data = {
            "orderids": orderid,
            "orderdetails": orderdetail,
            "emails": email,
            "amounts": amount,
            "intentids": intentid
        }
        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.paymentintent_table, data)

    def patch_paymentintent_orderdetails_from_orderid(orderid: str, orderdetails: dict) -> None:
        """
        Function to patch the order details in the payment intent data
        
        Args:
            orderid (str): The order ID
            orderdetails (dict): The order details
        """
        data = {
            "Id": Noco.get_payment_intent_Id_from_orderid(orderid),
            "orderids": orderid,
            "orderdetails": orderdetails,
            "emails": Noco.get_email_from_orderid(orderid),
            "amounts": Noco.get_amount_from_orderid(orderid),
            "intentids": Noco.get_intentid_from_orderid(orderid)
        }
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.paymentintent_table, data)

    def delete_sessionmapping_from_sessionid(sessionid: str) -> None:
        """
        Function to delete the session mapping from the session ID
        
        Args:
            sessionid (str): The session ID
        """
        session_mapping_data = Noco.get_session_mapping_data()
        index = session_mapping_data.sessionids.index(sessionid)
        Noco.delete_nocodb_table_data(NOCODB_TABLE_MAP.session_mapping_table, session_mapping_data.Ids[index])

    def get_orderid_from_sessionid(sessionid: str) -> str:
        """
        Function to get the order ID from the session ID
        
        Args:
            sessionid (str): The session ID

        Returns:
            str: The order ID
        """
        logger.info(f"Getting orderid from sessionid: {sessionid}")
        try:
            session_mapping_data = Noco.get_session_mapping_data()
            index = session_mapping_data.sessionids.index(sessionid)
            return session_mapping_data.orderids[index]
        except IndexError as e:
            logger.error(f"Session ID {sessionid} not found in session mapping data. {e}")
            return ""
        except ValueError as e:
            logger.error(f"Session ID {sessionid} not found in session mapping data. {e}")
            return ""
        
    def get_orderdetails_from_orderid(orderid: str) -> dict:
        """
        Function to get the order details from the order ID
        
        Args:
            orderid (str): The order ID

        Returns:
            dict: The order details
        """
        payment_intent_data = Noco.get_payment_intent_data()
        index = payment_intent_data.orderids.index(orderid)
        return payment_intent_data.orderdetails[index]

    def get_email_from_orderid(orderid: str) -> str:
        """
        Function to get the email from the order ID
        
        Args:
            orderid (str): The order ID

        Returns:
            str: The email
        """
        payment_intent_data = Noco.get_payment_intent_data()
        index = payment_intent_data.orderids.index(orderid)
        return payment_intent_data.emails[index]
    
    def get_amount_from_orderid(orderid: str) -> str:
        """
        Function to get the amount from the order ID
        
        Args:
            orderid (str): The order ID

        Returns:
            str: The amount
        """
        payment_intent_data = Noco.get_payment_intent_data()
        index = payment_intent_data.orderids.index(orderid)
        return payment_intent_data.amounts[index]
    
    def get_intentid_from_orderid(orderid: str) -> str:
        """
        Function to get the intent ID from the order ID
        
        Args:
            orderid (str): The order ID

        Returns:
            str: The intent ID
        """
        try:
            payment_intent_data = Noco.get_payment_intent_data()
            index = payment_intent_data.orderids.index(orderid)
            return payment_intent_data.intentids[index]
        except ValueError as e:
            logger.error(f"Order ID {orderid} not found in payment intent data. {e}")
            return ""
        except KeyError as e:
            logger.error(f"Intent ID not found in payment intent data. {e}")
            return ""

    def get_payment_intent_Id_from_orderid(orderid: str) -> str:
        """
        Function to get the payment intent ID from the order ID
        
        Args:
            orderid (str): The order ID

        Returns:
            str: The payment intent ID
        """
        payment_intent_data = Noco.get_payment_intent_data()
        index = payment_intent_data.orderids.index(orderid)
        return payment_intent_data.Ids[index]
        
    def patch_email_to_cookie(sessionid: str, email: str) -> None:
        """
        Function to post the email to the cookie
        
        Args:
            sessionid (str): The session ID
            email (str): The email
        """
        current_nocodb_data = Noco.get_full_cookie_from_session_id(sessionid)
        current_nocodb_data['email'] = email

        data = {
            "Id": Noco.get_cookie_Id_from_session_id(sessionid),
            "sessionid": sessionid,
            "cookiesJson": current_nocodb_data
        }
        Noco.patch_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)


    def get_email_from_cookie(sessionid: str) -> str:
        """
        Function to get the email from the cookie
        
        Args:
            sessionid (str): The session ID

        Returns:
            str: The email
        """
        current_nocodb_data = Noco.get_full_cookie_from_session_id(sessionid)
        return current_nocodb_data['email']
    
    def refresh_content_cache():
        """
        Function to refresh the cookie cache
        """
        Noco.get_content_data.cache_clear()

    # def refresh_img_quant_lists():
    #     """

    #     Since this table stores the img_quantity_list, we need to loop throught he dictionaries in the img_quantity_list which is in the cookiesJson column
    #     and then we need to sync it with the prices, and titles in the artwork table, and update the data_uri for each title in the img_quantity_list,
    #     the data uri is created from the signedPath in the artwork table. and the functions in Noco. The img quant list can't have the data uri object it in it
    #     you have to replace that part ofthe object in the art object
    #     """
    #     cookie_data = Noco.get_cookie_data()
    #     artwork_data = Noco.get_artwork_data()
    #     for i, art_title in enumerate(artwork_data.titles):
    #         for cookie_title in cookie_data.cookiesJson:
    #             try:
    #                 price = artwork_data.prices[i]
    #             except ValueError:
    #                 # If the title is not found in the artwork data, remove it from the cookie data and patch the cookiesJson back
    #                 cookie_data.cookiesJson.remove(cookie_title)
    #                 cookie_data = {
    #                     "Id": cookie_data.Id[i],
    #                     "sessionid": cookie_data.sessionids[i],
    #                     "cookiesJson": cookie_data.cookiesJson
    #                 }
    #             try:
    
    def post_payment_payload(sessionid, payment_payload) -> None:
        """
        Function to post the payment payload
        
        Args:
            data (dict): The payment payload
        """
        payment_payload = {
            "sessionid": sessionid,
            "payment_payload": payment_payload
        }

        Noco.post_nocodb_table_data(NOCODB_TABLE_MAP.content_table, payment_payload)


    def get_cookie_session_begginging_time(sessionid: str) -> str:
        """
        Function to get the session time
        
        Args:
            sessionid (str): The session ID

        Returns:
            str: The session time
        """
        cookie_data = Noco.get_cookie_data()
        index = cookie_data.sessionids.index(sessionid)
        return cookie_data.created_ats[index]