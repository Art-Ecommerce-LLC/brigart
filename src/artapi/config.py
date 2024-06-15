# app/config.py
import dotenv
import os

# Get file path of .env file
dotenv_path = dotenv.find_dotenv()

# Load environment variables from .env file
dotenv.load_dotenv(dotenv_path)

NOCODB_EMAIL_URL = os.getenv("nocodb_email_url")
NOCODB_KEY_URL = os.getenv("key_url")
NOCODB_IMG_URL = os.getenv("img_url")
NOCODB_ICON_URL = os.getenv("icon_url")
XC_AUTH = os.getenv("xc_auth")
NOCODB_PATH = os.getenv("nocodb_path")
NOCODB_IMG_UPDATE_URL = os.getenv("nocodb_img_update_url")
NOCODB_CONTACT_URL = os.getenv("nocodb_contact_url")
NOCODB_ORDER_URL = os.getenv("nocodb_order_url")
NOCODB_CONTENT_URL = os.getenv("nocodb_content_url")

