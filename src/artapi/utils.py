import json
import re
from functools import lru_cache
from PIL import Image
import os
from io import BytesIO
import base64
from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from src.artapi.noco import (
    post_nocodb_contact_data, post_nocodb_order_data, post_nocodb_content_data, get_nocodb_data, get_nocodb_icons, get_nocodb_email_data,  SITE_HOST, API_KEYS, HTTP
)
from src.artapi.logger import logger
from src.artapi.models import OrderInfo
from src.artapi.cache import Cache, load_nocodb_data, load_nocodb_icon_data, load_nocodb_email_data
from tempfile import TemporaryDirectory
import requests
import tempfile
import time
import string
import random
from typing import Union

scale_factor = 0.4
temp_dir = TemporaryDirectory()
api_key_header = APIKeyHeader(name='X-API_KEY')

cache = Cache()

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

async def cleancart(request: Request) -> None:
    logger.info("Cleaning cart")
    try:
        img_quant_list = request.session.get("img_quantity_list", [])

        # Check that each title in img_quant_list has
        # an accurate price and quantity in the cookies

        for item in img_quant_list:
            price_check = await get_price_from_title_and_quantity(item['title'], item['quantity'])
            if item['price'] != price_check:
                # update price
                item['price'] = price_check
                request.session['img_quantity_list'] = img_quant_list
                logger.info(f"Price updated for {item['title']}")


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

def update_email_cache_if_needed() -> dict:
    """Fetch current email data, check for inconsistencies, and update cache if needed."""
    logger.info("Fetching current email data from NoCoDB")
    current_email_data = json.loads(get_nocodb_email_data())

    # Fetch cached data
    cached_email_data = load_nocodb_email_data()

    # Check for inconsistencies between cache data and current data
    if check_for_inconsistencies(current_email_data, cached_email_data):
        load_nocodb_email_data.cache_clear()
        logger.info("Email cache cleared due to inconsistencies")
        email_data = current_email_data
    else:
        email_data = cached_email_data

    return email_data

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
        for i, item in enumerate(nocodb_data['list']):
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

def clear_cache():
    cache.data_uris = None
    cache.titles = None
    cache.icons = None
    load_nocodb_data.cache_clear()
    load_nocodb_icon_data.cache_clear()
    load_nocodb_email_data.cache_clear()
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

async def get_email_list() -> list:
    logger.info("Fetching email list")
    try:
        return fetch_email_list()
    except Exception as e:
        logger.error(f"Failed to fetch email list: {e}")
        raise

def fetch_email_list() -> list:
    try:
        email_data = update_email_cache_if_needed()
        email_list = [item['email'] for item in email_data['list']]
        logger.info("Email list fetched successfully")
        return email_list
    except Exception as e:
        logger.error(f"Failed to fetch email list: {e}")
        raise
def generate_order_number():
    timestamp = int(time.time())  # Current timestamp as an integer
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # Random string of 6 characters
    return f"{timestamp}{random_str}"

def post_order_data(contact_info: dict, shipping_info:dict, order_contents : list) -> str:
    try:
        order_number = generate_order_number()
        shipping_info['order_number'] = order_number
        logger.info(f"Posting order data for order number {order_number}")
        contact_payload = {
            "order_number" : order_number,
            "email" : contact_info['email'],
            "phone" : contact_info['phone'],           
        }
        shipping_payload = {
            "fullname" : shipping_info['fullname'],
            "address1" : shipping_info['address1'],
            "address2" : shipping_info['address2'],
            "city" : shipping_info['city'],
            "state" : shipping_info['state'],
            "zip" : shipping_info['zip'],
            "order_number" : order_number
        }
        post_nocodb_contact_data(shipping_payload)
        post_nocodb_order_data(contact_payload)
        post_content_data(shipping_info['order_number'], order_contents)
        logger.info("Order data posted successfully")
    except Exception as e:
        logger.error(f"Failed to post order data: {e}")
        raise

def post_content_data(order_number: str, order_contents : list) -> str:
    try:
        logger.info("Posting content data")
        order = {
            "order" : order_contents
        }
        order_data = {
            "order_number": order_number,
            "order_contents": order
        }
        post_nocodb_content_data(order_data)
        logger.info("Content data posted successfully")
    except Exception as e:
        logger.error(f"Failed to post content data: {e}")
        raise


async def get_price_from_title_and_quantity(title: str, quantity: Union[str,int]) -> str:
    """ Function to get price from title """
    try:
        nocodb_data = json.loads(get_nocodb_data())
        for item in nocodb_data['list']:
            if item['img_label'].replace("+", " ") == title:
                total_price = str(int(item['price']) * int(quantity))
                return total_price
    except Exception as e:
        logger.error(f"Failed to fetch price for {title}: {e}")
        raise

async def get_price_from_title(title: str) -> str:
    """ Function to get price from title """
    try:
        nocodb_data = json.loads(get_nocodb_data())
        for item in nocodb_data['list']:
            if item['img_label'] == title:
                return item['price']
    except Exception as e:
        logger.error(f"Failed to fetch price for {title}: {e}")
        raise

async def get_price_list() -> list:
    """ Function to get price list """
    try:
        nocodb_data = json.loads(get_nocodb_data())
        price_list = [item['price'] for item in nocodb_data['list']]
        return price_list
    except Exception as e:
        logger.error(f"Failed to fetch price list: {e}")
        raise