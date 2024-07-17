import os
from src.artapi.noco import Noco

noco_db = Noco()

key_data = noco_db.get_key_data()

for i in range(len(key_data.envvars)):
    os.environ[key_data.envvars[i]] = key_data.envvals[i]

FASTAPI_PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
SITE_HOST = os.getenv("site_host")
API_KEYS = [FASTAPI_PASSWORD]
HTTP = os.getenv("http")
MIDDLEWARE_STRING = os.getenv("middleware_string")
OPENAPI_URL = os.getenv("openapi_url")
SCENE = os.getenv("scene")
BRIG_USERNAME = os.getenv("brig_username")
BRIG_PASSWORD = os.getenv("brig_password")
BEN_USERNAME = os.getenv("ben_username")
BEN_PASSWORD = os.getenv("ben_password")
SITE = os.getenv("site")
SMARTY_AUTH_ID = os.getenv("smarty_auth_id")