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

class PreviousData:
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
        self.previous_data = PreviousData()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        stripe.api_key = STRIPE_SECRET_KEY 

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

    def get_artwork_data(self) -> ArtObject:
        """
            Get the artwork data from NocoDB

            Returns:
                ArtObject: An object containing the artwork data
            
            Raises:
                Exception: If there is an error getting the artwork data
        """
        try:
            # Do a check to see if there is specific data in the ArtObject that needs to be updated
            if self.previous_data.artwork:
                old_data = self.previous_data.artwork.updated_ats
                new_data = self.get_current_artwork_data_timestamps()
                if self.compare_updated_at_timestamps(old_data, new_data):
                    # self.previous_data.artwork = self.get_artwork_data_no_cache()
                    self.update_previous_data()
                    return self.previous_data.artwork
                return self.previous_data.artwork
            else:
                self.previous_data.artwork = self.get_artwork_data_no_cache()
                return self.previous_data.artwork
        except Exception as e:
            logger.error(f"Error getting artwork data: {e}")
            raise



    def update_previous_data(self) -> Dict[str, pd.DataFrame]:
        try:
            # Watch for changes to the Id's, img_label, art_paths, and prices
            old_data = self.previous_data.artwork
            new_data = self.get_artwork_data_no_cache_no_datauri()
            key_columns = ["Ids", "titles", "prices", "art_paths"]
            df_old = pd.DataFrame(
                {
                    "Ids": old_data.Ids,
                    "titles": old_data.titles,
                    "prices": old_data.prices,
                    "art_paths": old_data.art_paths
                },
                columns=key_columns
            )
            df_new = pd.DataFrame(
                {
                    "Ids": new_data.Ids,
                    "titles": new_data.titles,
                    "prices": new_data.prices,
                    "art_paths": new_data.art_paths
                },
                columns=key_columns
            )
            
            # Compare the two dataframes

            # Check for added and deleted columns
            old_columns: Set[str] = set(df_old.columns)
            new_columns: Set[str] = set(df_new.columns)
            
            added_columns: Set[str] = new_columns - old_columns
            deleted_columns: Set[str] = old_columns - new_columns

            # Check for duplicates
            duplicates_old: pd.DataFrame = df_old[df_old.duplicated(subset=key_columns, keep=False)]
            duplicates_new: pd.DataFrame = df_new[df_new.duplicated(subset=key_columns, keep=False)]
            
            # Merge datasets on key columns
            df_merged: pd.DataFrame = pd.merge(df_old, df_new, on=key_columns, how='outer', suffixes=('_old', '_new'), indicator=True)

            # Identify added, deleted, and changed rows
            added: pd.DataFrame = df_merged[df_merged['_merge'] == 'right_only']
            deleted: pd.DataFrame = df_merged[df_merged['_merge'] == 'left_only']
            
            # For changed rows, we need to check if any column values (other than the key columns) have changed
            changes: pd.DataFrame = df_merged[df_merged['_merge'] == 'both']
            changed: pd.DataFrame = changes[
                (changes.filter(regex='_old$') != changes.filter(regex='_new$')).any(axis=1)
            ]

            # Check for null value changes
            null_changes: Dict[str, Tuple[int, int]] = {}
            for col in old_columns.intersection(new_columns):
                old_nulls: int = df_old[col].isnull().sum()
                new_nulls: int = df_new[col].isnull().sum()
                if old_nulls != new_nulls:
                    null_changes[col] = (old_nulls, new_nulls)

            # Check for row order changes
            row_order_changed: bool = not df_old.equals(df_new)

            data_changes = {
                'added': added,
                'deleted': deleted,
                'changed': changed,
                'added_columns': added_columns,
                'deleted_columns': deleted_columns,
                'null_changes': null_changes,
                'duplicates_old': duplicates_old,
                'duplicates_new': duplicates_new,
                'row_order_changed': row_order_changed
            }
            
            # Patch the data
            self.patch_inconsistent_artwork_data(data_changes)

        except Exception as e:
            logger.error(f"Error updating previous data: {e}")
            raise

    def patch_inconsistent_artwork_data(self, data: Dict[str, pd.DataFrame]) -> None:
        """
            Patch the inconsistent artwork data in the cache from the new data

            Arguments:
                data (dict): A dictionary containing the data to patch
            
            Raises:
                Exception: If there is an error patching the inconsistent artwork data
        """
        try:
            added: pd.DataFrame = data['added']
            deleted: pd.DataFrame = data['deleted']
            changed: pd.DataFrame = data['changed']
            added_columns: Set[str] = data['added_columns']
            deleted_columns: Set[str] = data['deleted_columns']
            null_changes: Dict[str, Tuple[int, int]] = data['null_changes']
            duplicates_old: pd.DataFrame = data['duplicates_old']
            duplicates_new: pd.DataFrame = data['duplicates_new']
            row_order_changed: bool = data['row_order_changed']

            # Create a mapping from IDs to their indices
            id_to_index = {id: index for index, id in enumerate(self.previous_data.artwork.Ids)}

            if added.shape[0] > 0:
                for index, row in added.iterrows():
                    new_id = row['Ids']
                    new_title = row['titles']
                    new_price = row['prices']
                    new_art_path = row['art_paths']
                    self.previous_data.artwork.Ids.append(new_id)
                    self.previous_data.artwork.titles.append(new_title)
                    self.previous_data.artwork.prices.append(new_price)
                    self.previous_data.artwork.art_paths.append(new_art_path)
                    self.previous_data.artwork.data_uris.append(self.convert_paths_to_data_uris([new_art_path])[0])
                    logger.info(f"Patched new data for title {new_title}")
            
            if deleted.shape[0] > 0:
                for index, row in deleted.iterrows():
                    old_id = row['Ids']
                    if old_id in id_to_index:
                        idx = id_to_index[old_id]
                        self.previous_data.artwork.Ids.pop(idx)
                        self.previous_data.artwork.titles.pop(idx)
                        self.previous_data.artwork.prices.pop(idx)
                        self.previous_data.artwork.art_paths.pop(idx)
                        self.previous_data.artwork.data_uris.pop(idx)
                        logger.info(f"Deleted data for ID {old_id}")
                        # Update the mapping since we modified the lists
                        id_to_index = {id: index for index, id in enumerate(self.previous_data.artwork.Ids)}
            
            if changed.shape[0] > 0:
                for index, row in changed.iterrows():
                    old_id = row['Ids_old']
                    new_id = row['Ids_new']
                    new_title = row['titles_new']
                    new_price = row['prices_new']
                    new_art_path = row['art_paths_new']
                    if old_id in id_to_index:
                        idx = id_to_index[old_id]
                        self.previous_data.artwork.Ids[idx] = new_id
                        self.previous_data.artwork.titles[idx] = new_title
                        self.previous_data.artwork.prices[idx] = new_price
                        self.previous_data.artwork.art_paths[idx] = new_art_path
                        self.previous_data.artwork.data_uris[idx] = self.convert_paths_to_data_uris([new_art_path])[0]
                        logger.info(f"Patched changed data for title {new_title}")
                        # Update the mapping since we modified the lists
                        id_to_index[new_id] = id_to_index.pop(old_id)

            if len(added_columns) > 0:
                for col in added_columns:
                    logger.info(f"Added column {col}")
            if len(deleted_columns) > 0:
                for col in deleted_columns:
                    logger.info(f"Deleted column {col}")
            if len(null_changes) > 0:
                for col, values in null_changes.items():
                    logger.info(f"Changed null values for column {col} from {values[0]} to {values[1]}")
            if duplicates_old.shape[0] > 0:
                for index, row in duplicates_old.iterrows():
                    logger.info(f"Found duplicate in old data: {row}")
            if duplicates_new.shape[0] > 0:
                for index, row in duplicates_new.iterrows():
                    logger.info(f"Found duplicate in new data: {row}")
            if row_order_changed:
                logger.info(f"Row order has changed between the datasets")
        except Exception as e:
            logger.error(f"Error patching inconsistent artwork data: {e}")
            raise


    def get_artwork_data_no_cache(self) -> ArtObject:
        """
            Get the artwork data from NocoDB without caching

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

    def get_artwork_data_no_cache_no_datauri(self) -> ArtObject:
        """
            Get the artwork data from NocoDB without caching and without data URIs

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

    def get_used_artwork_data_timestamps(self) -> list:
        """
            Get the updated_at timestamps of the artwork data that was used in the previous iteration

            Returns:
                list: A list of updated_at timestamps of the artwork data that was used in the previous iteration
            
            Raises:
                Exception: If there is an error getting the updated_at timestamps for the artwork data
            
        """
        try:
            artwork_data = self.get_artwork_data()
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
            artwork_data = self.get_artwork_data()
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
            artwork_data = self.get_artwork_data()
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
            artwork_data = self.get_artwork_data()
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