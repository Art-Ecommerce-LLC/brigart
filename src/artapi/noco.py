import base64
import requests
from PIL import Image
from io import BytesIO
from typing import Union
import time
from datetime import datetime, timezone
from functools import lru_cache
import ast

from .config import (
    NOCODB_XC_TOKEN, NOCODB_PATH
)
from .models import (
    ArtObject, IconObject, KeyObject, CookieObject, ProductMapObject
)
from . import crud, models
from .tables import NOCODB_TABLE_MAP
from .postgres import engine, SessionLocal, Base

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
        self.previous_data = CachedData()
        self.resolution_factor = 0.8
        self.cookie_session_time_limit = 60 * 15

        self.engine = engine
        self.SessionLocal = SessionLocal
        self.Base = Base
        self.crud = crud

        self.request = requests
        self.headers = {'xc-token': NOCODB_XC_TOKEN}
        self.base_url = NOCODB_PATH
        self.models = models
        self.models.Base.metadata.create_all(bind=self.engine)

    def get_auth_headers(self) -> dict:
        return self.headers

    def get_nocodb_path(self, table: str) -> str:
        return f"{self.base_url}/api/v2/tables/{table}/records"

    def get_storage_upload_path(self) -> str:
        return f"{self.base_url}/api/v2/storage/upload"
    
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
            response = self.request.post(self.get_nocodb_path(table), json=data, headers=self.get_auth_headers())
            response.raise_for_status()
        except Exception as e:
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
            response = self.request.patch(self.get_nocodb_path(table), json=data, headers=self.get_auth_headers())
            response.raise_for_status()
        except Exception as e:
            raise

    def convert_paths_to_data_uris(self, paths: list) -> list:
        """

            Convert a list of image paths to a list of data URIs

            Arguments:
                paths (list): A list of image paths to convert

            Returns:
                list: A list of data URIs of the image paths

            Raises:
                Exception: If there is an error converting the image paths to data URIs
        """
        try:
            data_uris = []
            for path in paths:
                url_path = f"{self.base_url}/{path}"
                img_data = requests.get(url_path).content
                data_uri = self.convert_to_data_uri(img_data)
                data_uris.append(data_uri)
            return data_uris
        except Exception as e:
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
                resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                buffer = BytesIO()
                resized_img.save(buffer, format="JPEG")
                resized_img_data = buffer.getvalue()
            base64_data = base64.b64encode(resized_img_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"
        except Exception as e:
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
                self.clear_artwork_data_cache()
                self.previous_data.artwork = self.get_artwork_data_no_cache()
            return self._get_artwork_data_cached()
        except Exception as e:
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

    def compare_timestamps(self) -> bool:
        """
        Compare the timestamps of the current artwork data with the previous artwork data.

        Returns:
            bool: True if the timestamps are different, False otherwise
        """
        try:
            if self.previous_data.artwork is None:
                self.previous_data.artwork = self.get_artwork_data_no_cache()
                return False
            old_data = self.previous_data.artwork.updated_ats
            new_data = self.get_artwork_data_no_cache_no_datauri().updated_ats
            if new_data != old_data:
                return True
            return False
        except Exception as e:
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
            data = self.crud.get_icons(self.SessionLocal(), skip=0, limit=100)
            icon_paths = [ast.literal_eval(item.img)[0]['path'] for item in data]
            data_uris = self.convert_paths_to_data_uris(icon_paths)
            icon_data = IconObject(
                icon_paths=icon_paths,
                titles=[item.img_label for item in data],
                data_uris=data_uris,
                created_ats=[item.created_at for item in data],
                updated_ats=[item.updated_at for item in data],
                Ids=[item.id for item in data]
            )
            return icon_data
        
        except Exception as e:
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
            data = self.crud.get_keys(self.SessionLocal(), skip=0, limit=100)
            key_data = KeyObject(
                envvars=[item.envvar for item in data],
                envvals=[item.envval for item in data],
            )
            return key_data
        except Exception as e:
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
            data = self.crud.get_cookies(self.SessionLocal(), skip=0, limit=100)
            cookie_data = CookieObject(
                Id=[item.id for item in data],
                sessionids=[item.sessionids for item in data],
                cookies=[item.cookies for item in data],
                created_ats=[item.created_at for item in data]  
            )
            return cookie_data
        except Exception as e:
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
            data = self.crud.get_artworks(self.SessionLocal(), skip=0, limit=100)
            art_paths = [ast.literal_eval(item.img)[0]['path'] for item in data]
            artwork_data = ArtObject(
                art_paths=art_paths,
                titles=[item.img_label for item in data],
                prices=[item.price for item in data],
                data_uris=self.convert_paths_to_data_uris(art_paths),
                created_ats=[item.created_at for item in data],
                updated_ats=[item.updated_at for item in data],
                Ids=[item.id for item in data]
            )
            return artwork_data
        except Exception as e:
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
            data = self.crud.get_artworks(self.SessionLocal(), skip=0, limit=100)
            art_paths = [ast.literal_eval(item.img)[0]['path'] for item in data]
            artwork_data = ArtObject(
                art_paths=art_paths,
                titles=[item.img_label for item in data],
                prices=[item.price for item in data],
                created_ats=[item.created_at for item in data],
                updated_ats=[item.updated_at for item in data],
                Ids=[item.id for item in data]
            )

            return artwork_data
        except Exception as e:
            raise
    
    def pull_single_key_record(self) -> dict:
        """
            Pull a single key record using the functions from the Noco class
        """
        try:
            # Pull key data and get the first record

            key_data_1 = self.get_key_data().envvals[0]
            return key_data_1
        except Exception as e:
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
                return True
            return False
        except Exception as e:
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
            return icon_data.data_uris[index]
        except ValueError:
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
            return artwork_data.data_uris[index]
        except ValueError:
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
            return self.crud.get_artwork_by_label(self.SessionLocal(), title).price
        except:
            raise

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
        return str(int(price) * quantity)
    
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
            return self.crud.get_cookie_by_sessionid(self.SessionLocal(), session_id).cookies["img_quantity_list"]
        except:
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
            self.crud.delete_cookie_from_sessionid(self.SessionLocal(), session_id)
        except:
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
        try:
            self.crud.create_cookie(self.SessionLocal(), sessionid, cookies)
        except:
            raise
    def patch_cookies_data(self, data: dict):
        """
            Patch the cookies data

            Arguments:
                data (dict): The data to patch
            
            Raises:
                Exception: If there is an error patching the cookies data
        """
        try:
            self.crud.update_cookie(self.SessionLocal(), data["Id"], data["sessionids"], data["cookies"])
        except:
            raise


    def get_cookie_Id_from_session_id(self, session_id: str) -> int:
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
            return self.crud.get_cookie_by_sessionid(self.SessionLocal(), session_id).id
        except:
            return ""

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
            response = self.request.post(self.get_storage_upload_path(), files=file_to_upload, params=params)
            response.raise_for_status()
            return response.json()
        except:
            raise

    def post_image(self, data: dict) -> None:
        try:
            self.post_nocodb_table_data(NOCODB_TABLE_MAP.img_table, data)
        except:
            raise

    def patch_image(self, data: dict) -> None:
        try:
            self.patch_nocodb_table_data(NOCODB_TABLE_MAP.img_table, data)
        except:
            raise

    def get_cookie_session_begginging_time(self, sessionid: str) -> datetime:
        """
            Get the session beginning time for the session ID

            Arguments:
                sessionid (str): The session ID to fetch the session beginning time
            
            Returns:
                str: The session beginning time for the session ID
        """
        try:
            return self.crud.get_cookie_by_sessionid(self.SessionLocal(), sessionid).created_at
        except:
            return ""

    @staticmethod
    def get_version():
        return str(int(time.time()))

    async def delete_expired_sessions(self) -> None:
        """
        Delete expired sessions every 15 minutes.

        Raises:
            Exception: If there is an error deleting expired sessions.
        """
        try:
            cookie_data = self.get_cookie_data()
            sessions = cookie_data.sessionids
            created_ats = cookie_data.created_ats
            current_time = datetime.now(timezone.utc)
            for session_id, creation_time in zip(sessions, created_ats):
                elapsed_time = (current_time - creation_time.replace(tzinfo=timezone.utc)).total_seconds()
                if elapsed_time > self.cookie_session_time_limit:
                    self.delete_session_cookie(session_id)
        except:
            raise 