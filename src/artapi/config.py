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

# Prod Tables
NOCODB_KEY_TABLE = os.getenv("nocodb_key_table")
NOCODB_IMG_TABLE = os.getenv("nocodb_img_table")
NOCODB_ICON_TABLE = os.getenv("nocodb_icon_table")
NOCODB_COOKIES_TABLE = os.getenv("nocodb_cookies_table")
NOCODB_PRODUCT_MAP_TABLE = os.getenv("nocodb_product_map_table")

STRIPE_SECRET_KEY = os.getenv("stripe_secret_key")

DEVELOPMENT_ORIGINS = os.getenv("development_origins")
PRODUCTION_ORIGINS = os.getenv("production_origins")
DEVELOPMENT_HOSTS = os.getenv("development_hosts")
PRODUCTION_HOSTS = os.getenv("production_hosts")
ENVIORNMENT = os.getenv("enviornment")

# Create an instance of TableMap
NOCODB_TABLE_MAP = TableMap(
    img_table=NOCODB_IMG_TABLE,
    icon_table=NOCODB_ICON_TABLE,
    key_table=NOCODB_KEY_TABLE,
    cookies_table=NOCODB_COOKIES_TABLE,
    product_map_table =NOCODB_PRODUCT_MAP_TABLE
)

CSP_POLICY = os.getenv("csp_policy")