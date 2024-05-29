# app/config.py
import dotenv
import os

dotenv.load_dotenv()

NOCODB_KEY_URL = os.getenv("key_url")
NOCODB_IMG_URL = os.getenv("img_url")
NOCODB_ICON_URL = os.getenv("icon_url")
XC_AUTH = os.getenv("xc_auth")
NOCODB_PATH = os.getenv("nocodb_path")
NOCODB_IMG_UPDATE_URL = os.getenv("nocodb_img_update_url")
