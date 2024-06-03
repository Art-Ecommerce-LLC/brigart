# app/main.py
from fastapi import (
    FastAPI, Request, Form, UploadFile, File, HTTPException
)
from fastapi.responses import ( 
    HTMLResponse, JSONResponse, RedirectResponse
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import sys
# Add the parent directory of src to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import NOCODB_PATH, NOCODB_IMG_UPDATE_URL, XC_AUTH
from src.logger import logger
from src.middleware import add_middleware
from src.models import Credentials, Title, TitleQuantity
from src.utils import (
    cleancart, hosted_image
)
from src.noco import (
    get_nocodb_data, HTTP, BRIG_PASSWORD, BRIG_USERNAME, OPENAPI_URL, SCENE, SITE, BEN_USERNAME, BEN_PASSWORD, SITE_HOST
)
from src.logger import get_logs
import requests
import json
import tempfile
import os
from typing import List
import uvicorn

# Initialize FastAPI App
desc = "Backend platform for BRIG ART"

if OPENAPI_URL == "None":
    OPENAPI_URL = None

app = FastAPI(
    title="Brig API",
    description=desc,
    openapi_url=OPENAPI_URL
)

# Middleware
add_middleware(app)

# Get path of where the file is running
script_path = os.path.abspath(__file__)

# Get the directory where the script is located
script_dir = os.path.dirname(script_path)

# Static files and templates
static_dir = os.path.join(script_dir, "static")
templates_dir = os.path.join(script_dir, "templates")


# Static files and templates
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 500:
        logger.error(f"Internal server error: {exc.detail}")
        return templates.TemplateResponse("error_500.html", {"request": request}, status_code=500)
    return HTMLResponse(content=str(exc.detail), status_code=exc.status_code)

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    logger.info(f"Homepage accessed by: {request.client.host}")
    try:
        hosted_images, titles = await hosted_image()
        zipped_imgs_titles = zip(hosted_images[:-3], titles[:-3])
        context = {
            "shopping_cart_url": hosted_images[-3],
            "hamburger_menu_url": hosted_images[-2],
            "brig_logo_url": hosted_images[-1],
            "temp_vars": zipped_imgs_titles,
        }
        return templates.TemplateResponse(request=request, name="index.html", context=context)
    except Exception as e:
        logger.error(f"Error in homepage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop/{title}", response_class=HTMLResponse)
async def shop(request: Request, title: str):
    logger.info(f"Shop page accessed for title {title} by {request.client.host}")
    try:
        hosted_images, titles = await hosted_image()
        for each in titles:
            if title.lower().replace("+"," ") in each.lower():
                img_url = hosted_images[titles.index(each)]
                img_title = each
                break
    
        context = {
            "img_url": img_url,
            "img_title": img_title,
            "shopping_cart_url": hosted_images[-3],
            "hamburger_menu_url": hosted_images[-2],
            "brig_logo_url": hosted_images[-1],
        }
        return templates.TemplateResponse(request=request, name="shop.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/shop_art")
async def shop_art_url(request: Request, title_quantity: TitleQuantity):
    logger.info(f"Shop art URL for {title_quantity.title} by {request.client.host}")

    try:
        img_quant_dict = {}
        img_quant_dict["title"] = title_quantity.title
        img_quant_dict["quantity"] = title_quantity.quantity
        # img_quant_dict["img_url"] = await get_data_uri_from_title(title_quantity.title)

        img_quant_list = request.session.get("img_quantity_list")

        if not img_quant_list:
            img_quant_list = []
            img_quant_list.append(img_quant_dict)
            request.session["img_quantity_list"] = img_quant_list
            return JSONResponse({"quantity": title_quantity.quantity})
        
        # Check if the title is already in the cart
        for item in img_quant_list:
            if item["title"] == title_quantity.title:
                # Update the quantity
                item["quantity"] = str(int(item["quantity"]) + int(title_quantity.quantity))
                request.session["img_quantity_list"] = img_quant_list
                total_quantity = sum(int(item["quantity"]) for item in img_quant_list)
                logger.info(f"Updated quantity for {title_quantity.title}, new quantity: {total_quantity}")
                return JSONResponse({"quantity": total_quantity})
            
        # If title is not in the cart, add it
        img_quant_list.append(img_quant_dict)
        request.session["img_quantity_list"] = img_quant_list
        total_quantity = sum(int(item["quantity"]) for item in img_quant_list)
        logger.info(f"Total cart quantity: {total_quantity}")
        print(img_quant_list)
        return JSONResponse({"quantity": total_quantity})

    except Exception as e:
        logger.error(f"Error in shop_art_url: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_cart_quantity")
async def get_cart_quantity(request: Request):
    logger.info(f"Get cart quantity by {request.client.host}")
    try:
        img_quantity_list = request.session.get("img_quantity_list")
        if not img_quantity_list:
            return JSONResponse({"quantity": 0})

        total_quantity = sum(int(item['quantity']) for item in img_quantity_list)
        logger.info(f"Total cart quantity: {total_quantity}")
        return JSONResponse({"quantity": total_quantity})
    except Exception as e:
        logger.error(f"Error in get_cart_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop_art", response_class=HTMLResponse)
async def shop_art(request: Request):
    logger.info(f"Shop art page accessed by {request.client.host}")
    try:
        cleancart(request)
        img_quant_list = request.session.get("img_quantity_list")
        if not img_quant_list:
            img_quant_list = []

        hosted_images, titles = await hosted_image()
        img_data_list = []

        for item in img_quant_list:
            for title in titles:
                if item["title"] in title:
                    img_url = hosted_images[titles.index(title)]
                    img_dict = {}
                    img_dict["img_url"] = img_url
                    img_dict["img_title"] = title
                    img_dict["quantity"] = item["quantity"]
                    img_dict["price"] = 225 * int(item["quantity"])
                    img_data_list.append(img_dict)
        
        context = {
            "img_data_list": img_data_list,
            "shopping_cart_url": hosted_images[-3],
            "hamburger_menu_url": hosted_images[-2],
            "brig_logo_url": hosted_images[-1],
        }
        return templates.TemplateResponse(request=request, name="shop_art.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop_art_menu", response_class=HTMLResponse)
async def shop_art_menu(request: Request):
    logger.info(f"Shop art menu page accessed by {request.client.host}")
    try:
        hosted_images, titles = await hosted_image()

        artwork_data = zip(titles[:-3], hosted_images[:-3])

        context = {
            "artwork_data": artwork_data,
            "shopping_cart_url": hosted_images[-3],
            "hamburger_menu_url": hosted_images[-2],
            "brig_logo_url": hosted_images[-1],
        }
        return templates.TemplateResponse(request=request, name="shop_art_menu.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art_menu: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/giclee_prints", response_class=HTMLResponse)
async def shop_giclee_prints(request: Request):
    logger.info(f"Giclee prints page accessed by {request.client.host}")
    hosted_images, titles = await hosted_image()

    context = {
        "shopping_cart_url": hosted_images[-3],
        "hamburger_menu_url": hosted_images[-2],
        "brig_logo_url": hosted_images[-1],
    }
    return templates.TemplateResponse(request=request, name="gicle_prints.html", context=context)

@app.post("/increase_quantity")
async def increase_quantity(request: Request, title: Title):
    logger.info(f"Increase quantity for {title.title} by {request.client.host}")
    try:
            title = title.title
            img_quant_list = request.session.get("img_quantity_list")
            for each in img_quant_list:
                if title == each["title"]:
                    # Increase quantity by one
                    each["quantity"] = str(int(each["quantity"]) + 1)

    except Exception as e:
        logger.error(f"Error in increase_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/decrease_quantity")
async def decrease_quantity(request: Request, title: Title):
    logger.info(f"Decrease quantity for {title.title} by {request.client.host}")
    try:
        img_quant_list = request.session.get("img_quantity_list")
        for each in img_quant_list:
            if title == each["title"]:
                # Increase quantity by one
                each["quantity"] = str(int(each["quantity"]) - 1)
    except Exception as e:
        logger.error(f"Error in decrease_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/delete_item")
async def delete_item(request: Request, title: Title):
    logger.info(f"Delete item {title.title} by {request.client.host}")
    try:
        title = title.title
        img_quant_list = request.session.get("img_quantity_list")
        for each in img_quant_list:
            if title == each["title"]:
                img_quant_list.remove(each)
                request.session["img_quantity_list"] = img_quant_list
                logger.info(f"Item {title} removed from cart")
                return JSONResponse({"message": "Item removed from cart"})
        
    except Exception as e:
        logger.error(f"Error in delete_item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/checkout", response_class=HTMLResponse)
async def shop_checkout(request: Request):
    logger.info(f"Checkout page accessed by {request.client.host}")
    try: 
        img_quant_list = request.session.get("img_quantity_list")
        if not img_quant_list:
            img_quant_list = []

        hosted_images, titles = await hosted_image()
        img_data_list = []

        for item in img_quant_list:
            for title in titles:
                if item["title"] in title:
                    img_url = hosted_images[titles.index(title)]
                    img_dict = {}
                    img_dict["img_url"] = img_url
                    img_dict["img_title"] = title
                    img_dict["quantity"] = item["quantity"]
                    img_dict["price"] = 225 * int(item["quantity"])
                    img_data_list.append(img_dict)
        total_quantity = sum(int(item["quantity"]) * 225 for item in img_quant_list)
        total_price = 225 * total_quantity

        context = {
            "img_data_list": img_data_list,
            "shopping_cart_url": hosted_images[-3],
            "hamburger_menu_url": hosted_images[-2],
            "brig_logo_url": hosted_images[-1],
            "total_price": total_price,
            "total_quantity": total_quantity
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
    try:
        hosted_images, titles = await hosted_image()
        context = {"brig_logo_url": hosted_images[-1]}
        return templates.TemplateResponse(request=request, name="login.html", context=context)
    except Exception as e:
        logger.error(f"Error in portal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
        hosted_images, titles = await hosted_image()
        if not request.session.get('logged_in'):
            return RedirectResponse(url='/portal')
        context = {"brig_logo_url": hosted_images[-1]}
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

# @app.get("/hostedimage/{title}", response_class=HTMLResponse)
# async def hosted_image(request: Request, title: str):
#     logger.info(f"Hosted image request for {title} by {request.client.host}")
#     file_path = os.path.join(temp_dir.name, f"{title}.png")
#     if os.path.exists(file_path):
#         return FileResponse(file_path, media_type="image/png")
#     try:
#         nocodb_data = get_nocodb_data()
#         loaded_nocodb_data = json.loads(nocodb_data)
#         for item in loaded_nocodb_data['list']:
#             if item['img_label'] == title:
#                 db_path = item['img'][0]['signedPath']
#                 url_path = f"{HTTP}://{SITE_HOST}/{db_path}"
#                 async with aiohttp.ClientSession() as session:
#                     async with session.get(url_path) as response:
#                         if response.status == 200:
#                             image_data = await response.read()
#                             scale_image(image_data, file_path)
#                             return FileResponse(file_path, media_type="image/png")
#                         else:
#                             logger.error(f"Failed to fetch image for {title}, status code: {response.status}")
#                             raise HTTPException(status_code=404, detail="Image not found")
#         logger.warning(f"Image not found for {title}")
#         raise HTTPException(status_code=404, detail="Image not found")
#     except Exception as e:
#         logger.error(f"Failed to fetch hosted image: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    if SCENE == "dev":
       uvicorn.run(app="app:app", host=os.getenv("host"), port=int(os.getenv("port")), reload=True)
    # If Mac:
    # uvicorn.run(app="app:app", host=os.getenv("host"), port=444, reload=True)