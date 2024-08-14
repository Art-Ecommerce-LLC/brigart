import os
from src.artapi.noco import Noco

# Pull in the Noco object and postgreSQL connection

noco = Noco()
key_data = noco.get_key_data_with_api()

for i in range(len(key_data.envvars)):
    os.environ[key_data.envvars[i]] = key_data.envvals[i]

MIDDLEWARE_STRING = os.getenv("middleware_string")
OPENAPI_URL = os.getenv("openapi_url")
SHIPPING_RATE = os.getenv("shipping_rate")
ADMIN_DEVELOPER_NUMBER = os.getenv("admin_developer_number")
ADMIN_DEVELOPER_EMAIL = os.getenv("admin_developer_email")

# SMTP Server Config
SMTP_SERVER = os.getenv("smtp_server")
SMTP_PORT = os.getenv("smtp_port")
APP_PASSWORD = os.getenv("app_password")

# Telegram Config
ERROR405_BOT_TOKEN = os.getenv("error405_bot_token")
ERROR405_CHAT_ID = os.getenv("error405_chat_id")
