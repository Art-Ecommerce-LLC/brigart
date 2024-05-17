from fastapi import FastAPI, Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
import uvicorn
import json
import dotenv
import os
import requests
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.sessions import SessionMiddleware
import json
from urllib.parse import unquote
import urllib3
import re
from smartystreets_python_sdk import SharedCredentials, StaticCredentials, exceptions, ClientBuilder
from smartystreets_python_sdk.us_street import Lookup as StreetLookup
from smartystreets_python_sdk.us_street.match_type import MatchType
from typing import Annotated, List
import tempfile
import shutil

urllib3.disable_warnings()



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
            title = item["img"][0]["title"]
            title_strip = title.split(".")[-3]
            title_replace = title_strip.split("_")[-1]
            title_replace = title_replace.replace("+", " ")

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


    shopping_cart_url = nocodb_path + icons[0]
    hamburger_menu_url = nocodb_path + icons[1]
    brig_logo_url = nocodb_path + icons[2]
    temp_vars = [nocodb_path + each for each in imgs]

    zipped_imgs_titles = zip(temp_vars, titles)


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
async def shop(request: Request, title):
 
    
    icons = get_nocodb_icon_data()
    # Refresh the shopping cart because IMG URls change
    print(title)
    # Find the img url associate with the title and store both in the session
    nocodb_data = get_nocodb_data()
    loaded_nocodb_data = json.loads(nocodb_data)
    for item in loaded_nocodb_data['list']:
        if item['img_label'] == title:
            db_path = item['img'][0]['signedPath']
            url_path = f"{http}://" + f"{site_host}/" + db_path
            request.session["img_url"] = url_path
            request.session["title"] = title.replace("+", " ")

    shopping_cart_url = nocodb_path + icons[0]
    hamburger_menu_url = nocodb_path + icons[1]
    brig_logo_url = nocodb_path + icons[2]
    img_url = request.session.get("img_url")
    img_title = request.session.get("title")

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
    for item in imgs:
        url_string = f"{http}://" + f"{site_host}/" + item
        if url_string == url_quant.url:
            match = True

    if match == True:
        img_url = url_quant.url
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


@app.get("/shop_art", response_class=HTMLResponse)
async def shop_art(request: Request):
    
    refresh_shop_cart(request)

    img_quant_list = request.session.get("img_quantity_list")

    icons = get_nocodb_icon_data()

    # Refresh the shopping cart because IMG URls change


    shopping_cart_url = nocodb_path + icons[0]
    hamburger_menu_url = nocodb_path + icons[1]
    brig_logo_url = nocodb_path + icons[2]

    img_data_list = []

    if img_quant_list is None or []:
        img_quant_list = []
        for item in img_quant_list:
            img_dict = {}
            decoded_url = unquote(item['img_url'])
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

    shopping_cart_url = nocodb_path + icons[0]
    hamburger_menu_url = nocodb_path + icons[1]
    brig_logo_url = nocodb_path + icons[2]
    temp_vars = [nocodb_path + each for each in imgs]

    artwork_data = zip(titles, temp_vars)
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


    shopping_cart_url = nocodb_path + icons[0]
    hamburger_menu_url = nocodb_path + icons[1]
    brig_logo_url = nocodb_path + icons[2]

    context = {
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url, 
        "brig_logo_url": brig_logo_url
        }
    return templates.TemplateResponse(request = request,
                                      name = "gicle_prints.html",
                                      context = context)

            
@app.post("/increase_quantity")
async def increase_quantity(request: Request, url:Url):

    imgs,titles = get_nocodb_img_data()

    match = False
    for item in imgs:
        url_string = f"{http}://" + f"{site_host}/" + item
        if url.url == url_string:
            match = True
    
    if match == True:

        img_quantity_list = request.session.get("img_quantity_list")
        img_url = url.url
        

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
async def decrease_quantity(request: Request, url: Url):

    imgs,titles = get_nocodb_img_data()

    match = False
    for item in imgs:
        url_string = f"{http}://" + f"{site_host}/" + item
        if url.url == url_string:
            match = True
    
    if match == True:
        img_quantity_list = request.session.get("img_quantity_list")
        img_url = url.url
        # Parse over img_quantity_list and increase the quantity of the item

        for each_url in img_quantity_list:
            if each_url["img_url"] == img_url:
                each_url["quantity"] = str(int(each_url["quantity"]) - 1)
                break
    else:
        raise(HTTPException(status_code=400, detail="Invalid URL in Decrease Quantity Request"))

