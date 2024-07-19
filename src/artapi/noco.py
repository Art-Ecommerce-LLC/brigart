import base64
import requests
from functools import lru_cache
from src.artapi.config import (
    NOCODB_XC_TOKEN, NOCODB_PATH, NOCODB_TABLE_MAP
)
from src.artapi.models import (
    ArtObject, IconObject, KeyObject, CookieObject
)
from src.artapi.logger import logger
from PIL import Image
from io import BytesIO
from typing import Union, List, Dict, Any
import uuid
import asyncio
from fastapi import WebSocket
import stripe
from src.artapi.config import STRIPE_SECRET_KEY
import os
import tempfile
import random
import string
import time
from datetime import datetime, timezone

class PreviousData:
    def __init__(self):
        self.artwork: Union[ArtObject, None] = None
        self.icon: Union[IconObject, None] = None
        self.key: Union[KeyObject, None] = None
        self.cookie: Union[CookieObject, None] = None

class Noco:
    """
    Class to interact with NocoDB
    """
    _instance = None

    def __init__(self):
        self.headers = None
        self.base_url = None
        self.previous_data = PreviousData()
        self.connected_clients: List[WebSocket] = []
        self.artwork_cache: Union[ArtObject, None] = None
        stripe.api_key = STRIPE_SECRET_KEY 
        self.init_connection()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Noco, cls).__new__(cls)
        return cls._instance

    def init_connection(self):
        self.headers = {'xc-token': NOCODB_XC_TOKEN}
        self.base_url = NOCODB_PATH

    def get_auth_headers(self) -> dict:
        return self.headers

    def get_nocodb_path(self, table: str) -> str:
        return f"{self.base_url}/api/v2/tables/{table}/records"

    def get_storage_upload_path(self) -> str:
        return f"{self.base_url}/api/v2/storage/upload"

    def get_nocodb_table_data(self, table: str) -> dict:
        try:
            params = {"limit": 200}
            response = requests.get(self.get_nocodb_path(table), headers=self.get_auth_headers(), params=params)
            response.raise_for_status()
            logger.info(f"Fetched data from NocoDB table {table}")
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching data from NocoDB table {table}: {e}")
            raise

    def delete_nocodb_table_data(self, table: str, Id: int) -> None:
        try:
            body = {"Id": Id}
            response = requests.delete(f"{self.get_nocodb_path(table)}", headers=self.get_auth_headers(), json=body)
            response.raise_for_status()
            logger.info(f"Deleted data with ID {Id} from NocoDB table {table}")
        except Exception as e:
            logger.error(f"Error deleting data with ID {Id} from NocoDB table {table}: {e}")
            raise

    def post_nocodb_table_data(self, table: str, data: dict) -> None:
        try:
            response = requests.post(self.get_nocodb_path(table), headers=self.get_auth_headers(), json=data)
            response.raise_for_status()
            logger.info(f"Posted data to NocoDB table {table}")
        except Exception as e:
            logger.error(f"Error posting data to NocoDB table {table}: {e}")
            raise

    def patch_nocodb_table_data(self, table: str, data: dict) -> None:
        try:
            response = requests.patch(self.get_nocodb_path(table), headers=self.get_auth_headers(), json=data)
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
                img_data = requests.get(url_path).content
                data_uri = self.convert_to_data_uri(img_data)
                data_uris.append(data_uri)
            logger.info("Converted image paths to data URIs")
            return data_uris
        except Exception as e:
            logger.error(f"Error converting paths to data URIs: {e}")
            raise

    def convert_to_data_uri(self, image_data: bytes) -> str:
        try:
            with Image.open(BytesIO(image_data)) as img:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                width, height = img.size
                new_size = (int(width * 0.4), int(height * 0.4))
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

    @lru_cache(maxsize=128)
    def get_artwork_data(self) -> ArtObject:
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
            logger.info("Fetched and parsed artwork data from NocoDB")
            return artwork_data
        except Exception as e:
            logger.error(f"Error getting artwork data: {e}")
            raise

    def get_artwork_data_no_cache(self) -> ArtObject:
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

    def get_used_artwork_data_timestamps(self) -> list:
        try:
            artwork_data = self.get_artwork_data()
            return artwork_data.updated_ats
        except Exception as e:
            logger.error(f"Error getting updated_at timestamps for artwork data: {e}")
            raise

    def get_current_artwork_data_timestamps(self) -> list:
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.img_table)
            return [item['UpdatedAt'] for item in data['list']]
        except Exception as e:
            logger.error(f"Error getting updated_at timestamps for current artwork data: {e}")
            raise

    def compare_updated_at_timestamps(self, old_data: list, new_data: list) -> bool:
        try:
            if old_data != new_data:
                logger.info("Detected change in updated_at timestamps")
                return True
            return False
        except Exception as e:
            logger.error(f"Error comparing updated_at timestamps: {e}")
            raise

    def update_previous_data(self) -> None:
        try:
            # refresh the cached artwork data object
            self.get_artwork_data.cache_clear()

            logger.info("Updated previous_data with the current artwork data")
        except Exception as e:
            logger.error(f"Error updating previous_data: {e}")
            raise

    def has_artwork_data_changed(self) -> bool:
        try:
            used_timestamps = self.get_used_artwork_data_timestamps()
            current_timestamps = self.get_current_artwork_data_timestamps()
            # Compare the timestamps, if there is a discrepency then the data has changed
            if self.compare_updated_at_timestamps(used_timestamps, current_timestamps):
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking if artwork data changed: {e}")
            return False
        

    async def notify_clients_of_update(self, message: str):
        try:
            for client in self.connected_clients:
                await client.send_text(message)
            logger.info("Notified clients of update")
        except Exception as e:
            logger.error(f"Error notifying clients of update: {e}")

    @lru_cache(maxsize=128)
    def get_icon_data(self) -> IconObject:
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.icon_table)
            icon_paths = [item['img'][0]['signedPath'] for item in data['list']]
            data_uris = self.convert_paths_to_data_uris(icon_paths)
            icon_data = IconObject(
                icon_paths=icon_paths,
                titles=[item['img_label'] for item in data['list']],
                data_uris=data_uris
            )
            logger.info("Fetched and parsed icon data from NocoDB")
            return icon_data
        except Exception as e:
            logger.error(f"Error getting icon data: {e}")
            raise

    def get_key_data(self) -> KeyObject:
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

    def get_cookie_data_no_cache_no_object(self) -> list:
        try:
            data = self.get_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table)
            logger.info("Fetched cookie data without cache")
            return data
        except Exception as e:
            logger.error(f"Error getting cookie data without cache: {e}")
            raise

    def get_icon_uri_from_title(self, title: str) -> str:
        try:
            icon_data = self.get_icon_data()
            index = icon_data.titles.index(title)
            logger.info(f"Fetched icon URI for title {title}")
            return icon_data.data_uris[index]
        except ValueError:
            logger.error(f"Icon with title {title} not found")
            return ""

    def get_art_uri_from_title(self, title: str) -> str:
        try:
            artwork_data = self.get_artwork_data()
            index = artwork_data.titles.index(title)
            logger.info(f"Fetched artwork URI for title {title}")
            return artwork_data.data_uris[index]
        except ValueError:
            logger.error(f"Artwork with title {title} not found")
            return ""

    def get_art_price_from_title(self, title: str) -> str:
        try:
            artwork_data = self.get_artwork_data()
            index = artwork_data.titles.index(title)
            logger.info(f"Fetched price for artwork title {title}")
            return artwork_data.prices[index]
        except ValueError:
            logger.error(f"Artwork with title {title} not found")
            raise ValueError(f"Artwork with title {title} not found")

    def get_art_price_from_title_and_quantity(self, title: str, quantity: int) -> str:
        price = self.get_art_price_from_title(title)
        logger.info(f"Calculated price for {quantity} of artwork title {title}")
        return str(int(price) * quantity)

    def get_full_cookie_from_session_id(self, session_id: str) -> dict:
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            logger.info(f"Fetched full cookie for session ID {session_id}")
            return cookie_data.cookies[index]
        except ValueError:
            logger.error(f"Session ID {session_id} not found")
            return {}

    def get_cookie_from_session_id(self, session_id: str) -> list:
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
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            self.delete_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, cookie_data.Id[index])
            logger.info(f"Deleted session cookie for session ID {session_id}")
        except Exception as e:
            logger.error(f"Error deleting session cookie for session ID {session_id}: {e}")
            raise

    def patch_order_cookie(self, session_id: str, cookiesJson: dict, Id: int) -> None:
        data = {
            "Id": self.get_cookie_Id_from_session_id(session_id),
            "sessionid": session_id,
            "cookiesJson": cookiesJson
        }
        try:
            self.patch_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)
            logger.info(f"Patched order cookie for session ID {session_id}")
        except Exception as e:
            logger.error(f"Error patching order cookie for session ID {session_id}: {e}")
            raise

    def post_cookie_session_id_and_cookies(self, sessionid: str, cookies: dict):
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
        try:
            self.patch_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, data)
            logger.info("Patched cookies data")
        except Exception as e:
            logger.error(f"Error patching cookies data: {e}")
            raise

    def get_cookie_Id_from_session_id(self, session_id: str) -> str:
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            logger.info(f"Fetched cookie ID for session ID {session_id}")
            return cookie_data.Id[index]
        except ValueError:
            logger.info(f"ID {session_id} not found")
            return ""

    def get_artwork_Id_from_title(self, title: str) -> Union[int, None]:
        try:
            artwork_data = self.get_artwork_data()
            index = artwork_data.titles.index(title)
            logger.info(f"Fetched artwork ID for title {title}")
            return artwork_data.Ids[index]
        except ValueError:
            logger.error(f"Artwork with title {title} not found")
            return None

    def upload_image(self, file_to_upload: dict, path: str) -> dict:
        try:
            params = {
                "path": path
            }
            response = requests.post(self.get_storage_upload_path(), headers=self.get_auth_headers(), files=file_to_upload, params=params)
            response.raise_for_status()
            logger.info("Uploaded image")
            return response.json()
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            raise

    def get_last_art_Id(self) -> int:
        try:
            artwork_data = self.get_artwork_data()
            logger.info("Fetched last artwork ID")
            return artwork_data.Ids[-1]
        except Exception as e:
            logger.error(f"Error getting last artwork ID: {e}")
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

    @staticmethod
    def generate_unique_order_number():
        return str(uuid.uuid4())

    def refresh_artwork_cache(self) -> None:
        try:
            self.get_artwork_data.cache_clear()
            logger.info("Refreshed artwork cache")
        except Exception as e:
            logger.error(f"Error refreshing artwork cache: {e}")
            raise

    def delete_user_session_after_payment(self, session_id: str) -> None:
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(session_id)
            self.delete_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, cookie_data.Id[index])
            logger.info(f"Deleted user session after payment for session ID {session_id}")
        except Exception as e:
            logger.error(f"Error deleting user session after payment for session ID {session_id}: {e}")
            raise

    def get_last_cookie_Id(self) -> int:
        try:
            cookie_data = self.get_cookie_data()
            logger.info("Fetched last cookie ID")
            return cookie_data.Id[-1]
        except Exception as e:
            logger.error(f"Error getting last cookie ID: {e}")
            raise

    def get_cookie_session_begginging_time(self, sessionid: str) -> str:
        try:
            cookie_data = self.get_cookie_data()
            index = cookie_data.sessionids.index(sessionid)
            logger.info(f"Fetched session beginning time for session ID {sessionid}")
            return cookie_data.created_ats[index]
        except Exception as e:
            logger.error(f"Error getting session beginning time for session ID {sessionid}: {e}")
            raise
    
    def upload_image_to_stripe(self, file_path: str, title: str) -> str:
        try:
            with open(file_path, "rb") as fp:
                stripe_file = stripe.File.create(
                    purpose="product_image",
                    file=fp
                )
            file_link = stripe.FileLink.create(
                file=stripe_file.id
            )
            logger.info(f"Uploaded image to Stripe for title {title}: File ID {stripe_file.id}, File Link {file_link.url}")
            return file_link.url
        except Exception as e:
            logger.error(f"Error uploading image to Stripe for title {title}: {e}")
            raise

    def create_or_update_stripe_product(self, title: str, price: int, image_url: str) -> None:
        try:
            products = stripe.Product.list(limit=100)
            product_exists = False
            product_id = None

            for product in products:
                if product.name == title:
                    product_exists = True
                    product_id = product.id
                    break

            if product_exists:
                # Check if the image has changed
                if product.images != [image_url]:
                    stripe.Product.modify(
                        product_id,
                        images=[image_url]
                    )
                    logger.info(f"Updated Stripe product image for title {title}")

                existing_price_id = product.default_price
                existing_price = stripe.Price.retrieve(existing_price_id)
                existing_price_amount = existing_price.unit_amount // 100

                if existing_price_amount != price:
                    # Check if there's an existing inactive price with the same amount
                    prices = stripe.Price.list(product=product_id)
                    matching_inactive_price = next((p for p in prices if p.unit_amount == price * 100 and not p.active), None)

                    if matching_inactive_price:
                        # Reactivate the inactive matching price
                        stripe.Price.modify(
                            matching_inactive_price.id,
                            active=True
                        )
                        new_price_id = matching_inactive_price.id
                        logger.info(f"Reactivated existing price for product title {title}")
                    else:
                        # Create new price
                        new_price = stripe.Price.create(
                            product=product_id,
                            unit_amount=price * 100,
                            currency="usd",
                            tax_behavior="exclusive"
                        )
                        new_price_id = new_price.id
                        logger.info(f"Created new price for product title {title}")

                    # Update product with new price
                    stripe.Product.modify(
                        product_id,
                        default_price=new_price_id
                    )
                    logger.info(f"Updated product with new price for title {title}")

                    # Archive the old price if needed
                    stripe.Price.modify(
                        existing_price_id,
                        active=False
                    )
                    logger.info(f"Set existing price inactive for product title {title}")

            else:
                stripe.Product.create(
                    name=title,
                    tax_code="txcd_99999999",
                    default_price_data={
                        'currency': 'usd',
                        'unit_amount': price * 100,
                        'tax_behavior': 'exclusive'
                    },
                    images=[image_url],
                    shippable=True,
                )
                logger.info(f"Created new Stripe product for title {title}")

        except Exception as e:
            logger.error(f"Error creating or updating Stripe product for title {title}: {e}")
            raise


    async def check_for_artwork_updates(self, interval: int = 60):
        while True:
            try:
                if self.has_artwork_data_changed():
                    artwork_data = self.get_artwork_data_no_cache()
                    previous_data = self.get_artwork_data()

                    # Process the existing artwork data
                    min_length = min(len(artwork_data.titles), len(previous_data.titles))

                    for i in range(min_length):
                        new_image_data = artwork_data.data_uris[i]
                        new_price = int(artwork_data.prices[i])
                        new_title = artwork_data.titles[i]
                        new_image_path = self.decode_data_uri(new_image_data, new_title)

                        previous_image_data = previous_data.data_uris[i]
                        previous_price = int(previous_data.prices[i])
                        previous_title = previous_data.titles[i]

                        if new_image_data != previous_image_data or new_price != previous_price or new_title != previous_title:
                            image_url = self.upload_image_to_stripe(new_image_path, new_title)
                            self.create_or_update_stripe_product(new_title, new_price, image_url)
                            logger.info(f"Updated Stripe product for title {new_title}")

                        if new_image_path and os.path.exists(new_image_path):
                            os.remove(new_image_path)

                    # Process any new artwork data
                    if len(artwork_data.titles) > len(previous_data.titles):
                        for i in range(len(previous_data.titles), len(artwork_data.titles)):
                            new_image_data = artwork_data.data_uris[i]
                            new_price = int(artwork_data.prices[i])
                            new_title = artwork_data.titles[i]
                            new_image_path = self.decode_data_uri(new_image_data, new_title)

                            image_url = self.upload_image_to_stripe(new_image_path, new_title)
                            self.create_or_update_stripe_product(new_title, new_price, image_url)
                            logger.info(f"Created new Stripe product for title {new_title}")

                            if new_image_path and os.path.exists(new_image_path):
                                os.remove(new_image_path)

                    # Update the cached artwork data
                    self.update_previous_data()

                    await self.notify_clients_of_update("Artwork data updated")

            except Exception as e:
                logger.error(f"Error checking for artwork updates: {e}")
            await asyncio.sleep(interval)
    @staticmethod
    def generate_order_number():
        timestamp = int(time.time())  # Current timestamp as an integer
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # Random string of 6 characters
        return f"{timestamp}{random_str}"
    
    @staticmethod
    def get_version():
        return str(int(time.time()))

    @staticmethod
    async def delete_expired_sessions():
        while True:
            try:
                noco_db = Noco()  # Instantiate your database connection
                cookie_data = noco_db.get_cookie_data()
                sessions = cookie_data.sessionids
                created_ats = cookie_data.created_ats
                current_time = datetime.now(timezone.utc)

                for session_id, creation_time_str in zip(sessions, created_ats):
                    session_creation_time = datetime.fromisoformat(creation_time_str.replace('Z', '+00:00'))

                    elapsed_time = (current_time - session_creation_time).total_seconds()
                    if elapsed_time > 900:  # 15 minutes = 900 seconds
                        noco_db.delete_session_cookie(session_id)
                        logger.info(f"Deleted expired session {session_id}")

            except Exception as e:
                logger.error(f"Error deleting expired sessions: {e}")

            # Wait for 1 minute before checking again
            await asyncio.sleep(900)

    @staticmethod
    def decode_data_uri(data_uri: str, title: str) -> str:
        try:
            header, encoded = data_uri.split(",", 1)
            data = base64.b64decode(encoded)
            
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, f"{title}.png")
            
            # Write the image content to the file with the custom name
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(data)
            
            return temp_file_path
        except Exception as e:
            logger.error(f"Failed to decode data URI: {e}")

    @staticmethod
    def delete_temp_file(path: str):
        try:
            os.remove(path)
        except Exception as e:
            logger.error(f"Failed to delete temp file: {e}")

    @staticmethod
    def decode_data_uri_to_BytesIO(data_uri: str) -> BytesIO:
        try:
            header, encoded = data_uri.split(",", 1)
            data = base64.b64decode(encoded)
            return BytesIO(data)
        except Exception as e:
            logger.error(f"Failed to decode data URI: {e}")