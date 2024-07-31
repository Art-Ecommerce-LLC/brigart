import base64
import requests
from src.artapi.config import (
    NOCODB_XC_TOKEN, NOCODB_PATH, NOCODB_TABLE_MAP
)
from src.artapi.models import (
    ArtObject, IconObject, KeyObject, CookieObject, ProductMapObject
)
from src.artapi.logger import logger
from PIL import Image
from io import BytesIO
from typing import Union
import stripe
from src.artapi.config import STRIPE_SECRET_KEY
from src.artapi.stripe_connector import StripeAPI
import time
from datetime import datetime, timezone
import pandas as pd
from typing import Dict, Set, Tuple
from functools import lru_cache

class CachedData:

    def __init__(self):
        self.artwork: Union[ArtObject, None] = None
        self.icon: Union[IconObject, None] = None
        self.key: Union[KeyObject, None] = None
        self.cookie: Union[CookieObject, None] = None
        self.product_map: Union[ProductMapObject, None] = None

class Noco:
    """
    Class to interact with NocoDB
    """
    _instance = None


    def __init__(self):
        self.headers = {'xc-token': NOCODB_XC_TOKEN}
        self.base_url = NOCODB_PATH
        self.previous_data = CachedData()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        stripe.api_key = STRIPE_SECRET_KEY 
        self.stripe_connector = StripeAPI()
        self.resolution_factor = 0.8

    def __del__(self):
        # Ensure the session is closed when the object is deleted
        self.session.close()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Noco, cls).__new__(cls)
        return cls._instance

    def get_auth_headers(self) -> dict:
        return self.headers

    def get_nocodb_path(self, table: str) -> str:
        return f"{self.base_url}/api/v2/tables/{table}/records"

    def get_storage_upload_path(self) -> str:
        return f"{self.base_url}/api/v2/storage/upload"

    def get_nocodb_table_data(self, table: str) -> dict:
        """
            Function to get the data from a table with a limit of 200

            Arguments:
                table (str): The name of the table to fetch data from.

            Returns:
                dict: The JSON response containing the data from the table.

            Raises:
                Exception: If there is an error fetching data from the table.
        """
        try:
            params = {"limit": 200}
            response = self.session.get(self.get_nocodb_path(table), params=params)
            response.raise_for_status()
            logger.info(f"Fetched data from NocoDB table {table}")
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching data from NocoDB table {table}: {e}")
            raise

    def get_nocodb_table_data_record(self, table: str, Id: int) -> dict:
        """
            Function to get a record from a table by its ID

            Arguments:
                table (str): The name of the table to fetch data from.
                Id (int): The ID of the record to fetch.

            Returns:
                dict: The JSON response containing the data from the record.
            
            Raises:
                Exception: If there is an error fetching data from the record
        """
        try:
            response = self.session.get(f"{self.get_nocodb_path(table)}/{Id}")
            response.raise_for_status()
            logger.info(f"Fetched data with ID {Id} from NocoDB table {table}")
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching data with ID {Id} from NocoDB table {table}: {e}")

    def delete_nocodb_table_data(self, table: str, Id: int) -> None:
        """
            Function to delete a record from a table by its ID

            Arguments:
                table (str): The name of the table to delete data from.
                Id (int): The ID of the record to delete.

            Raises:
                Exception: If there is an error deleting data from the table
        """
        try:
            body = {"Id": Id}
            response = self.session.delete(f"{self.get_nocodb_path(table)}", json=body)
            response.raise_for_status()
            logger.info(f"Deleted data with ID {Id} from NocoDB table {table}")
        except Exception as e:
            logger.error(f"Error deleting data with ID {Id} from NocoDB table {table}: {e}")
            raise

    def post_nocodb_table_data(self, table: str, data: dict) -> None:
        """
            Function to post data to a table

            Arguments:
                table (str): The name of the table to post data to.
                data (dict): The data to post to the table.
            
            Raises:
                Exception: If there is an error posting data to the table
        """
        try:
            response = self.session.post(self.get_nocodb_path(table), json=data)
            response.raise_for_status()
            logger.info(f"Posted data to NocoDB table {table}")
        except Exception as e:
            logger.error(f"Error posting data to NocoDB table {table}: {e}")
            raise

    def patch_nocodb_table_data(self, table: str, data: dict) -> None:
        """
            Function to patch data in a table

            Arguments:
                table (str): The name of the table to patch data in.
                data (dict): The data to patch in the table.

            Raises:
                Exception: If there is an error patching data in the table
        """
        try:
            response = self.session.patch(self.get_nocodb_path(table), json=data)
            response.raise_for_status()
            logger.info(f"Patched data in NocoDB table {table}")
        except Exception as e:
            logger.error(f"Error patching data in NocoDB table {table}: {e}")
            raise

    def convert_paths_to_data_uris(self, paths: list) -> list:
        try:
            data_uris = []
            for path in paths:
                url_path = f"{self.base_url}/{path}"
                img_data = self.session.get(url_path).content
                data_uri = self.convert_to_data_uri(img_data)
                data_uris.append(data_uri)
            logger.info("Converted image paths to data URIs")
            return data_uris
        except Exception as e:
            logger.error(f"Error converting paths to data URIs: {e}")
            raise

    def convert_to_data_uri(self, image_data: bytes) -> str:
        """
            Convert image data to a data URI
            
            Arguments:
                image_data (bytes): The image data to convert
            
            Returns:
                str: The data URI of the image data
            
            Raises:
                Exception: If there is an error converting the image data to a data URI
        """
        try:
            with Image.open(BytesIO(image_data)) as img:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                width, height = img.size
                new_size = (int(width * self.resolution_factor), int(height * self.resolution_factor))
                resized_img = img.resize(new_size, Image.ANTIALIAS)
                buffer = BytesIO()
                resized_img.save(buffer, format="JPEG")
                resized_img_data = buffer.getvalue()
            base64_data = base64.b64encode(resized_img_data).decode('utf-8')
            logger.info("Converted image data to data URI")
            return f"data:image/jpeg;base64,{base64_data}"
        except Exception as e:
            logger.error(f"Error converting image data to data URI: {e}")
            raise
    
    
    
    def get_artwork_data_with_cache(self) -> ArtObject:
        """
        Get the artwork data from NocoDB with caching.

        Returns:
            ArtObject: An object containing the artwork data

        Raises:
            Exception: If there is an error getting the artwork data
        """
        try:
            if self.compare_timestamps():
                # Clear the cache and update previous_data.artwork if timestamps are different
                self.clear_artwork_data_cache()
                self.previous_data.artwork = self.get_artwork_data_no_cache()
            return self._get_artwork_data_cached()
        except Exception as e:
            logger.error(f"Error getting artwork data with cache: {e}")
            raise

    @lru_cache(maxsize=1)
    def _get_artwork_data_cached(self) -> ArtObject:
        """
        Get the artwork data from NocoDB, this method is cached.

        Returns:
            ArtObject: An object containing the artwork data
        """
        return self.previous_data.artwork

    def clear_artwork_data_cache(self):
        """
        Clear the cache for artwork data.
        """
        self._get_artwork_data_cached.cache_clear()
        logger.info("Cleared artwork data cache")

    def compare_timestamps(self) -> bool:
        """
        Compare the timestamps of the current artwork data with the previous artwork data.

        Returns:
            bool: True if the timestamps are different, False otherwise
        """
        try:
            if self.previous_data.artwork is None:
                logger.info("No previous artwork data found")
                self.previous_data.artwork = self.get_artwork_data_no_cache()
                return False
            old_data = self.previous_data.artwork.updated_ats
            new_data = self.get_artwork_data_no_cache_no_datauri().updated_ats
            if new_data != old_data:
                logger.info("Detected change in updated_at timestamps")
                return True
            return False
        except Exception as e:
            logger.error(f"Error comparing timestamps: {e}")
            raise

    def get_artwork_data_no_cache(self) -> ArtObject:
        """
        Get the artwork data from NocoDB without caching.

        Returns:
            ArtObject: An object containing the artwork data

        Raises:
            Exception: If there is an error getting the artwork data without cache
        """
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.img_table)
            art_paths = [item['img'][0]['signedPath'] for item in data['list']]
            data_uris = self.convert_paths_to_data_uris(art_paths)
            artwork_data = ArtObject(
                art_paths=art_paths,
                titles=[item['img_label'] for item in data['list']],
                prices=[item['price'] for item in data['list']],
                data_uris=data_uris,
                created_ats=[item['CreatedAt'] for item in data['list']],
                updated_ats=[item['UpdatedAt'] for item in data['list']],
                Ids=[item['Id'] for item in data['list']]
            )
            logger.info("Fetched and parsed artwork data from NocoDB without cache")
            return artwork_data
        except Exception as e:
            logger.error(f"Error getting artwork data without cache: {e}")
            raise

    def get_artwork_data_no_cache_no_datauri(self) -> ArtObject:
        """
        Get the artwork data from NocoDB without caching and without data URIs.

        Returns:
            ArtObject: An object containing the artwork data without data URIs

        Raises:
            Exception: If there is an error getting the artwork data without cache and without data URIs
        """
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.img_table)
            art_paths = [item['img'][0]['signedPath'] for item in data['list']]
            artwork_data = ArtObject(
                art_paths=art_paths,
                titles=[item['img_label'] for item in data['list']],
                prices=[item['price'] for item in data['list']],
                created_ats=[item['CreatedAt'] for item in data['list']],
                updated_ats=[item['UpdatedAt'] for item in data['list']],
                Ids=[item['Id'] for item in data['list']]
            )
            logger.info("Fetched and parsed artwork data from NocoDB without cache and without data URIs")
            return artwork_data
        except Exception as e:
            logger.error(f"Error getting artwork data without cache and without data URIs: {e}")
            raise

    def get_product_id_from_title(self, title: str, product_map_data: ProductMapObject) -> Union[str, None]:
        """
            Get the product ID from the title

            Arguments:
                title (str): The title of the product
                product_map_data (ProductMapObject): The product map data
            
            Returns:
                str: The product ID for the title
        """
        try:
            index = product_map_data.noco_product_Ids.index(self.get_artwork_Id_from_title(title))
            logger.info(f"Fetched product ID for title {title}")
            return product_map_data.stripe_product_ids[index]
        except ValueError:
            logger.error(f"Product with title {title} not found")
            return None
        
    # def sync_stripe_product(self, product_id: str, title: str, price: str):
    #     """
    #         Sync a stripe product with the artwork data

    #         Arguments:
    #             product_id (str): The product ID to sync
    #             title (str): The title of the product
    #             price (str): The price of the product
    #     """
    #     try:
    #         stripe_product = self.stripe_connector.retrieve_product(product_id)
    #         stripe_price = self.stripe_connector.retrieve_price(stripe_product['prices']['data'][0]['id'])
    #         if str(stripe_price['unit_amount']) != price:
    #             self.stripe_connector.update_price(stripe_price['id'], price)
    #         if stripe_product['name'] != title:
    #             self.stripe_connector.update_product(product_id, title)
    #         if not stripe_product['active']:
    #             self.stripe_connector.unarchive_product(product_id)
    #         if not stripe_price['active']:
    #             self.stripe_connector.unarchive_price(stripe_price['id'])
    #         stripe_image_url = stripe_product['images'][0]
    #         stripe_image_to_uri = self.convert_to_data_uri(requests.get(stripe_image_url).content)
    #         if stripe_image_to_uri != self.get_art_uri_from_title(title):
    #             self.stripe_connector.update_product_image(product_id, f"{NOCODB_PATH}/{self.get_art_uri_from_title(title)}")
    #     except Exception as e:
    #         logger.error(f"Error syncing stripe product {product_id}: {e}")
    #         raise



    def get_product_map_data_no_cache(self) -> ProductMapObject:
        """
            Get the product map data from NocoDB

            Returns:
                ProductMapObject: An object containing the product map data

            Raises:
                Exception: If there is an error getting the product map data
        """
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.product_map_table)
            product_map_data = ProductMapObject(
                Id=[item['Id'] for item in data['list']],
                noco_product_Ids=[item['noco_product_Id'] for item in data['list']],
                stripe_product_ids=[item['stripe_product_id'] for item in data['list']],
                created_ats=[item['CreatedAt'] for item in data['list']],
                updated_ats=[item['UpdatedAt'] for item in data['list']]
            )
            logger.info("Fetched and parsed product map data from NocoDB")
            return product_map_data
        except Exception as e:
            logger.error(f"Error getting product map data: {e}")
            raise

  

    def get_used_artwork_data_timestamps(self) -> list:
        """
            Get the updated_at timestamps of the artwork data that was used in the previous iteration

            Returns:
                list: A list of updated_at timestamps of the artwork data that was used in the previous iteration
            
            Raises:
                Exception: If there is an error getting the updated_at timestamps for the artwork data
            
        """
        try:
            artwork_data = self.previous_data.artwork
            return artwork_data.updated_ats
        except Exception as e:
            logger.error(f"Error getting updated_at timestamps for artwork data: {e}")
            raise

    def get_current_artwork_data_timestamps(self) -> list:
        """
            Get the updated_at timestamps of the current artwork data

            Returns:
                list: A list of updated_at timestamps of the current artwork data
            
            Raises:
                Exception: If there is an error getting the updated_at timestamps for the current artwork data
        """
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.img_table)
            return [item['UpdatedAt'] for item in data['list']]
        except Exception as e:
            logger.error(f"Error getting updated_at timestamps for current artwork data: {e}")
            raise

    def compare_updated_at_timestamps(self, old_data: list, new_data: list) -> bool:
        """
            Compare the updated_at timestamps of the old and new artwork data
        
            Arguments:
                old_data (list): A list of updated_at timestamps of the old artwork data
                new_data (list): A list of updated_at timestamps of the new artwork data

            Returns:
                bool: True if the timestamps are different, False otherwise
        """
        try:
            if old_data != new_data:
                logger.info("Detected change in updated_at timestamps")
                return True
            return False
        except Exception as e:
            logger.error(f"Error comparing updated_at timestamps: {e}")
            raise
    

    def get_current_icon_data_timestamps(self) -> list:
        """
            Get the updated_at timestamps of the current icon data

            Returns:
                list: A list of updated_at timestamps of the current icon data
            
            Raises:
                Exception: If there is an error getting the updated_at timestamps for the current icon data
        """
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.icon_table)
            return [item['UpdatedAt'] for item in data['list']]
        except Exception as e:
            logger.error(f"Error getting updated_at timestamps for current icon data: {e}")
            raise



    def get_icon_data(self) -> IconObject:
        """
            Get the icon data from NocoDB
            
            Returns:
                IconObject: An object containing the icon data

            Raises:
                Exception: If there is an error getting the icon data
        """
        try:
            # Do a check to see if there is specific data in the IconObject that needs to be updated
            if self.previous_data.icon:
                return self.previous_data.icon
            else:
                self.previous_data.icon = self.get_icon_data_no_cache()
                return self.previous_data.icon
        except Exception as e:
            logger.error(f"Error getting icon data: {e}")
            raise



    def get_icon_data_no_cache(self) -> IconObject:
        """
            Get the icon data from NocoDB without caching
            
            Returns:
                IconObject: An object containing the icon data without caching
                
            Raises:
                Exception: If there is an error getting the icon data without caching
                
        """
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.icon_table)
            icon_paths = [item['img'][0]['signedPath'] for item in data['list']]
            data_uris = self.convert_paths_to_data_uris(icon_paths)
            icon_data = IconObject(
                icon_paths=icon_paths,
                titles=[item['img_label'] for item in data['list']],
                data_uris=data_uris,
                created_ats=[item['CreatedAt'] for item in data['list']],
                updated_ats=[item['UpdatedAt'] for item in data['list']],
                Ids=[item['Id'] for item in data['list']]
            )
            logger.info("Fetched and parsed icon data from NocoDB without cache")
            return icon_data
        
        except Exception as e:
            logger.error(f"Error getting icon data without cache: {e}")
            raise

    def get_key_data(self) -> KeyObject:
        """
            Get the key data from NocoDB

            Returns:
                KeyObject: An object containing the key data
            
            Raises:
                Exception: If there is an error getting the key data
            
        """
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.key_table)
            key_data = KeyObject(
                envvars=[item['envvar'] for item in data['list']],
                envvals=[item['envval'] for item in data['list']]
            )
            logger.info("Fetched and parsed key data from NocoDB")
            return key_data
        except Exception as e:
            logger.error(f"Error getting key data: {e}")
            raise
        
    def get_cookie_data(self) -> CookieObject:
        """
            Get the cookie data from NocoDB

            Returns:
                CookieObject: An object containing the cookie data
            
            Raises:
                Exception: If there is an error getting the cookie data
        """
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table)
            cookie_data = CookieObject(
                Id=[item['Id'] for item in data['list']],
                sessionids=[item['sessionids'] for item in data['list']],
                cookies=[item['cookies'] for item in data['list']],
                created_ats=[item['CreatedAt'] for item in data['list']]
            )
            logger.info("Fetched and parsed cookie data from NocoDB")
            return cookie_data
        except Exception as e:
            logger.error(f"Error getting cookie data: {e}")
            raise


    def get_icon_uri_from_title(self, title: str) -> str:
        """
            Get the icon URI from the title

            Arguments:
                title (str): The title of the icon
            
            Returns:
                str: The URI of the icon with the title
            
            Raises:
                ValueError: If the icon with the title is not found
        """
        try:
            icon_data = self.get_icon_data()
            index = icon_data.titles.index(title)
            logger.info(f"Fetched icon URI for title {title}")
            return icon_data.data_uris[index]
        except ValueError:
            logger.error(f"Icon with title {title} not found")
            return ""

    def get_art_uri_from_title(self, title: str) -> str:
        """
            Get the artwork URI from the title

            Arguments:
                title (str): The title of the artwork
            
            Returns:
                str: The URI of the artwork with the title
            
            Raises:
                ValueError: If the artwork with the title is not found
        """
        try:
            artwork_data = self.get_artwork_data_with_cache()
            index = artwork_data.titles.index(title)
            logger.info(f"Fetched artwork URI for title {title}")
            return artwork_data.data_uris[index]
        except ValueError:
            logger.error(f"Artwork with title {title} not found")
            return ""

    def get_art_price_from_title(self, title: str) -> str:
        """
            Get the price of the artwork from the title

            Arguments:
                title (str): The title of the artwork
            
            Returns:
                str: The price of the artwork with the title

            Raises:
                ValueError: If the artwork with the title is not found
        """
        try:
            artwork_data = self.get_artwork_data_with_cache()
            index = artwork_data.titles.index(title)
            logger.info(f"Fetched price for artwork title {title}")
            return artwork_data.prices[index]
        except ValueError:
            logger.error(f"Artwork with title {title} not found")
            raise ValueError(f"Artwork with title {title} not found")

    def get_art_price_from_title_and_quantity(self, title: str, quantity: int) -> str:
        """
            Get the total price of the artwork from the title and quantity

            Arguments:
                title (str): The title of the artwork
                quantity (int): The quantity of the artwork
            
            Returns:
                str: The total price of the artwork with the title and quantity
            
            Raises:
                ValueError: If the artwork with the title is not found
        """
        price = self.get_art_price_from_title(title)
        logger.info(f"Calculated price for {quantity} of artwork title {title}")
        return str(int(price) * quantity)

    def get_full_cookie_from_session_id(self, session_id: str) -> dict:
        """
            Get the full cookie data from the session ID

            Arguments:
                session_id (str): The session ID to fetch the cookie data
            
            Returns:
                dict: The full cookie data for the session ID
            
            Raises:
                ValueError: If the session ID is not found
        """
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            logger.info(f"Fetched full cookie for session ID {session_id}")
            return cookie_data.cookies[index]
        except ValueError:
            logger.error(f"Session ID {session_id} not found")
            return {}

    def get_cookie_from_session_id(self, session_id: str) -> list:
        """
            Get the cookie data from the session ID

            Arguments:
                session_id (str): The session ID to fetch the cookie data
            
            Returns:
                list: The cookie data for the session ID
            
            Raises:
                ValueError: If the session ID is not found
        """
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            img_quant_list = cookie_data.cookies[index]["img_quantity_list"]
            logger.info(f"Fetched cookie for session ID {session_id}")
            return img_quant_list
        except ValueError:
            logger.error(f"Session ID {session_id} not found")
            return []

    def delete_session_cookie(self, session_id: str) -> None:
        """
            Delete the session cookie from the session ID

            Arguments:
                session_id (str): The session ID to delete the cookie data
            
            Raises:
                Exception: If there is an error deleting the session cookie
        """
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            self.delete_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, cookie_data.Id[index])
            logger.info(f"Deleted session cookie for session ID {session_id}")
        except Exception as e:
            logger.error(f"Error deleting session cookie for session ID {session_id}: {e}")
            raise

    def post_cookie_session_id_and_cookies(self, sessionid: str, cookies: dict):
        """
            Post the cookie session ID and cookies

            Arguments:
                sessionid (str): The session ID to post
                cookies (dict): The cookies to post
            
            Raises:
                Exception: If there is an error posting the cookie session ID and cookies
        """
        data = {
            "sessionids": sessionid,
            "cookies": cookies
        }
        try:
            self.post_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)
            logger.info(f"Posted cookie session ID {sessionid}")
        except Exception as e:
            logger.error(f"Error posting cookies for session ID {sessionid}: {e}")

    def patch_cookies_data(self, data: dict):
        """
            Patch the cookies data

            Arguments:
                data (dict): The data to patch
            
            Raises:
                Exception: If there is an error patching the cookies data
        """
        try:
            self.patch_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)
            logger.info("Patched cookies data")
        except Exception as e:
            logger.error(f"Error patching cookies data: {e}")
            raise

    def get_cookie_Id_from_session_id(self, session_id: str) -> str:
        """
            Get the cookie ID from the session ID

            Arguments:
                session_id (str): The session ID to fetch the cookie ID
            
            Returns:
                str: The cookie ID for the session ID
            
            Raises:
                ValueError: If the session ID is not found
        """
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            logger.info(f"Fetched cookie ID for session ID {session_id}")
            return cookie_data.Id[index]
        except ValueError:
            logger.info(f"ID {session_id} not found")
            return ""

    def get_artwork_Id_from_title(self, title: str) -> Union[int, None]:
        """
            Get the artwork ID from the title

            Arguments:
                title (str): The title of the artwork
            
            Returns:
                int: The artwork ID for the title
            
            Raises:
                ValueError: If the artwork with the title is not found
        """
        try:
            artwork_data = self.get_artwork_data_with_cache()
            index = artwork_data.titles.index(title)
            logger.info(f"Fetched artwork ID for title {title}")
            return artwork_data.Ids[index]
        except ValueError:
            logger.error(f"Artwork with title {title} not found")
            return None

    def upload_image(self, file_to_upload: dict, path: str) -> dict:
        """
            Upload an image to the storage

            Arguments:
                file_to_upload (dict): The file to upload
                path (str): The path to upload the file to
            
            Returns:
                dict: The JSON response containing the uploaded image data
            
            Raises:
                Exception: If there is an error uploading the image
        """
        try:
            params = {
                "path": path
            }
            response = self.session.post(self.get_storage_upload_path(), files=file_to_upload, params=params)
            response.raise_for_status()
            logger.info("Uploaded image")
            return response.json()
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            raise

    def post_image(self, data: dict) -> None:
        try:
            self.post_nocodb_table_data(NOCODB_TABLE_MAP.img_table, data)
            logger.info("Posted image")
        except Exception as e:
            logger.error(f"Error posting image: {e}")
            raise

    def patch_image(self, data: dict) -> None:
        try:
            self.patch_nocodb_table_data(NOCODB_TABLE_MAP.img_table, data)
            logger.info("Patched image")
        except Exception as e:
            logger.error(f"Error patching image: {e}")
            raise

    def delete_user_session_after_payment(self, session_id: str) -> None:
        """
            Delete the user session after payment

            Arguments:
                session_id (str): The session ID to delete
            
            Raises:
                Exception: If there is an error deleting the user session after payment
            
        """
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            self.delete_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, cookie_data.Id[index])
            logger.info(f"Deleted user session after payment for session ID {session_id}")
        except Exception as e:
            logger.error(f"Error deleting user session after payment for session ID {session_id}: {e}")
            raise

    def get_cookie_session_begginging_time(self, sessionid: str) -> str:
        """
            Get the session beginning time for the session ID

            Arguments:
                sessionid (str): The session ID to fetch the session beginning time
            
            Returns:
                str: The session beginning time for the session ID
        """
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(sessionid)
            logger.info(f"Fetched session beginning time for session ID {sessionid}")
            return cookie_data.created_ats[index]
        except Exception as e:
            logger.error(f"Error getting session beginning time for session ID {sessionid}: {e}")
            raise

    @staticmethod
    def get_version():
        return str(int(time.time()))

    def delete_expired_sessions(self):
        """
            Delete expired sessions every 15 minutes
            
            Raises:
                Exception: If there is an error deleting expired sessions
        """
        try:
            cookie_data = self.get_cookie_data()
            sessions = cookie_data.sessionids
            created_ats = cookie_data.created_ats
            current_time = datetime.now(timezone.utc)

            for session_id, creation_time_str in zip(sessions, created_ats):
                session_creation_time = datetime.fromisoformat(creation_time_str.replace('Z', '+00:00'))

                elapsed_time = (current_time - session_creation_time).total_seconds()
                if elapsed_time > 900:  # 15 minutes = 900 seconds
                    self.delete_session_cookie(session_id)
                    logger.info(f"Deleted expired session {session_id}")

        except Exception as e:
            logger.error(f"Error deleting expired sessions: {e}")