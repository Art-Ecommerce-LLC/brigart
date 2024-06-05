import os
import requests
import json
from artapi.config import NOCODB_KEY_URL, NOCODB_IMG_URL, NOCODB_ICON_URL, XC_AUTH


def get_nocodb_key_data() -> str:
    headers = {'xc-token': XC_AUTH}
    response = requests.get(NOCODB_KEY_URL, headers=headers)
    response.raise_for_status()
    return response.text

def get_nocodb_data() -> str:
    headers = {'xc-token': XC_AUTH}
    response = requests.get(NOCODB_IMG_URL, headers=headers)
    response.raise_for_status()
    return response.text

def get_nocodb_icons() -> str:
    headers = {'xc-token': XC_AUTH}
    response = requests.get(NOCODB_ICON_URL, headers=headers)
    response.raise_for_status()
    return response.text

def get_nocodb_img_data() -> tuple:
    headers = {'xc-token': XC_AUTH}
    response = requests.get(NOCODB_IMG_URL, headers=headers)
    response.raise_for_status()
    data = response.json()
    images = []
    titles = []
    for item in data['list']:
        if item['img'] and len(item['img']) > 0:
            image_url = item['img'][0]['signedPath']
            images.append(image_url)
            title = item["img_label"]
            title_replace = title.replace("+", " ")
            titles.append(title_replace)
    return images,titles

def get_nocodb_icon_data() -> list:
    headers = {'xc-token': XC_AUTH}
    response = requests.get(NOCODB_ICON_URL, headers=headers)
    response.raise_for_status()
    data = response.json()
    images = []
    titles = []
    for item in data['list']:
        if item['img'] and len(item['img']) > 0:
            image_url = item['img'][0]['signedPath']
            images.append(image_url)
            titles.append(item["img_label"])
        
    return images, titles

def get_parsed_nocodb_data(data) -> tuple:
    try:
        data = json.loads(data)
        envvariable_names = []
        envvariable_values = []
        for i in data["list"]:
            if i["envvar"] != None:
                envvariable_names.append(i["envvar"])
            if i["envval"] != None:
                envvariable_values.append(i["envval"])
        return envvariable_names, envvariable_values
    except:
        print("Failed to parse data")

def get_allenv_variables() -> dict:
    env_names, env_values = get_parsed_nocodb_data(get_nocodb_key_data())
    # Make a dictionary of each env_name to env_value
    env_dict = {}
    for i in range(len(env_names)):
        env_dict[env_names[i]] = env_values[i]

    return env_dict

# Load all env variables from NOCODB into enviornment variables
env_dict = get_allenv_variables()
for key, value in env_dict.items():
    os.environ[key] = value

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
SMARTY_AUTH_TOKEN = os.getenv("smarty_auth_token")
