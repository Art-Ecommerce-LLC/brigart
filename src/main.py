# app/main.py
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Security, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from config import NOCODB_PATH, NOCODB_IMG_UPDATE_URL, XC_AUTH
from logger import logger
from middleware import add_middleware
from models import Url, UrlQuantity, OrderInfo, Credentials, Title
from utils import lifespan, cleancart, scale_image, temp_dir
from noco import (
    get_nocodb_img_data, get_nocodb_data, get_nocodb_icon_data, HTTP, BRIG_PASSWORD, BRIG_USERNAME, OPENAPI_URL, SCENE, SITE, BEN_USERNAME, BEN_PASSWORD, SITE_HOST
)
from logger import get_logs
import requests
import base64
import aiohttp
import json
from urllib.parse import unquote
import tempfile
import os
from typing import List
from PIL import Image
from io import BytesIO
import uvicorn

# Initialize FastAPI App
desc = "Backend platform for BRIG ART"

if OPENAPI_URL == "None":
    OPENAPI_URL = None

app = FastAPI(
    title="Brig API",
    description=desc,
    openapi_url=OPENAPI_URL,
    lifespan=lifespan
)

# Middleware
add_middleware(app)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# Icon URLs
shopping_cart_url = f"{HTTP}://{SITE}/hostedimage/shopping_cart"
hamburger_menu_url = f"{HTTP}://{SITE}/hostedimage/menu_burger"
brig_logo_url = f"{HTTP}://{SITE}/hostedimage/brigLogo"

# Routes
def convert_to_data_uri(image_data: bytes) -> str:
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_data}"

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    logger.info(f"Homepage accessed by: {request.client.host}")
    try:
        imgs, titles = get_nocodb_img_data()
        temp_vars = [f"{HTTP}://{SITE}/hostedimage/{title.replace(' ', '+')}" for title in titles]
        data_uris = []
        async with aiohttp.ClientSession() as session:
            for url in temp_vars:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        data_uri = convert_to_data_uri(image_data)
                        data_uris.append(data_uri)
                    else:
                        logger.error(f"Failed to fetch image from {url}, status code: {response.status}")
        zipped_imgs_titles = zip(data_uris, titles)
        context = {
            "shopping_cart_url": shopping_cart_url,
            "hamburger_menu_url": hamburger_menu_url,
            "brig_logo_url": brig_logo_url,
            "temp_vars": zipped_imgs_titles,
        }
        return templates.TemplateResponse(request=request, name="index.html", context=context)
    except Exception as e:
        logger.error(f"Error in homepage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/shop")
async def shop_img_url(request: Request, url: Url):
    logger.info(f"Shop URL accessed with {url.url} at {request.client.host}")
    try:
        imgs, titles = get_nocodb_img_data()
        match = False
        for item in imgs:
            url_string = f"{HTTP}://{SITE_HOST}/{item}"
            if url.url == url_string:
                match = True
                break
        if match:
            request.session["img_url"] = url.url
            request.session["title"] = url.title1
        else:
            logger.warning(f"Invalid URL in Shop Request: {url.url}")
            raise HTTPException(status_code=400, detail="Invalid URL in Shop Request")
    except Exception as e:
        logger.error(f"Error in shop_img_url: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop/{title}", response_class=HTMLResponse)
async def shop(request: Request, title: str):
    logger.info(f"Shop page accessed for title {title} by {request.client.host}")
    try:
        nocodb_data = get_nocodb_data()
        loaded_nocodb_data = json.loads(nocodb_data)
        for item in loaded_nocodb_data['list']:
            if item['img_label'] == title:
                url_path = f"{HTTP}://{SITE}/hostedimage/{title.replace(' ', '+')}"
                request.session["img_url"] = url_path
                request.session["title"] = title.replace("+", " ")
                break
        img_url = request.session.get("img_url")
        img_title = request.session.get("title")
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    img_url = convert_to_data_uri(image_data)
                else:
                    logger.error(f"Failed to fetch image for {title}, status code: {response.status}")
                    raise HTTPException(status_code=404, detail="Image not found")
        context = {
            "img_url": img_url,
            "img_title": img_title,
            "shopping_cart_url": shopping_cart_url,
            "hamburger_menu_url": hamburger_menu_url,
            "brig_logo_url": brig_logo_url
        }
        return templates.TemplateResponse(request=request, name="shop.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/shop_art")
