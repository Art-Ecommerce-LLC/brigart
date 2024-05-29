import json
import re
from functools import lru_cache
from PIL import Image
from aiohttp import ClientSession, ClientError
import os
from io import BytesIO
from contextlib import asynccontextmanager
import base64
from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from fastapi import FastAPI
from noco import get_nocodb_data, get_nocodb_icons, SITE_HOST, API_KEYS, HTTP
from logger import logger
from models import OrderInfo
from tempfile import TemporaryDirectory
import asyncio
import requests

scale_factor = 0.4
temp_dir = TemporaryDirectory()
api_key_header = APIKeyHeader(name='X-API_KEY')

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

async def preload_images() -> None:
    logger.info("Preloading images")
    try:
        loaded_nocodb_data = load_nocodb_data()
        loaded_icon_data = load_nocodb_icon_data()
        loaded_list = loaded_nocodb_data['list']
        tasks = []
        for each in loaded_icon_data['list']:
            loaded_list.append(each)
        async with ClientSession() as session:
            for item in loaded_nocodb_data['list']:
                for img_info in item['img']:
                    db_path = img_info['signedPath']
                    url_path = f"{HTTP}://{SITE_HOST}/{db_path}"
                    img_label = item['img_label']
                    file_path = os.path.join(temp_dir.name, f"{img_label}.png")
                    tasks.append(download_image(session, url_path, file_path))

            await asyncio.gather(*tasks)
        logger.info("Images preloaded successfully")
    except Exception as e:
        logger.error(f"Error preloading images: {e}")

def scale_image(image_data: bytes, file_path: str) -> None:
    try:
        image = Image.open(BytesIO(image_data))
        scaled_width = int(image.width * scale_factor)
        scaled_height = int(image.height * scale_factor)
        resized_image = image.resize((scaled_width, scaled_height))
        resized_image.save(file_path)
        logger.info(f"Image scaled and saved to {file_path}")
    except Exception as e:
        logger.error(f"Error scaling image: {e}")
        raise

async def download_image(session: ClientSession, url: str, file_path: str) -> None:
    logger.info(f"Downloading image from {url} to {file_path}")
    try:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                scale_image(image_data, file_path)
                logger.info(f"Successfully downloaded and saved image to {file_path}")
            else:
                logger.error(f"Failed to download image from {url}, status code: {response.status}")
    except ClientError as e:
        logger.error(f"Client error while downloading image from {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while downloading image from {url}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await preload_images()
        yield
    except Exception as e:
        logger.error(f"Error during app lifespan: {e}")
    finally:
        temp_dir.cleanup()
        logger.info("Temporary directory cleaned up")

def encode_image_to_base64(image_path: str) -> str:
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            logger.info(f"Encoded image at {image_path} to base64")
            return encoded
    except Exception as e:
        logger.error(f"Error encoding image at {image_path} to base64: {e}")
        raise

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