@app.post("/delete_item")
async def delete_item(request: Request, url: Url):
    # find the item attatched ot the url and delete the item

    imgs, titles = get_nocodb_img_data()

    match = False
    for item in imgs:
        url_string = f"{http}://" + f"{site_host}/" + item
        if url.url == url_string:
            match = True
    
    if match == True:
        img_quantity_list = request.session.get("img_quantity_list")
        img_url = url.url

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

    refresh_shop_cart(request)


    icons = get_nocodb_icon_data()

    # Refresh the shopping cart because IMG URls change


    shopping_cart_url = nocodb_path + icons[0]
    hamburger_menu_url = nocodb_path + icons[1]
    brig_logo_url = nocodb_path + icons[2]

    img_quant_list = request.session.get("img_quantity_list")

    img_data_list = []

    if img_quant_list is None or []:
        img_quant_list = []
        for item in img_quant_list:
            img_dict = {}
            decoded_url = unquote(item['img_url'])
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
    
def validate_address(
    full_name : str,
    street: str,
    street2: str,
    city: str,
    state: str,
    zipcode: str,
    candidates: int,
):
    # for server-to-server requests, use this code:
    auth_id = smarty_auth_id
    auth_token = smarty_auth_token
    
    credentials = StaticCredentials(auth_id, auth_token)


    client = ClientBuilder(credentials).with_licenses(["us-core-cloud"]).build_us_street_api_client()


    lookup = StreetLookup()
    lookup.addressee = full_name
    lookup.street = street
    # lookup.street2 = "closet under the stairs"
    # lookup.secondary = "APT 2"
    # lookup.urbanization = ""  # Only applies to Puerto Rico addresses
    lookup.city = city
    lookup.state = state
    lookup.zipcode = zipcode
    lookup.candidates = 3
    lookup.match = MatchType.INVALID  # "invalid" is the most permissive match,
                                      # this will always return at least one result even if the address is invalid.
                                      # Refer to the documentation for additional Match Strategy options.

    try:
        client.send_lookup(lookup)
    except exceptions.SmartyException as err:
        print(err)
        return

    result = lookup.result

    if not result:
        print("No candidates. This means the address is not valid.")
        return

    print("Show Address")
    for c, candidate in enumerate(lookup.result):
        print(f"Candidate {c} is:")
        print(candidate.delivery_line_1)
        print(candidate.last_line)
        print()
@app.post("/process_payment")
async def process_checkout(request: Request, order_info: OrderInfo):
    # Validate inputs
    validation_errors = validate_inputs(order_info)
    print(order_info)

    validate_address(
        full_name = order_info.fullname,
        street = order_info.address1,
        street2 = order_info.address2,
        city = order_info.city,
        state = order_info.state,
        zipcode = order_info.zip,
        candidates = 3
    )

    if validation_errors:
        return {"error": validation_errors}

    # If all inputs are valid, process the payment
    # If the payment is successful, send an email to the user

    return {"message": "Payment processed successfully"}

    # Validate all inputs

# Take in an image and apply the watermark, swap that image with the image intended for swap
@app.post("/swap_image")
async def swap_image(title: str, new_title: str, file: UploadFile):
    # Get the record ID by matching the title
    nocodb_upload_url = f"{nocodb_path}api/v2/storage/upload"
    response_object = json.loads(get_nocodb_data())  # Assume this function gets the data correctly
    print(title)

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

        with open(temp_file_path, "rb") as temp_file:
            files_to_upload = {
                "file": temp_file
            }
            headers = {
                'xc-token': xc_auth
            }
            path = os.path.basename(temp_file.name)
            print(path)
            upload_response = requests.post(nocodb_upload_url, headers=headers, files=files_to_upload, params={"path": path})
            print(upload_response)
            if upload_response.status_code == 200:
                data = upload_response.json()
                # Assume data is a list of dictionaries
                new_file_info = data[0]  # Access the first item in the list
                new_file_path = new_file_info.get('path')
                new_signed_path = new_file_info.get('signedPath')
                print(new_file_info)
            else:
                return {"message": f"Failed to upload file: {upload_response.status_code} - {upload_response.text}"}

            # Update record with new image path
            
            new_title = new_title.replace(" ", "+")
            title = "watermarked_" + new_title + ".PNG" + ".png"
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
            print(json.dumps(update_data, indent=4))
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
                return {"message": f"Failed to update record: {update_response.status_code} - {update_response.text}"}
    except Exception as e:
        print(e)
        return {"message": "Image not swapped successfully"}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# @app.get("/portal")
# async def portal(request: Request):
#     return {"message": "Welcome to the portal"}
# # Take in an image and apply the watermark, then add to the img database
# @app.post("/add_image")
# async def add_image(request: Request, title, files: Annotated[list[bytes], File(description="Multiple files as bytes")]):
#     # Put the image in the database
#     return {"message": "Image added successfully"}


    
# Development Server
# Run the app
if __name__ == "__main__" and scene == "dev":
    uvicorn.run(app = "main:app",
                host = host, 
                port = int(port),
                reload= True)