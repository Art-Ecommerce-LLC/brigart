import json
import re
from functools import lru_cache
from PIL import Image
import os
from io import BytesIO
import base64
from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from src.noco import get_nocodb_data, get_nocodb_icons, SITE_HOST, API_KEYS, HTTP
from logger import logger
from models import OrderInfo
from tempfile import TemporaryDirectory
import requests
import tempfile

scale_factor = 0.4
temp_dir = TemporaryDirectory()
api_key_header = APIKeyHeader(name='X-API_KEY')

class Cache:
    def __init__(self) -> None:
        self.data_uris = None
        self.titles = None

cache = Cache()

@lru_cache(maxsize=128)
def load_nocodb_data() -> dict:
    try:
        logger.info("Loading NoCoDB data")
        data = json.loads(get_nocodb_data())
        logger.info("NoCoDB data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_icon_data() -> dict:
    try:
        logger.info("Loading NoCoDB icon data")
        data = json.loads(get_nocodb_icons())
        logger.info("NoCoDB icon data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB icon data: {e}")
        raise

def encode_image_to_base64(image_path: str) -> str:
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            logger.info(f"Encoded image at {image_path} to base64")
            return encoded
    except Exception as e:
        logger.error(f"Error encoding image at {image_path} to base64: {e}")
        raise

def convert_to_data_uri(image_data: bytes) -> str:
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_data}"

def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in API_KEYS:
        logger.info("Valid API key provided")
        return api_key_header
    logger.warning("Invalid or missing API Key")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key")

def validate_inputs(order_info: OrderInfo) -> dict:
    logger.info("Validating order inputs")
    errors = {}
    if not re.match(r"[^@]+@[^@]+\.[^@]+", order_info.email):
        errors['email'] = 'Invalid email format'
        logger.warning("Invalid email format")
    if not re.match(r'^\+?\d+$', order_info.phone):
        errors['phone'] = 'Invalid phone number format'
        logger.warning("Invalid phone number format")
    return errors

def cleancart(request: Request) -> None:
    logger.info("Cleaning cart")
    try:
        img_quant_list = request.session.get("img_quantity_list", [])
        titles = [item['title'].lower() for item in img_quant_list]
        for title in titles:
            if titles.count(title) > 1:
                for item in img_quant_list:
                    if item['title'].lower() == title:
                        img_quant_list.remove(item)
                        break
        nocodb_data = get_nocodb_data()
        loaded_nocodb_data = json.loads(nocodb_data)
        for item in img_quant_list:
            match = False
            for each in loaded_nocodb_data['list']:
                if each['img_label'].replace("+", " ") == item['title']:
                    match = True
            if not match:
                img_quant_list.remove(item)
        request.session["img_quantity_list"] = img_quant_list
        logger.info("Cart cleaned successfully")
    except Exception as e:
        logger.error(f"Error cleaning cart: {e}")
        raise
def update_cache_if_needed() -> tuple:
    """Fetch current data, check for inconsistencies, and update cache if needed."""
    logger.info("Fetching current data from NoCoDB")
    current_nocodb_data = json.loads(get_nocodb_data())
    current_icon_data = json.loads(get_nocodb_icons())

    # Fetch cached data
    cached_nocodb_data = load_nocodb_data()
    cached_icon_data = load_nocodb_icon_data()
    # Check for inconsistencies between cache data and current data
    if check_for_inconsistencies(current_nocodb_data, cached_nocodb_data) or \
       check_for_inconsistencies(current_icon_data, cached_icon_data):
        clear_cache()
        logger.info("Cache cleared due to inconsistencies")
        nocodb_data = current_nocodb_data
        icon_data = current_icon_data
    else:
        nocodb_data = cached_nocodb_data
        icon_data = cached_icon_data

    return nocodb_data, icon_data

def check_for_inconsistencies(current_data: dict, cached_data: dict) -> bool:
    """Check for inconsistencies between current data and cached data."""

    return current_data != cached_data
def fetch_data_uris() -> tuple:
    logger.info("Fetching data URIs")
    try:
        nocodb_data, icon_data = update_cache_if_needed()

        # Check if cache is already populated and valid
        if cache.data_uris and cache.titles:
            logger.info("Using cached data URIs and titles")
            return cache.data_uris, cache.titles

        # Add icon data to the end of nocodb_data
        for item in icon_data['list']:
            nocodb_data['list'].append(item)

        imgs, titles = [], []
        temp_files = []
        for item in nocodb_data['list']:
            db_path = item['img'][0]['signedPath']
            url_path = f"{HTTP}://{SITE_HOST}/{db_path}"
            img_data = requests.get(url_path).content

            # Create temporary file for pre-scaled image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as pre_temp_file:
                pre_temp_file.write(img_data)
                pre_temp_file_path = pre_temp_file.name
                temp_files.append(pre_temp_file_path)

            # Scale image and convert to data URI
            scaled_img_data = scale_image(pre_temp_file_path)
            data_uri = convert_to_data_uri(scaled_img_data)
            imgs.append(data_uri)
            titles.append(item['img_label'].replace("+", " "))

        # Clean up all temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
                logger.info(f"Deleted temporary file {temp_file}")
            except Exception as e:
                logger.error(f"Error deleting temporary file {temp_file}: {e}")

        # Update cache
        cache.data_uris = imgs
        cache.titles = titles

        return imgs, titles
    except Exception as e:
        logger.error(f"Failed to fetch data URIs: {e}")
        raise

def update_cache_if_needed() -> tuple:
    """Fetch current data, check for inconsistencies, and update cache if needed."""
    logger.info("Fetching current data from NoCoDB")
    current_nocodb_data = json.loads(get_nocodb_data())
    current_icon_data = json.loads(get_nocodb_icons())

    # Fetch cached data
    cached_nocodb_data = load_nocodb_data()
    cached_icon_data = load_nocodb_icon_data()
    # Check for inconsistencies between cache data and current data
    if check_for_inconsistencies(current_nocodb_data, cached_nocodb_data) or \
       check_for_inconsistencies(current_icon_data, cached_icon_data):
        clear_cache()
        logger.info("Cache cleared due to inconsistencies")
        nocodb_data = current_nocodb_data
        icon_data = current_icon_data
    else:
        nocodb_data = cached_nocodb_data
        icon_data = cached_icon_data

    return nocodb_data, icon_data

def clear_cache():
    cache.data_uris = None
    cache.titles = None
    load_nocodb_data.cache_clear()
    load_nocodb_icon_data.cache_clear()
    logger.info("Caches cleared")

def scale_image(file_path: str) -> bytes:
    try:
        image = Image.open(file_path)
        scaled_width = int(image.width * scale_factor)
        scaled_height = int(image.height * scale_factor)
        resized_image = image.resize((scaled_width, scaled_height))
        
        with BytesIO() as output:
            resized_image.save(output, format="PNG")
            logger.info(f"Image scaled and saved to in-memory bytes")
            return output.getvalue()
    except Exception as e:
        logger.error(f"Error scaling image: {e}")
        raise


async def hosted_image() -> tuple:
    logger.info("Hosted images requested")
    try:
        return fetch_data_uris()
    except Exception as e:
        logger.error(f"Failed to fetch hosted image: {e}")
        raise

async def get_data_uri_from_title(title) -> str:
    logger.info(f"Fetching data URI for {title}")
    try:
        data_uris, titles = await hosted_image()
        index = titles.index(title)
        data_uri = data_uris[index]
        return data_uri
    except Exception as e:
        logger.error(f"Failed to fetch data URI for {title}: {e}")
        raise
            