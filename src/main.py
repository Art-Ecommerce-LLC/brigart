from fastapi import FastAPI, Security, HTTPException, status, Request, Form
from fastapi.security import APIKeyHeader
import uvicorn
import json
import dotenv
import os
import requests
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.sessions import SessionMiddleware
import json
from urllib.parse import unquote
import urllib3
import re
from typing import Annotated, List
import tempfile
import shutil
import PIL
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
import aiohttp
import asyncio
from contextlib import asynccontextmanager
import base64

urllib3.disable_warnings()
# Temporary directory to store images
temp_dir = tempfile.TemporaryDirectory()

@lru_cache(maxsize=128)
def load_nocodb_data():
    nocodb_data = get_nocodb_data()  # Your function to fetch data from NoCodeB
    return json.loads(nocodb_data)

@lru_cache(maxsize=128)
def load_nocodb_icon_data():
    nocodb_data = get_nocodb_icons()
    return json.loads(nocodb_data)
    
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def preload_images():
    loaded_nocodb_data = load_nocodb_data()
    loaded_icon_data = load_nocodb_icon_data()
    loaded_list = loaded_nocodb_data['list']
    tasks= []
    for each in loaded_icon_data['list']:
        loaded_list.append(each)
        
    async with aiohttp.ClientSession() as session:
        for item in loaded_nocodb_data['list']:
            for img_info in item['img']:
                db_path = img_info['signedPath']
                url_path = f"http://{site_host}/{db_path}"
                img_label = item['img_label']
                file_path = os.path.join(temp_dir.name, f"{img_label}.png")
                tasks.append(download_image(session, url_path, file_path))

        await asyncio.gather(*tasks)



async def download_image(session, url, file_path):
    async with session.get(url) as response:
        if response.status == 200:
            # Read the image data
            image_data = await response.read()
            scale_factor = 0.4
            # Open and resize the image by a factor
            image = Image.open(BytesIO(image_data))
            scaled_width = int(image.width * scale_factor)
            scaled_height = int(image.height * scale_factor)
            resized_image = image.resize((scaled_width, scaled_height))
            
            # Save the resized image
            resized_image.save(file_path)


