from fastapi import FastAPI, Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
import uvicorn
import json
import dotenv
import os
import requests
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
import json
from urllib.parse import unquote


class Url(BaseModel):
    url: str
    title1: str

class UrlQuantity(BaseModel):
    url: str
    quantity: str
    title2 : str

# Define FastAPI App

desc = "Backend platform for BRIG ART"
app = FastAPI(
    title = "Brig API",
    description= desc
)
app.add_middleware(SessionMiddleware, secret_key="some-random-string")

# Mount StaticFiles instance to serve files from the "src" directory
# app.mount("/", StaticFiles(directory="src", html=True), name="src")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="src/templates")
# Define API Key Header
api_key_header = APIKeyHeader(name = 'X-API_KEY')

# Load NocDB env variables from .env file
dotenv.load_dotenv()
nocodb_key_url = str(os.getenv("key_url"))
nocodb_img_url = str(os.getenv("img_url"))
nocodb_icon_url = str(os.getenv("icon_url"))
xc_auth = str(os.getenv("xc_auth"))
nocodb_path = str(os.getenv("nocodb_path"))

# Define Security Scheme
def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
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

def refresh_shop_cart(request: Request):
    
    img_quant_list = request.session.get("img_quantity_list")
    imgs, titles = get_nocodb_img_data()

    if img_quant_list is None:
        img_quant_list = []
    for each_url in img_quant_list:
        for title in titles:
            if each_url["title"] == title:
                correct_link = imgs[titles.index(title)]
                host_string = f"http://{site_host}/{correct_link}"
                each_url["img_url"] = host_string
                request.session["img_quantity_list"] = img_quant_list


@app.middleware("http")
async def some_middleware(request: Request, call_next):
    response = await call_next(request)

    # No need to manually handle session cookies here
    return response

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):

    print("The pod has been sucessfully updated")

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

    request.session["img_url"] = url.url
    request.session["title"] = url.title1

    return url

@app.get("/shop", response_class=HTMLResponse)
async def shop(request: Request):
 
    img_url = request.session.get("img_url")
    img_title = request.session.get("title")
    icons = get_nocodb_icon_data()
    # Refresh the shopping cart because IMG URls change


    shopping_cart_url = nocodb_path + icons[0]
    hamburger_menu_url = nocodb_path + icons[1]
    brig_logo_url = nocodb_path + icons[2]

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
                break
        else:
            request.session["img_quantity_list"].append(quant_img_dict)
    


    return {"status_code": "200"}



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
async def shop(request: Request):

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
async def shop(request: Request):


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


    img_quantity_list = request.session.get("img_quantity_list")
    img_url = url.url
    title = url.title1
    # Parse over img_quantity_list and increase the quantity of the item

    for each_url in img_quantity_list:
        if each_url["img_url"] == img_url:
            each_url["quantity"] = str(int(each_url["quantity"]) + 1)
            break
    return {"status_code": 200, "message": "Quantity increased successfully"}

@app.post("/decrease_quantity")
async def decrease_quantity(request: Request, url: Url):


    img_quantity_list = request.session.get("img_quantity_list")
    img_url = url.url
    # Parse over img_quantity_list and increase the quantity of the item

    for each_url in img_quantity_list:
        if each_url["img_url"] == img_url:
            each_url["quantity"] = str(int(each_url["quantity"]) - 1)
            break

    return {"status_code": 200, "message": "Quantity increased successfully"}

@app.post("/delete_item")
async def delete_item(request: Request, url: Url):
    # find the item attatched ot the url and delete the item

    img_quantity_list = request.session.get("img_quantity_list")
    img_url = url.url

    for item in img_quantity_list:
        if item["img_url"] == img_url:
            img_quantity_list.remove(item)
            break
    print(img_quantity_list)
    return "item removed"
    # return JSONResponse(status_code=200, content={"message": "Item deleted successfully"})

@app.get("/get_cart_quantity")
async def get_cart_quantity(request: Request):



    img_quantity_list = request.session.get("img_quantity_list")

    if img_quantity_list is None:
        return JSONResponse({"quantity": 0})
    
    total_quantity = sum(int(item['quantity']) for item in img_quantity_list)
    return JSONResponse({"quantity": total_quantity})

@app.get("/checkout", response_class=HTMLResponse)
async def shop(request: Request):

    icons = get_nocodb_icon_data()

    # Refresh the shopping cart because IMG URls change


    shopping_cart_url = nocodb_path + icons[0]
    hamburger_menu_url = nocodb_path + icons[1]
    brig_logo_url = nocodb_path + icons[2]

    img_quant_list = request.session.get("img_quantity_list")
    print(img_quant_list)
    total_quantity = sum(int(item['quantity']) for item in img_quant_list)
    total_price = 225 * total_quantity

    context = {
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url, 
        "brig_logo_url": brig_logo_url,
        "total_price": total_price,
        }

    return templates.TemplateResponse(request = request,
                                      name = "checkout.html",
                                      context = context)

# @app.post("/sign_up")
# async def sign_up(request: Request):

@app.post("/subscribe")
async def subscribe(request: Request):

    refresh_shop_cart(request)

    json_body = await request.json()

    print(json_body)



@app.post("/process_payment")
async def process_checkout(request: Request):

    try:
        # Placeholder for your processing logic
        # For demonstration, let's assume the payment is processed successfully
        # You can replace this with your actual payment processing logic

        json_body = await request.json()

        # Check if payment processing was successful (you can add your own conditions here)
        if payment_processed_successfully(json_body):
            return {"payment_processed": True, "message": "Payment processed successfully."}
        else:
            # If payment processing failed
            raise HTTPException(status_code=400, detail="Payment processing failed.")
    except Exception as e:
        # Handle any exceptions that may occur during payment processing
        print(f"Error processing payment: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def payment_processed_successfully(payment_data):
    # Simulate payment processing success based on some conditions
    # Here you can define your own conditions to determine if the payment was successful
    # For demonstration, let's assume payment is successful if card_number is even
    # card_number = payment_data.get("card_number", "")
    # if card_number.isdigit() and int(card_number) % 2 == 0:
    #     return True
    # else:
    #     return False
    print(payment_data)
    return True



# Run the app
if __name__ == "__main__":
    uvicorn.run(app = "main:app",
                host = host, 
                port = int(port), 
                http = "auto"
                reload= True)