async def shop_art_url(request: Request, url_quant: UrlQuantity):
    logger.info(f"Shop art URL accessed for title {url_quant.title2} with quantity {url_quant.quantity} by {request.client.host}")
    try:
        match = False
        nocodb_data = get_nocodb_data()
        loaded_nocodb_data = json.loads(nocodb_data)
        for item in loaded_nocodb_data['list']:
            title = url_quant.title2.replace(" ", "+")
            if item['img_label'] == title:
                url_path = f"{HTTP}://{SITE}/hostedimage/{title.replace(' ', '+')}"
                request.session["img_url"] = url_path
                request.session["title"] = title.replace("+", " ")
                match = True
                break
        if match:
            img_url = url_path
            quantity = url_quant.quantity
            title = url_quant.title2
            img_quantity_list = request.session.get("img_quantity_list", [])
            quant_img_dict = {
                "img_url": img_url,
                "quantity": quantity,
                "title": title
            }
            for each_item in img_quantity_list:
                if title == each_item["title"]:
                    new_quantity = int(each_item["quantity"]) + int(quantity)
                    each_item["quantity"] = new_quantity
                    break
            else:
                img_quantity_list.append(quant_img_dict)
            request.session["img_quantity_list"] = img_quantity_list
            logger.info(f"Added {quantity} of {title} to cart")
        else:
            logger.warning(f"Invalid URL in Shop_Art Request: {url_quant.title2}")
            raise HTTPException(status_code=400, detail="Invalid URL in Shop_Art Request")
    except Exception as e:
        logger.error(f"Error in shop_art_url: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop_art", response_class=HTMLResponse)
