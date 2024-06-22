# app/config.py
import dotenv
import os
from src.artapi.models import TableMap
# Get file path of .env file
dotenv_path = dotenv.find_dotenv()

# Load environment variables from .env file
dotenv.load_dotenv(dotenv_path)

NOCODB_PATH = os.getenv("nocodb_path")

NOCODB_XC_TOKEN = os.getenv("nocodb_xc_token")
NOCODB_EMAIL_TABLE = os.getenv("nocodb_email_table")
NOCODB_KEY_TABLE = os.getenv("nocodb_key_table")
NOCODB_IMG_TABLE = os.getenv("nocodb_img_table")
NOCODB_ICON_TABLE = os.getenv("nocodb_icon_table")
NOCODB_CONTACT_TABLE = os.getenv("nocodb_contact_table")
NOCODB_ORDER_TABLE = os.getenv("nocodb_order_table")
NOCODB_CONTENT_TABLE = os.getenv("nocodb_content_table")
NOCODB_COOKIES_TABLE = os.getenv("nocodb_cookies_table")
STRIPE_SECRET_KEY = os.getenv("stripe_secret_key")


# Create an instance of TableMap
NOCODB_TABLE_MAP = TableMap(
    img_table=NOCODB_IMG_TABLE,
    icon_table=NOCODB_ICON_TABLE,
    key_table=NOCODB_KEY_TABLE,
    email_table=NOCODB_EMAIL_TABLE,
    content_table=NOCODB_CONTENT_TABLE,
    contact_table=NOCODB_CONTACT_TABLE,
    order_table=NOCODB_ORDER_TABLE,
    cookies_table=NOCODB_COOKIES_TABLE
)