async def run_periodically(interval, coro, *args, **kwargs):
    while True:
        await coro(*args, **kwargs)
        await asyncio.sleep(interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    interval = 6 * 60 * 60  # 6 hours in seconds
    preload_task = asyncio.create_task(run_periodically(interval, preload_images))
    try:
        await preload_images()  # Initial preload
        yield
    finally:
        preload_task.cancel()
        temp_dir.cleanup()


# Define FastAPI App
api_key_header = APIKeyHeader(name = 'X-API_KEY')

# Load NocDB env variables from .env file
dotenv.load_dotenv()
nocodb_key_url = os.getenv("key_url")
nocodb_img_url = os.getenv("img_url")
nocodb_icon_url = os.getenv("icon_url")
xc_auth = os.getenv("xc_auth")
nocodb_path = os.getenv("nocodb_path")
nocodb_img_update_url = os.getenv("nocodb_img_update_url")

# Define Security Scheme
def get_watermark(img_path, title) -> tuple[Image.Image, str]:
    with Image.open(img_path) as img:
        # Add watermark
        watermark_text = "BRIGLIGHT"
        
        # Increase the font size and choose a bold font
        watermark_font = ImageFont.truetype("arialbd.ttf", 407)
        
        draw = ImageDraw.Draw(img)

        # Calculate text size using textbbox
        text_bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        img_width, img_height = img.size

        # Calculate position for the watermark text (top-down from top)
        watermark_x = (img_height - text_width) // 2  # Adjusted to center vertically
        watermark_y = 0  # Start from the top of the image

        # Rotate and add the watermark text at the calculated position
        rotated_text = Image.new('RGBA', (text_width, img_height), (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(rotated_text)

        # Use a bold gray color for the watermark text
        lighter_gray_color = (220, 220, 220, 50)

        text_draw.text((0, 0), watermark_text, fill=lighter_gray_color, font=watermark_font)
        rotated_text = rotated_text.rotate(65, expand=True)

        img.paste(rotated_text, (watermark_x, watermark_y), rotated_text)
        base_path = os.path.dirname(img_path)
        
        # Save the watermarked image
        watermark_filename = f"watermarked_{title}.PNG.png"
        watermark_path = os.path.join(base_path, watermark_filename)
        img.save(watermark_path)

        return img, watermark_path

def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",

        
    )
def get_nocodb_data():
    headers = {
        'xc-token': xc_auth
    }
    response = requests.get(nocodb_img_url, headers=headers)
    return response.text

def get_nocodb_icons():
    headers = {
        'xc-token': xc_auth
    }
    response = requests.get(nocodb_icon_url, headers=headers)
    return response.text

# Get nocodb data from their REST API
def get_nocodb_key_data():
    headers = {
        'xc-token': xc_auth
    }
    response = requests.get(nocodb_key_url, headers=headers)
    return response.text

def get_nocodb_img_data():
    headers = {
        'xc-token': xc_auth
    }
    response = requests.get(nocodb_img_url, headers=headers)
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


def get_nocodb_icon_data():
    headers = {
        'xc-token': xc_auth
    }
    response = requests.get(nocodb_icon_url, headers=headers)
    data = response.json()

    images = []
    for item in data['list']:
        if item['img'] and len(item['img']) > 0:
            image_url = item['img'][0]['signedPath']
            images.append(image_url)
        
    return images

# Parse the nocodb data into a list of environment variables
def get_parsed_nocodb_data(data):
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

# Structure the enviornment variables from the nocodb cloud table into a dictionary
def get_allenv_variables():
    env_names, env_values = get_parsed_nocodb_data(get_nocodb_key_data())
    # Make a dictionary of each env_name to env_value
    env_dict = {}
    for i in range(len(env_names)):
        env_dict[env_names[i]] = env_values[i]

    return env_dict




             
# Define API Keys
# Get the enviornment variables from the nocodb cloud table
env_dict = get_allenv_variables()
fastapi_password = env_dict["password"]
host = env_dict["host"]
port = env_dict["port"]
site_host = env_dict["site_host"]
api_keys = [fastapi_password]
http = env_dict["http"]
middleware_string = env_dict["middleware_string"]
openapi_url = env_dict["openapi_url"]
scene = env_dict["scene"]
brig_username = env_dict["brig_username"]
brig_password = env_dict["brig_password"]
site = env_dict["site"]


#smarty keys
smarty_auth_id = env_dict["smarty_auth_id"]
smarty_auth_token = env_dict["smarty_auth_token"]

# Initialize FastAPI App
desc = "Backend platform for BRIG ART"

if openapi_url == "None":
    openapi_url = None

app = FastAPI(
    title = "Brig API",
    description= desc,
    openapi_url = openapi_url,
    lifespan=lifespan
)
app.add_middleware(SessionMiddleware, secret_key=middleware_string)

# Mount StaticFiles instance to serve files from the "src" directory
# app.mount("/", StaticFiles(directory="src", html=True), name="src")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="src/templates")
# Define API Key Header

def refresh_shop_cart(request: Request):
    
    img_quant_list = request.session.get("img_quantity_list")
    imgs, titles = get_nocodb_img_data()

    if img_quant_list is None:
        img_quant_list = []
    for each_url in img_quant_list:
        for title in titles:
            if each_url["title"] == title:
                correct_link = imgs[titles.index(title)]
                host_string = f"{http}://{site_host}/{correct_link}"
                each_url["img_url"] = host_string
                request.session["img_quantity_list"] = img_quant_list

class Url(BaseModel):
    url: str
    title1: str

class UrlQuantity(BaseModel):
    url: str
    quantity: str
    title2 : str


class OrderInfo(BaseModel):
    email: EmailStr = Field(...)
    phone: str = Field(..., min_length=10, max_length=15)
    cardName: str = Field(...)
    cardNumber: str = Field(..., min_length=15, max_length=16)
    expiryDate: str = Field(..., pattern=r'^\d{2}/\d{2}$')
    cvv: str = Field(..., min_length=3, max_length=4)
    fullname: str = Field(...)
    address1: str = Field(...)
    address2: str = Field(...)
    city: str = Field(...)
    state: str = Field(...)
    zip: str = Field(..., min_length=5, max_length=10) # Adjust min and max length as needed

class Credentials(BaseModel):
    username : str
    password : str

def validate_inputs(order_info: OrderInfo):
    errors = {}
    
    # Validate email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", order_info.email):
        errors['email'] = 'Invalid email format'

    # Validate phone number
    if not re.match(r'^\+?\d+$', order_info.phone):
        errors['phone'] = 'Invalid phone number format'

    # Other validations...

    return errors


@app.middleware(http)
async def some_middleware(request: Request, call_next):
    response = await call_next(request)

    # No need to manually handle session cookies here
    return response


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):

    imgs,titles = get_nocodb_img_data()
    icons = get_nocodb_icon_data()

    # Refresh the shopping cart because IMG URls change


    shopping_cart_url = f"{http}://" + f"{site}/hostedimage/shopping_cart" 
    hamburger_menu_url = f"{http}://" + f"{site}/hostedimage/menu_burger" 
    brig_logo_url = f"{http}://" + f"{site}/hostedimage/brigLogo" 
    # temp_vars = [nocodb_path + each for each in imgs]
    # each tempvar will now be the path to the image
    temp_vars = [f"{http}://" + f"{site}/hostedimage/" + title.replace(" ", "+") for title in titles]
    data_uris = []
    for url in temp_vars:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                image_data = await response.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                data_uri = f"data:image/jpeg;base64,{base64_data}"
                data_uris.append(data_uri)
    zipped_imgs_titles = zip(data_uris, titles)


    context = {
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url,
        "brig_logo_url": brig_logo_url,
        "temp_vars": zipped_imgs_titles,
    }

    return templates.TemplateResponse(request=request,
                                      name="index.html",
                                      context=context)

@app.post("/shop")
async def shop_img_url(request: Request, url: Url):

    imgs, titles = get_nocodb_img_data()

    # By default if the match string doesn't change to true the url is invalid
    match = False
    for item in imgs:
        url_string = f"{http}://" + f"{site_host}/" + item
        if url.url == url_string:
            match = True
    
    if match == True:
        request.session["img_url"] = url.url
        request.session["title"] = url.title1
    else:
        raise(HTTPException(status_code=400, detail="Invalid URL in Shop Request"))

@app.get("/shop/{title}", response_class=HTMLResponse)
async def shop(request: Request, title : str):
 
    
    # icons = get_nocodb_icon_data()
    # Refresh the shopping cart because IMG URls change
    # Find the img url associate with the title and store both in the session
    nocodb_data = get_nocodb_data()
    loaded_nocodb_data = json.loads(nocodb_data)



    for item in loaded_nocodb_data['list']:
        if item['img_label'] == title:
            db_path = item['img'][0]['signedPath']
            url_path = f"{http}://" + f"{site}/hostedimage/" + title.replace(" ", "+")
            request.session["img_url"] = url_path
            request.session["title"] = title.replace("+", " ")

    shopping_cart_url = f"{http}://" + f"{site}/hostedimage/shopping_cart" 
    hamburger_menu_url = f"{http}://" + f"{site}/hostedimage/menu_burger" 
    brig_logo_url = f"{http}://" + f"{site}/hostedimage/brigLogo" 
    img_url = request.session.get("img_url")
    img_title = request.session.get("title")
    async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as response:
                image_data = await response.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                img_url = f"data:image/jpeg;base64,{base64_data}"
    context = {
        "img_url": img_url, 
        "img_title": img_title, 
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url, 
        "brig_logo_url": brig_logo_url
        }
    return templates.TemplateResponse(request = request,
                                      name = "shop.html",
                                      context = context)





@app.post("/shop_art")
async def shop_art_url(request: Request, url_quant: UrlQuantity):

    imgs, titles  = get_nocodb_img_data()
    match = False
    nocodb_data = get_nocodb_data()
    loaded_nocodb_data = json.loads(nocodb_data)
    for item in loaded_nocodb_data['list']:
        title = url_quant.title2.replace(" ", "+")
        if item['img_label'] == title:
            db_path = item['img'][0]['signedPath']
            url_path = f"{http}://" + f"{site}/hostedimage/" + title.replace(" ", "+")
            request.session["img_url"] = url_path
            request.session["title"] = title.replace("+", " ")
            match = True

    if match == True:
        img_url = url_path
        quantity = url_quant.quantity
        title = url_quant.title2

        img_quantity_list = request.session.get("img_quantity_list")

    
        quant_img_dict = {
            "img_url": img_url,
            "quantity": quantity,
            "title": title
        }

        if img_quantity_list is None or []:
            img_quantity_list = []
            img_quantity_list.append(quant_img_dict)
            request.session["img_quantity_list"] = img_quantity_list
        else:
            for each_item in img_quantity_list:
                if title == each_item["title"]:
                    new_quantity = int(each_item["quantity"]) + int(quantity)
                    temp_quant_dict = {
                        "img_url": img_url,
                        "quantity": new_quantity,
                        "title": title
                    }
                    request.session["img_quantity_list"].remove(each_item)
                    request.session["img_quantity_list"].append(temp_quant_dict)
                    print(img_quantity_list)
                    break
            else:
                request.session["img_quantity_list"].append(quant_img_dict)
    else:
        raise(HTTPException(status_code=400, detail="Invalid URL in Shop_Art Request"))

def cleancart(request: Request):
    img_quant_list = request.session.get("img_quantity_list")

    titles = [item['title'].lower() for item in img_quant_list]
    print(titles)
    # Check if there are repeating titles in the list
    for title in titles:
        if titles.count(title) > 1:
            for item in img_quant_list:
                if item['title'].lower() == title:
                    img_quant_list.remove(item)
                    break
    # Check if the title exists in the nocodb database, if not remove it from the list
    nocodb_data = get_nocodb_data()
    loaded_nocodb_data = json.loads(nocodb_data)
    for item in img_quant_list:
        match = False
        for each in loaded_nocodb_data['list']:
            if each['img_label'] == item['title']:
                match = True
        if match == False:
            img_quant_list.remove(item)
            
                    

    request.session["img_quantity_list"] = img_quant_list

@app.get("/shop_art", response_class=HTMLResponse)
async def shop_art(request: Request):
    
    cleancart(request)

    img_quant_list = request.session.get("img_quantity_list")

    icons = get_nocodb_icon_data()

    # Refresh the shopping cart because IMG URls change


    shopping_cart_url = f"{http}://" + f"{site}/hostedimage/shopping_cart" 
    hamburger_menu_url = f"{http}://" + f"{site}/hostedimage/menu_burger" 
    brig_logo_url = f"{http}://" + f"{site}/hostedimage/brigLogo" 

    img_data_list = []

    if img_quant_list is None or []:
        img_quant_list = []
        for item in img_quant_list:
            img_dict = {}
            decoded_url = unquote(item['img_url'])
            async with aiohttp.ClientSession() as session:
                async with session.get(decoded_url) as response:
                    image_data = await response.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    decoded_url = f"data:image/jpeg;base64,{base64_data}"

            img_title = item['title'] 
            img_dict["img_url"] = decoded_url

            img_dict["img_title"] = img_title
            img_dict["quantity"] = item['quantity']
            img_dict["price"] = 225 * int(item['quantity'])
            img_data_list.append(img_dict)
    else:
        for item in img_quant_list:
            img_dict = {}
            decoded_url = unquote(item['img_url']) 
            async with aiohttp.ClientSession() as session:
                async with session.get(decoded_url) as response:
                    image_data = await response.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    decoded_url = f"data:image/jpeg;base64,{base64_data}"
            img_title = item['title'] 
            img_dict["img_url"] = decoded_url
            img_dict["img_title"] = img_title
            img_dict["quantity"] = item['quantity']
            img_dict["price"] = 225 * int(item['quantity'])
            img_data_list.append(img_dict)


    context = {
        "img_data_list": img_data_list,
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url,
        "brig_logo_url": brig_logo_url,
    }

    return templates.TemplateResponse(
        request=request, name="shop_art.html", context=context
    )

@app.get("/shop_art_menu", response_class=HTMLResponse)
async def shop_art_menu(request: Request):

    imgs, titles = get_nocodb_img_data()
    icons = get_nocodb_icon_data()

    shopping_cart_url = f"{http}://" + f"{site}/hostedimage/shopping_cart" 
    hamburger_menu_url = f"{http}://" + f"{site}/hostedimage/menu_burger" 
    brig_logo_url = f"{http}://" + f"{site}/hostedimage/brigLogo" 
    temp_vars = [f"{http}://" + f"{site}/hostedimage/" + title.replace(" ", "+") for title in titles]
    data_uris = []
    for url in temp_vars:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                image_data = await response.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                data_uri = f"data:image/jpeg;base64,{base64_data}"
                data_uris.append(data_uri)

    artwork_data = zip(titles, data_uris)
    context = {
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url, 
        "brig_logo_url": brig_logo_url,
        "artwork_data": artwork_data,
        }
    
    return templates.TemplateResponse(request = request,
                                      name = "shop_art_menu.html",
                                      context = context)

@app.get("/giclee_prints", response_class=HTMLResponse)
async def shop_giclee_prints(request: Request):


    icons = get_nocodb_icon_data()

    # Refresh the shopping cart because IMG URls change


    shopping_cart_url = f"{http}://" + f"{site}/hostedimage/shopping_cart" 
    hamburger_menu_url = f"{http}://" + f"{site}/hostedimage/menu_burger" 
    brig_logo_url = f"{http}://" + f"{site}/hostedimage/brigLogo" 

    context = {
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url, 
        "brig_logo_url": brig_logo_url
        }
    return templates.TemplateResponse(request = request,
                                      name = "gicle_prints.html",
                                      context = context)

class Title(BaseModel):
    title: str
            
@app.post("/increase_quantity")
async def increase_quantity(request: Request, title: Title):

    title = title.title
    match = False
    nocodb_data = get_nocodb_data()
    loaded_nocodb_data = json.loads(nocodb_data)
    for item in loaded_nocodb_data['list']:
        title = title.replace(" ", "+")
        if item['img_label'] == title:
            db_path = item['img'][0]['signedPath']
            url_path = f"{http}://" + f"{site}/hostedimage/" + title.replace(" ", "+")
            request.session["img_url"] = url_path
            request.session["title"] = title.replace("+", " ")
            match = True
    if match == True:

        img_quantity_list = request.session.get("img_quantity_list")
        img_url = url_path
        

        # Parse over img_quantity_list and increase the quantity of the item
        
        for each_url in img_quantity_list:
            if each_url["img_url"] == img_url:
                each_url["quantity"] = str(int(each_url["quantity"]) + 1)
                request.session["img_quantity_list"] = img_quantity_list
                total_quantity = sum(int(item["quantity"]) for item in img_quantity_list)
                print(request.session["img_quantity_list"])
                return JSONResponse({"quantity": total_quantity})
        
        
        
    else:
        raise(HTTPException(status_code=400, detail="Invalid URL in Increase Quantity Request"))


@app.post("/decrease_quantity")
async def decrease_quantity(request: Request, title: Title):
    title = title.title
    match = False
    nocodb_data = get_nocodb_data()
    loaded_nocodb_data = json.loads(nocodb_data)
    for item in loaded_nocodb_data['list']:
        title = title.replace(" ", "+")
        if item['img_label'] == title:
            db_path = item['img'][0]['signedPath']
            url_path = f"{http}://" + f"{site}/hostedimage/" + title.replace(" ", "+")
            request.session["img_url"] = url_path
            request.session["title"] = title.replace("+", " ")
            match = True
    if match == True:

        img_quantity_list = request.session.get("img_quantity_list")
        img_url = url_path
        # Parse over img_quantity_list and increase the quantity of the item

        for each_url in img_quantity_list:
            if each_url["img_url"] == img_url:
                each_url["quantity"] = str(int(each_url["quantity"]) - 1)
                break
    else:
        raise(HTTPException(status_code=400, detail="Invalid URL in Decrease Quantity Request"))

@app.post("/delete_item")
async def delete_item(request: Request, title : Title):
    # find the item attatched ot the url and delete the item
    title = title.title
    match = False
    nocodb_data = get_nocodb_data()
    loaded_nocodb_data = json.loads(nocodb_data)
    for item in loaded_nocodb_data['list']:
        title = title.replace(" ", "+")
        if item['img_label'] == title:
            db_path = item['img'][0]['signedPath']
            url_path = f"{http}://" + f"{site}/hostedimage/" + title.replace(" ", "+")
            request.session["img_url"] = url_path
            request.session["title"] = title.replace("+", " ")
            match = True
    if match == True:

        img_quantity_list = request.session.get("img_quantity_list")
        img_url = url_path

        for item in img_quantity_list:
            if item["img_url"] == img_url:
                img_quantity_list.remove(item)
            
                break
    else:
        raise(HTTPException(status_code=400, detail="Invalid URL in Delete Item Request"))

@app.get("/get_cart_quantity")
async def get_cart_quantity(request: Request):

    img_quantity_list = request.session.get("img_quantity_list")

    if img_quantity_list is None:
        return JSONResponse({"quantity": 0})
    else:
        total_quantity = sum(int(item['quantity']) for item in img_quantity_list)
        
    return JSONResponse({"quantity": total_quantity})

@app.get("/checkout", response_class=HTMLResponse)
async def shop_checkout(request: Request):

    icons = get_nocodb_icon_data()

    # Refresh the shopping cart because IMG URls change


    shopping_cart_url = f"{http}://" + f"{site}/hostedimage/shopping_cart" 
    hamburger_menu_url = f"{http}://" + f"{site}/hostedimage/menu_burger" 
    brig_logo_url = f"{http}://" + f"{site}/hostedimage/brigLogo" 

    img_quant_list = request.session.get("img_quantity_list")

    img_data_list = []

    if img_quant_list is None or []:
        img_quant_list = []
        for item in img_quant_list:
            img_dict = {}
            decoded_url = unquote(item['img_url'])
            async with aiohttp.ClientSession() as session:
                async with session.get(decoded_url) as response:
                    image_data = await response.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    decoded_url = f"data:image/jpeg;base64,{base64_data}"

            img_title = item['title'] 
            img_dict["img_url"] = decoded_url
            img_dict["img_title"] = img_title
            img_dict["quantity"] = item['quantity']
            img_dict["price"] = 225 * int(item['quantity'])
            img_data_list.append(img_dict)
    else:
        for item in img_quant_list:
            img_dict = {}
            decoded_url = unquote(item['img_url']) 
            async with aiohttp.ClientSession() as session:
                async with session.get(decoded_url) as response:
                    image_data = await response.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    decoded_url = f"data:image/jpeg;base64,{base64_data}"

            img_title = item['title'] 
            img_dict["img_url"] = decoded_url
            img_dict["img_title"] = img_title
            img_dict["quantity"] = item['quantity']
            img_dict["price"] = 225 * int(item['quantity'])
            img_data_list.append(img_dict)

    total_quantity = sum(int(item['quantity']) for item in img_quant_list)
    total_price = 225 * total_quantity
    context = {
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url, 
        "brig_logo_url": brig_logo_url,
        "total_price": total_price,
        "items": img_quant_list,
        "img_data_list": img_data_list,
        }

    return templates.TemplateResponse(request = request,
                                      name = "checkout.html",
                                      context = context)

# @app.post("/sign_up")
# async def sign_up(request: Request):


@app.post("/subscribe")
async def subscribe(request: Request):

    json_body = await request.json()



    print(json_body)
    
# def validate_address(
#     full_name : str,
#     street: str,
#     street2: str,
#     city: str,
#     state: str,
#     zipcode: str,
#     candidates: int,
# ):
#     # for server-to-server requests, use this code:
#     auth_id = smarty_auth_id
#     auth_token = smarty_auth_token
    
#     credentials = StaticCredentials(auth_id, auth_token)


#     client = ClientBuilder(credentials).with_licenses(["us-core-cloud"]).build_us_street_api_client()


#     lookup = StreetLookup()
#     lookup.addressee = full_name
#     lookup.street = street
#     # lookup.street2 = "closet under the stairs"
#     # lookup.secondary = "APT 2"
#     # lookup.urbanization = ""  # Only applies to Puerto Rico addresses
#     lookup.city = city
#     lookup.state = state
#     lookup.zipcode = zipcode
#     lookup.candidates = 3
#     lookup.match = MatchType.INVALID  # "invalid" is the most permissive match,
#                                       # this will always return at least one result even if the address is invalid.
#                                       # Refer to the documentation for additional Match Strategy options.

#     try:
#         client.send_lookup(lookup)
#     except exceptions.SmartyException as err:
#         print(err)
#         return

#     result = lookup.result

#     if not result:
#         print("No candidates. This means the address is not valid.")
#         return

#     print("Show Address")
#     for c, candidate in enumerate(lookup.result):
#         print(f"Candidate {c} is:")
#         print(candidate.delivery_line_1)
#         print(candidate.last_line)
#         print()
# @app.post("/process_payment")
# async def process_checkout(request: Request, order_info: OrderInfo):
#     # Validate inputs
#     validation_errors = validate_inputs(order_info)
#     print(order_info)

#     validate_address(
#         full_name = order_info.fullname,
#         street = order_info.address1,
#         street2 = order_info.address2,
#         city = order_info.city,
#         state = order_info.state,
#         zipcode = order_info.zip,
#         candidates = 3
#     )

#     if validation_errors:
#         return {"error": validation_errors}

#     # If all inputs are valid, process the payment
#     # If the payment is successful, send an email to the user

#     return {"message": "Payment processed successfully"}

    # Validate all inputs

# Take in an image and apply the watermark, swap that image with the image intended for swap
@app.post("/swap_image")
async def swap_image(title: str = Form(...), new_title: str = Form(...), file: UploadFile = File(...)):
    # Get the record ID by matching the title
    nocodb_upload_url = f"{nocodb_path}api/v2/storage/upload"
    response_object = json.loads(get_nocodb_data())  # Assume this function gets the data correctly

    id = None
    for item in response_object['list']:
        if item['img'] and len(item['img']) > 0:
            title_check = item["img_label"].replace("+", " ").lower()
            if title.lower() in title_check:
                id = item["Id"]
                break

    if not id:
        return {"message": "Image not found"}

    # Upload new image
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".PNG", delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(await file.read())
            temp_file.flush()

        # For Watermarking Feature
        # watermarked_img, watermarked_path = get_watermark(temp_file_path, title)
        # get_watermark(temp_file_path, title)

        with open(temp_file_path, "rb") as f:

            files_to_upload = {
                "file": f
            }
            headers = {
                'xc-token': xc_auth
            }
            path = os.path.basename(temp_file_path)
            
            upload_response = requests.post(nocodb_upload_url, headers=headers, files=files_to_upload, params={"path": path})

            if upload_response.status_code == 200:
                data = upload_response.json()
                # Assume data is a list of dictionaries
                new_file_info = data[0]  # Access the first item in the list
                new_file_path = new_file_info.get('path')
                new_signed_path = new_file_info.get('signedPath')
                print(upload_response.json())
            else:
                return {"message": "Failed to upload file"}

            # Update record with new image path
            
            new_title = new_title.replace(" ", "+")
            title = new_title + ".png"
            update_data = {
                "Id": id,
                "img_label": new_title,
                "img": [
                    {
                        "title": title,
                        "mimetype": file.content_type,
                        "path": new_file_path,
                        "signedPath": new_signed_path
                    }
                ]
            }
            update_headers = {
                'accept': 'application/json',
                'xc-token': xc_auth,
                'Content-Type': 'application/json'
            }
            data = json.dumps(update_data)
            update_response = requests.patch(nocodb_img_update_url, headers=update_headers, data=data)

            if update_response.status_code == 200:
                return {"message": "Image swapped successfully"}
            else:
                return {"message": f"Failed to update record"}
    except:
        return {"message": "Image not swapped successfully"}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        

@app.get("/portal", response_class=HTMLResponse)
async def portal(request: Request):

    icons = get_nocodb_icon_data()

    brig_logo_url = f"{http}://" + f"{site}/hostedimage/brigLogo" 

    context = {
        "brig_logo_url": brig_logo_url,
    }
    return templates.TemplateResponse(request=request,
                                      name="login.html",
                                      context=context)

@app.post("/credentials_check")
async def credentials_check(request: Request, credentials: Credentials):
    if credentials.username == brig_username and credentials.password == brig_password:
        request.session['logged_in'] = True
        return RedirectResponse(url='/brig_portal', status_code=303)
    else:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.get("/brig_portal", response_class=HTMLResponse)
async def brig_portal(request: Request):
    if not request.session.get('logged_in'):
        return RedirectResponse(url='/portal')
    
    icons = get_nocodb_icon_data()
    brig_logo_url = nocodb_path + icons[2]
    context = {"brig_logo_url": brig_logo_url}
    return templates.TemplateResponse(request=request,
                                      name="brig_portal.html",
                                      context=context)

# Take in an image and apply the watermark, then add to the img database
@app.post("/add_images")
async def add_images(titles: List[str] = Form(...), files: List[UploadFile] = File(...)):
    if len(titles) != len(files):
        return {"message": "Number of titles doesn't match number of files"}

    return_list = []
    temp_file_paths = []

    try:
        for title, file in zip(titles, files):
            # Get the record ID by matching the title
            nocodb_upload_url = f"{nocodb_path}api/v2/storage/upload"
            response_object = json.loads(get_nocodb_data())  # Assume this function gets the data correctly

            # Get the last ID in the list and increment by 1
            try:
                id = response_object['list'][-1]['Id'] + 1
            except IndexError:
                id = 1

            with tempfile.NamedTemporaryFile(suffix=".PNG", delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file_paths.append(temp_file_path)
                temp_file.write(await file.read())
                temp_file.flush()

            # Watermarked feature
            # watermarked_img, watermarked_path = get_watermark(temp_file_path, title)
            with open(temp_file_path, "rb") as f:
            # get_watermark(temp_file_path, title)
                files_to_upload = {
                    "file": f
                }
                headers = {
                    'xc-token': xc_auth
                }
                path = os.path.basename(temp_file_path)
                upload_response = requests.post(nocodb_upload_url, headers=headers, files=files_to_upload, params={"path": path})
                if upload_response.status_code == 200:
                    data = upload_response.json()
                    print(data)
                    # Assume data is a list of dictionaries
                    new_file_info = data[0]  # Access the first item in the list
                    new_file_path = new_file_info.get('path')
                    new_signed_path = new_file_info.get('signedPath')
                else:
                    return {"message": "Failed to upload file"}

            # Update record with new image path
            
                new_title = title.replace(" ", "+")
                title = new_title + ".png"
                update_data = {
                    "Id": id,
                    "img_label": new_title,
                    "img": [
                        {
                            "title": title,
                            "mimetype": file.content_type,
                            "path": new_file_path,
                            "signedPath": new_signed_path
                        }
                    ]
                }
                update_headers = {
                    'accept': 'application/json',
                    'xc-token': xc_auth,
                    'Content-Type': 'application/json'
                }
                data = json.dumps(update_data)
                update_response = requests.post(nocodb_img_update_url, headers=update_headers, data=data)

                if update_response.status_code == 200:
                    return_message = {"message": "Image(s) added successfully"}
                    return_list.append(return_message)
                else:
                    return {"message": "Failed to update record"}
    except:
        return {"message": "Image not swapped successfully"}
    finally:
        for each in temp_file_paths:
            if each and os.path.exists(each):
                os.remove(each)
        return return_list[0]
    
@app.get("/hostedimage/{title}", response_class=HTMLResponse)
async def hosted_image(request: Request, title: str):
    file_path = os.path.join(temp_dir.name, f"{title}.png")

    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Image not found")


    
# Development Server
# Run the app
if __name__ == "__main__" and scene == "dev":
    uvicorn.run(app = "main:app",
                host = host, 
                port = int(port),
                reload= True)
    