async def shop_art(request: Request):
    logger.info(f"Shop art page accessed by {request.client.host}")
    try:
        cleancart(request)
        img_quant_list = request.session.get("img_quantity_list", [])
        img_data_list = []
        async with aiohttp.ClientSession() as session:
            for item in img_quant_list:
                img_dict = {}
                decoded_url = unquote(item['img_url'])
                async with session.get(decoded_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        decoded_url = convert_to_data_uri(image_data)
                        img_title = item['title']
                        img_dict["img_url"] = decoded_url
                        img_dict["img_title"] = img_title
                        img_dict["quantity"] = item['quantity']
                        img_dict["price"] = 225 * int(item['quantity'])
                        img_data_list.append(img_dict)
                    else:
                        logger.error(f"Failed to fetch image for {item['title']}, status code: {response.status}")
        context = {
            "img_data_list": img_data_list,
            "shopping_cart_url": shopping_cart_url,
            "hamburger_menu_url": hamburger_menu_url,
            "brig_logo_url": brig_logo_url,
        }
        return templates.TemplateResponse(request=request, name="shop_art.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop_art_menu", response_class=HTMLResponse)
async def shop_art_menu(request: Request):
    logger.info(f"Shop art menu page accessed by {request.client.host}")
    try:
        imgs, titles = get_nocodb_img_data()
        temp_vars = [f"{HTTP}://{SITE}/hostedimage/{title.replace(' ', '+')}" for title in titles]
        data_uris = []
        async with aiohttp.ClientSession() as session:
            for url in temp_vars:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        data_uri = convert_to_data_uri(image_data)
                        data_uris.append(data_uri)
                    else:
                        logger.error(f"Failed to fetch image from {url}, status code: {response.status}")
        artwork_data = zip(titles, data_uris)
        context = {
            "shopping_cart_url": shopping_cart_url,
            "hamburger_menu_url": hamburger_menu_url,
            "brig_logo_url": brig_logo_url,
            "artwork_data": artwork_data,
        }
        return templates.TemplateResponse(request=request, name="shop_art_menu.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art_menu: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/giclee_prints", response_class=HTMLResponse)
async def shop_giclee_prints(request: Request):
    logger.info(f"Giclee prints page accessed by {request.client.host}")
    context = {
        "shopping_cart_url": shopping_cart_url,
        "hamburger_menu_url": hamburger_menu_url,
        "brig_logo_url": brig_logo_url
    }
    return templates.TemplateResponse(request=request, name="gicle_prints.html", context=context)

@app.post("/increase_quantity")
async def increase_quantity(request: Request, title: Title):
    logger.info(f"Increase quantity for {title.title} by {request.client.host}")
    try:
        title_str = title.title
        match = False
        nocodb_data = get_nocodb_data()
        loaded_nocodb_data = json.loads(nocodb_data)
        for item in loaded_nocodb_data['list']:
            title_str = title_str.replace(" ", "+")
            if item['img_label'] == title_str:
                url_path = f"{HTTP}://{SITE}/hostedimage/{title_str.replace(' ', '+')}"
                request.session["img_url"] = url_path
                request.session["title"] = title_str.replace("+", " ")
                match = True
                break
        if match:
            img_quantity_list = request.session.get("img_quantity_list")
            img_url = url_path
            for each_url in img_quantity_list:
                if each_url["img_url"] == img_url:
                    each_url["quantity"] = str(int(each_url["quantity"]) + 1)
                    request.session["img_quantity_list"] = img_quantity_list
                    total_quantity = sum(int(item["quantity"]) for item in img_quantity_list)
                    logger.info(f"Increased quantity for {title.title}, new quantity: {total_quantity}")
                    return JSONResponse({"quantity": total_quantity})
        else:
            logger.warning(f"Invalid URL in Increase Quantity Request: {title.title}")
            raise HTTPException(status_code=400, detail="Invalid URL in Increase Quantity Request")
    except Exception as e:
        logger.error(f"Error in increase_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/decrease_quantity")
async def decrease_quantity(request: Request, title: Title):
    logger.info(f"Decrease quantity for {title.title} by {request.client.host}")
    try:
        title_str = title.title
        match = False
        nocodb_data = get_nocodb_data()
        loaded_nocodb_data = json.loads(nocodb_data)
        for item in loaded_nocodb_data['list']:
            title_str = title_str.replace(" ", "+")
            if item['img_label'] == title_str:
                url_path = f"{HTTP}://{SITE}/hostedimage/{title_str.replace(' ', '+')}"
                request.session["img_url"] = url_path
                request.session["title"] = title_str.replace("+", " ")
                match = True
                break
        if match:
            img_quantity_list = request.session.get("img_quantity_list")
            img_url = url_path
            for each_url in img_quantity_list:
                if each_url["img_url"] == img_url:
                    each_url["quantity"] = str(int(each_url["quantity"]) - 1)
                    request.session["img_quantity_list"] = img_quantity_list
                    logger.info(f"Decreased quantity for {title.title}, new quantity: {each_url['quantity']}")
                    return JSONResponse({"quantity": each_url["quantity"]})
        else:
            logger.warning(f"Invalid URL in Decrease Quantity Request: {title.title}")
            raise HTTPException(status_code=400, detail="Invalid URL in Decrease Quantity Request")
    except Exception as e:
        logger.error(f"Error in decrease_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/delete_item")
async def delete_item(request: Request, title: Title):
    logger.info(f"Delete item {title.title} by {request.client.host}")
    try:
        title_str = title.title
        match = False
        nocodb_data = get_nocodb_data()
        loaded_nocodb_data = json.loads(nocodb_data)
        for item in loaded_nocodb_data['list']:
            title_str = title_str.replace(" ", "+")
            if item['img_label'] == title_str:
                url_path = f"{HTTP}://{SITE}/hostedimage/{title_str.replace(' ', '+')}"
                request.session["img_url"] = url_path
                request.session["title"] = title_str.replace("+", " ")
                match = True
                break
        if match:
            img_quantity_list = request.session.get("img_quantity_list")
            img_url = url_path
            for item in img_quantity_list:
                if item["img_url"] == img_url:
                    img_quantity_list.remove(item)
                    request.session["img_quantity_list"] = img_quantity_list
                    logger.info(f"Deleted item {title.title} from cart")
                    return JSONResponse({"message": "Item deleted"})
        else:
            logger.warning(f"Invalid URL in Delete Item Request: {title.title}")
            raise HTTPException(status_code=400, detail="Invalid URL in Delete Item Request")
    except Exception as e:
        logger.error(f"Error in delete_item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_cart_quantity")
async def get_cart_quantity(request: Request):
    logger.info(f"Get cart quantity by {request.client.host}")
    try:
        img_quantity_list = request.session.get("img_quantity_list", [])
        total_quantity = sum(int(item['quantity']) for item in img_quantity_list)
        logger.info(f"Total cart quantity: {total_quantity}")
        return JSONResponse({"quantity": total_quantity})
    except Exception as e:
        logger.error(f"Error in get_cart_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/checkout", response_class=HTMLResponse)
async def shop_checkout(request: Request):
    logger.info(f"Checkout page accessed by {request.client.host}")
    try:
        img_quant_list = request.session.get("img_quantity_list", [])
        img_data_list = []
        async with aiohttp.ClientSession() as session:
            for item in img_quant_list:
                img_dict = {}
                decoded_url = unquote(item['img_url'])
                async with session.get(decoded_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        decoded_url = convert_to_data_uri(image_data)
                        img_title = item['title']
                        img_dict["img_url"] = decoded_url
                        img_dict["img_title"] = img_title
                        img_dict["quantity"] = item['quantity']
                        img_dict["price"] = 225 * int(item['quantity'])
                        img_data_list.append(img_dict)
                    else:
                        logger.error(f"Failed to fetch image for {item['title']}, status code: {response.status}")
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
        return templates.TemplateResponse(request=request, name="checkout.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_checkout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/subscribe")
async def subscribe(request: Request):
    try:
        json_body = await request.json()
        logger.info(f"Received subscription request: {json_body}")
    except Exception as e:
        logger.error(f"Error in subscribe: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/swap_image")
async def swap_image(title: str = Form(...), new_title: str = Form(...), file: UploadFile = File(...)):
    logger.info(f"Swap image for {title} to {new_title} ")
    nocodb_upload_url = f"{NOCODB_PATH}api/v2/storage/upload"
    try:
        response_object = json.loads(get_nocodb_data())
        id = None
        for item in response_object['list']:
            if item['img'] and len(item['img']) > 0:
                title_check = item["img_label"].replace("+", " ").lower()
                if title.lower() in title_check:
                    id = item["Id"]
                    break
        if not id:
            logger.warning(f"Image not found for title {title}")
            return {"message": "Image not found"}
        with tempfile.NamedTemporaryFile(suffix=".PNG", delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(await file.read())
            temp_file.flush()
        with open(temp_file_path, "rb") as f:
            files_to_upload = {"file": f}
            headers = {'xc-token': XC_AUTH}
            path = os.path.basename(temp_file_path)
            upload_response = requests.post(nocodb_upload_url, headers=headers, files=files_to_upload, params={"path": path})
            upload_response.raise_for_status()
            data = upload_response.json()
            new_file_info = data[0]
            new_file_path = new_file_info.get('path')
            new_signed_path = new_file_info.get('signedPath')
            new_title = new_title.replace(" ", "+")
            title = new_title + ".png"
            update_data = {
                "Id": id,
                "img_label": new_title,
                "img": [{
                    "title": title,
                    "mimetype": file.content_type,
                    "path": new_file_path,
                    "signedPath": new_signed_path
                }]
            }
            update_headers = {'accept': 'application/json', 'xc-token': XC_AUTH, 'Content-Type': 'application/json'}
            data = json.dumps(update_data)
            update_response = requests.patch(NOCODB_IMG_UPDATE_URL, headers=update_headers, data=data)
            update_response.raise_for_status()
            logger.info(f"Successfully swapped image for {title} to {new_title}")
            return {"message": "Image swapped successfully"}
    except Exception as e:
        logger.error(f"Failed to swap image: {e}")
        return {"message": "Image not swapped successfully"}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/portal", response_class=HTMLResponse)
async def portal(request: Request):

    logger.info(f"Portal page accessed by {request.client.host}")
    context = {"brig_logo_url": brig_logo_url}
    return templates.TemplateResponse(request=request, name="login.html", context=context)

@app.post("/credentials_check")
async def credentials_check(request: Request, credentials: Credentials):
    logger.info(f"Credentials check for {credentials.username} by {request.client.host}")
    try:
        if credentials.username == BRIG_USERNAME and credentials.password == BRIG_PASSWORD:
            request.session['logged_in'] = True
            return RedirectResponse(url='/brig_portal', status_code=200)
        if credentials.username == BEN_USERNAME and credentials.password == BEN_PASSWORD:
            request.session['ben_logged_in'] = True
            return RedirectResponse(url='/logs', status_code=201)
        else:
            logger.warning(f"Invalid credentials for {credentials.username}")
            raise HTTPException(status_code=401, detail="Invalid Credentials")
    except Exception as e:
        logger.error(f"Error in credentials_check: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/logs", response_class=HTMLResponse)
async def get_log_file(request: Request):
    logger.info(f"Logs page accessed: {request.client.host}")
    try:
        if not request.session.get('ben_logged_in'):
            return RedirectResponse(url='/portal')
        logs = get_logs()
        context = {"logs": logs}
        return templates.TemplateResponse(request=request, name="logs.html", context=context)
    except Exception as e:
        logger.error(f"Error in get_log_file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/brig_portal", response_class=HTMLResponse)
async def brig_portal(request: Request):
    logger.info(f"Brig portal page accessed by {request.client.host}")
    try:
        if not request.session.get('logged_in'):
            return RedirectResponse(url='/portal')
        context = {"brig_logo_url": brig_logo_url}
        return templates.TemplateResponse(request=request, name="brig_portal.html", context=context)
    except Exception as e:
        logger.error(f"Error in brig_portal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/add_images")
async def add_images(titles: List[str] = Form(...), files: List[UploadFile] = File(...)):
    logger.info(f"Add images for titles: {titles}")
    if len(titles) != len(files):
        logger.warning("Number of titles does not match number of files")
        return {"message": "Number of titles doesn't match number of files"}
    return_list = []
    temp_file_paths = []
    try:
        for title, file in zip(titles, files):
            nocodb_upload_url = f"{NOCODB_PATH}api/v2/storage/upload"
            response_object = json.loads(get_nocodb_data())
            try:
                id = response_object['list'][-1]['Id'] + 1
            except IndexError:
                id = 1
            with tempfile.NamedTemporaryFile(suffix=".PNG", delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file_paths.append(temp_file_path)
                temp_file.write(await file.read())
                temp_file.flush()
            with open(temp_file_path, "rb") as f:
                files_to_upload = {"file": f}
                headers = {'xc-token': XC_AUTH}
                path = os.path.basename(temp_file_path)
                upload_response = requests.post(nocodb_upload_url, headers=headers, files=files_to_upload, params={"path": path})
                upload_response.raise_for_status()
                data = upload_response.json()
                new_file_info = data[0]
                new_file_path = new_file_info.get('path')
                new_signed_path = new_file_info.get('signedPath')
                new_title = title.replace(" ", "+")
                title = new_title + ".png"
                update_data = {
                    "Id": id,
                    "img_label": new_title,
                    "img": [{
                        "title": title,
                        "mimetype": file.content_type,
                        "path": new_file_path,
                        "signedPath": new_signed_path
                    }]
                }
                update_headers = {'accept': 'application/json', 'xc-token': XC_AUTH, 'Content-Type': 'application/json'}
                data = json.dumps(update_data)
                update_response = requests.post(NOCODB_IMG_UPDATE_URL, headers=update_headers, data=data)
                update_response.raise_for_status()
                return_message = {"message": "Image(s) added successfully"}
                return_list.append(return_message)
    except Exception as e:
        logger.error(f"Failed to add images: {e}")
        return {"message": "Image(s) not added successfully"}
    finally:
        for each in temp_file_paths:
            if each and os.path.exists(each):
                os.remove(each)
        return return_list[0] if return_list else {"message": "No images added"}

@app.get("/hostedimage/{title}", response_class=HTMLResponse)
async def hosted_image(request: Request, title: str):
    logger.info(f"Hosted image request for {title} by {request.client.host}")
    file_path = os.path.join(temp_dir.name, f"{title}.png")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    try:
        nocodb_data = get_nocodb_data()
        loaded_nocodb_data = json.loads(nocodb_data)
        for item in loaded_nocodb_data['list']:
            if item['img_label'] == title:
                db_path = item['img'][0]['signedPath']
                url_path = f"http://{SITE_HOST}/{db_path}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url_path) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            scale_image(image_data, file_path)
                            return FileResponse(file_path, media_type="image/png")
                        else:
                            logger.error(f"Failed to fetch image for {title}, status code: {response.status}")
                            raise HTTPException(status_code=404, detail="Image not found")
        logger.warning(f"Image not found for {title}")
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.error(f"Failed to fetch hosted image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    if SCENE == "dev":
        uvicorn.run(app="main:app", host=os.getenv("host"), port=int(os.getenv("port")), reload=True)
