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
from src.artapi.config import NOCODB_PATH, NOCODB_IMG_UPDATE_URL, XC_AUTH
from src.artapi.logger import logger
from src.artapi.middleware import add_middleware
from src.artapi.models import (
    Credentials, Title, TitleQuantity, ContactInfo, PaymentInfo, BillingInfo, Email, CheckoutInfo, TotalPrice
)
from src.artapi.utils import (
    cleancart, hosted_image, fetch_email_list, post_order_data, get_price_from_title_and_quantity, get_price_from_title, get_price_list
)
from src.artapi.noco import (
    get_nocodb_data, post_nocodb_email_data, BRIG_PASSWORD, BRIG_USERNAME, OPENAPI_URL,BEN_USERNAME, BEN_PASSWORD
)
from src.artapi.logger import get_logs
import requests
import json
import tempfile
import os
from typing import List
import datetime

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
    if exc.status_code == 401:
        logger.warning(f"Unauthorized access: {exc.detail}")
        return templates.TemplateResponse("error_500.html", {"request": request}, status_code=401)
    if exc.status_code == 400:
        logger.warning(f"Bad request: {exc.detail}")
        return templates.TemplateResponse("error_500.html", {"request": request}, status_code=400)
    if exc.status_code == 405:
        logger.warning(f"Page not found: {exc.detail}")
        return templates.TemplateResponse("error_405.html", {"request": request}, status_code=404)
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
                price = await get_price_from_title(title)
                break

        context = {
            "img_url": img_url,
            "img_title": img_title,
            "price": price,
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
        img_quant_dict["price"] = await get_price_from_title_and_quantity(title_quantity.title, title_quantity.quantity)  
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
                # Change the price too
                item["price"] = await get_price_from_title_and_quantity(item["title"], item["quantity"])
                logger.info(f"Updated quantity for {title_quantity.title}, new quantity: {total_quantity}")
                return JSONResponse({"quantity": total_quantity})
            
        # If title is not in the cart, add it
        img_quant_list.append(img_quant_dict)
        request.session["img_quantity_list"] = img_quant_list
        total_quantity = sum(int(item["quantity"]) for item in img_quant_list)
        logger.info(f"Total cart quantity: {total_quantity}")
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
        await cleancart(request)
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
                    img_dict["price"] = await get_price_from_title_and_quantity(item["title"], item["quantity"])
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
        
        # Get price list
        price_list = await get_price_list()

        context = {
            "artwork_data": artwork_data,
            "price_list": price_list,
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

@app.post("/post_total_price")
async def post_total_price(request: Request, total_price: TotalPrice):
    logger.info(f"Post total price {total_price.totalPrice} by {request.client.host}")
    try:
        # Find the total price and check if it matches
        img_quant_list = request.session.get("img_quantity_list")
        cookie_price_total = sum(int(item["price"]) for item in img_quant_list)
        if cookie_price_total == total_price.totalPrice:
            return JSONResponse({"totalPrice": total_price.totalPrice})
        else:
            logger.warning(f"Total price {total_price} does not match")
            raise HTTPException(status_code=400, detail="Total price does not match")
    except Exception as e:
        logger.error(f"Error in post_total_price: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
                    each["price"] = await get_price_from_title_and_quantity(each["title"], each["quantity"])
                    return JSONResponse({"price": each["price"]})

    except Exception as e:
        logger.error(f"Error in increase_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/decrease_quantity")
async def decrease_quantity(request: Request, title: Title):
    logger.info(f"Decrease quantity for {title.title} by {request.client.host}")
    try:
        title = title.title
        img_quant_list = request.session.get("img_quantity_list")
        for each in img_quant_list:
            if title == each["title"]:
                # Increase quantity by one
                each["quantity"] = str(int(each["quantity"]) - 1)
                each["price"] = await get_price_from_title_and_quantity(each["title"], each["quantity"])
                if int(each["quantity"]) == 0:
                    img_quant_list.remove(each)
                    request.session["img_quantity_list"] = img_quant_list
                return JSONResponse({"price": each["price"]})

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
    # logger.info(f"Checkout page accessed by {request.client.host}")
    # try: 
    raise HTTPException(status_code=405, detail="Internal server error")
        # await cleancart(request)
        # img_quant_list = request.session.get("img_quantity_list")
        # if not img_quant_list:
        #     img_quant_list = []

        # hosted_images, titles = await hosted_image()
        # img_data_list = []

        # for item in img_quant_list:
        #     for title in titles:
        #         if item["title"] in title:
        #             img_url = hosted_images[titles.index(title)]
        #             img_dict = {}
        #             img_dict["img_url"] = img_url
        #             img_dict["img_title"] = title
        #             img_dict["quantity"] = item["quantity"]
        #             img_dict["price"] = await get_price_from_title_and_quantity(item["title"], item["quantity"])
        #             img_data_list.append(img_dict)
        # total_quantity = sum(int(item["quantity"]) for item in img_quant_list)
        # total_price = sum(int(item["price"]) for item in img_quant_list) 

        # context = {
        #     "img_data_list": img_data_list,
        #     "shopping_cart_url": hosted_images[-3],
        #     "hamburger_menu_url": hosted_images[-2],
        #     "brig_logo_url": hosted_images[-1],
        #     "total_price": total_price,
        #     "total_quantity": total_quantity
        # }

        # return templates.TemplateResponse(request=request, name="checkout.html", context=context)
    # except Exception as e:
    #     logger.error(f"Error in shop_checkout: {e}")
    #     raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/subscribe")
async def subscribe(request: Request, email: Email):
    logger.info(f"Subscribe request by {email.email} from {request.client.host}")
    try:
        if email.email:
            # Insert into NoCodeDB
            email_address = email.email
            if email_address in fetch_email_list():
                logger.warning(f"Email {email_address} already subscribed")
                return {"message": "Email already subscribed"}
            
            post_nocodb_email_data({"email": email_address})
            logger.info(f"Email subscribed and inserted into nocodb: {email_address}")
            return {"message": "Email subscribed successfully"}           
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

@app.post("/validate_contact_info")
async def validate_contact_info(request: Request, contact_info: ContactInfo):
    logger.info(f"Validate contact info for {contact_info.email} by {request.client.host}")
    try:
        if not contact_info.email or not contact_info.phone:
            logger.warning("Email or phone number not provided")
            raise HTTPException(status_code=400, detail="Email or phone number not provided")
        
    except Exception as e:
        logger.error(f"Error in validate_contact_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/validate_payment_info")
async def validate_payment_info(request: Request, payment_info: PaymentInfo):
    logger.info(f"Validate payment info for {payment_info.cardName} by {request.client.host}")
    try:
        if not payment_info.cardName or not payment_info.cardNumber or not payment_info.expiryDate or not payment_info.cvv:
            logger.warning("Payment information not provided")
            raise HTTPException(status_code=400, detail="Payment information not provided")
        
        # Insert into NoCodeDB

    except Exception as e:
        logger.error(f"Error in validate_payment_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/validate_shipping_info")
async def validate_billing_info(request: Request, billing_info: BillingInfo):
    logger.info(f"Validate billing info for {billing_info.fullname} by {request.client.host}")
    try:
        if not billing_info.fullname or not billing_info.address1 or not billing_info.city or not billing_info.state or not billing_info.zip:
            logger.warning("Billing information not provided")
            raise HTTPException(status_code=400, detail="Billing information not provided")
        
        # Insert into NoCodeDB

    except Exception as e:
        logger.error(f"Error in validate_billing_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/purchase")
async def checkout_info(request: Request, checkout_info: CheckoutInfo):
    logger.info(f"Checkout info for {checkout_info.email} by {request.client.host}")
    try:
        # Insert shipping info and contact info into NoCodeDB
        contact_info = {
            "email": checkout_info.email,
            "phone": checkout_info.phone,
        }
        billing_info = {
            "fullname": checkout_info.fullname,
            "address1": checkout_info.address1,
            "address2": checkout_info.address2,
            "city": checkout_info.city,
            "state": checkout_info.state,
            "zip": checkout_info.zip,
        }
        if checkout_info.shipFullname:
            billing_info["fullname"] = checkout_info.shipFullname
            billing_info["address1"] = checkout_info.shipAddress1
            billing_info["address2"] = checkout_info.shipAddress2
            billing_info["city"] = checkout_info.shipCity
            billing_info["state"] = checkout_info.shipState
            billing_info["zip"] = checkout_info.shipZip

        # Insert into NoCodeDB
        post_order_data(contact_info, billing_info, request.session.get("img_quantity_list"))

        request.session["contact_info"] = contact_info
        request.session["billing_info"] = billing_info

    except Exception as e:
        logger.error(f"Error in checkout_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/confirmation")
async def confirmation(request: Request):
    logger.info(f"Confirmation page accessed by {request.client.host}")
    try:
        hosted_images, titles = await hosted_image()
        img_quant_list = request.session.get("img_quantity_list")
        if img_quant_list:
            request.session["img_quantity_list"] = []

        contact_info = request.session.get("contact_info")
        billing_info = request.session.get("billing_info")

        order_payload = {
            "email": contact_info['email'],
            "phone": contact_info['phone'],
            "shipping_name": billing_info['fullname'],
            "shipping_address": billing_info['address1'],
            "shipping_city": billing_info['city'],
            "shipping_state": billing_info['state'],
            "shipping_zip": billing_info['zip'],
        }

        context = {
            "shopping_cart_url": hosted_images[-3],
            "hamburger_menu_url": hosted_images[-2],
            "brig_logo_url": hosted_images[-1],
            "order_payload": order_payload,
        }
        return templates.TemplateResponse(request=request, name="confirmation.html", context=context)
    except Exception as e:
        logger.error(f"Error in confirmation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
