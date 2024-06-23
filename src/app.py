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
from src.artapi.config import NOCODB_PATH, STRIPE_SECRET_KEY
from src.artapi.logger import logger
from src.artapi.middleware import add_middleware
from src.artapi.models import (
    Credentials, Title, TitleQuantity, ContactInfo, PaymentInfo, BillingInfo, Email,
    CheckoutInfo, TotalPrice, OrderContents
)
from src.artapi.noco import Noco
from src.artapi.logger import get_logs
import requests
import json
import tempfile
import os
from typing import List
import uuid
from src.artapi.noco_config import OPENAPI_URL, BRIG_USERNAME, BRIG_PASSWORD, BEN_USERNAME, BEN_PASSWORD
import datetime
import stripe
from typing import Dict, Any

# Initialize FastAPI App
desc = "Backend platform for BRIG ART"

if OPENAPI_URL == "None":
    OPENAPI_URL = None

app = FastAPI(
    title="Brig API",
    description=desc,
    openapi_url=OPENAPI_URL
)

stripe.api_key = STRIPE_SECRET_KEY

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
        return templates.TemplateResponse("error_500.html", {"request": request}, status_code=405)
    if exc.status_code == 404:
        logger.warning(f"Page not found: {exc.detail}")
        return templates.TemplateResponse("error_500.html", {"request": request}, status_code=404)
    

    return HTMLResponse(content=str(exc.detail), status_code=exc.status_code)

@app.get("/test_noco", response_class=HTMLResponse)
async def test_noco(request: Request):
    logger.info(f"Test NoCoDB accessed by {request.client.host}")
    try:
        # Get the image lists
        json = Noco.get_cookie_data_no_cache_no_object()
        test = Noco.get_cookie_data().cookiesJson
        return JSONResponse(test)
    except Exception as e:
        logger.error(f"Error in test_noco: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    logger.info(f"Homepage accessed by: {request.client.host}")
    try:
        context = {
            "art_uris": Noco.get_artwork_data().data_uris,
            "art_titles": Noco.get_artwork_data().titles,
            "brig_logo": Noco.get_icon_uri_from_title("brig_logo")
        }   
        return templates.TemplateResponse(request=request, name="index.html", context=context)
    except Exception as e:
        logger.error(f"Error in homepage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop/{title}", response_class=HTMLResponse)
async def shop(request: Request, title: str):
    logger.info(f"Shop page accessed for title {title} by {request.client.host}")
    try:
        
        context = {
            "img_uri": Noco.get_art_uri_from_title(title.replace("+", " ")),
            "img_title": title.replace("+", " "),
            "price": Noco.get_art_price_from_title(title.replace("+", " ")),
            "brig_logo" : Noco.get_icon_uri_from_title("brig_logo")
        }
        return templates.TemplateResponse(request=request, name="shop.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_cart_quantity")
async def get_cart_quantity(request: Request):
    logger.info(f"Get cart quantity by {request.client.host}")
    try:
        Noco.refresh_cookie_cache()
        if request.session.get("session_id") is None:
            return JSONResponse({"quantity": 0})
        
        img_quantity_list = Noco.get_cookie_from_session_id(request.session.get("session_id"))
        total_quantity = sum(int(item['quantity']) for item in img_quantity_list)
        logger.info(f"Total cart quantity: {total_quantity}")
        return JSONResponse({"quantity": total_quantity})
    except Exception as e:
        logger.error(f"Error in get_cart_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/shop_art")
async def shop_art_url(request: Request, title_quantity: TitleQuantity):
    logger.info(f"Shop art URL for {title_quantity.title} by {request.client.host}")
    try:
        Noco.refresh_cookie_cache()
        cookie_data = {}
        img_quant_dict = {}
        img_quant_dict["title"] = title_quantity.title
        img_quant_dict["quantity"] = title_quantity.quantity
        img_quant_dict["price"] = Noco.get_art_price_from_title_and_quantity(title_quantity.title, title_quantity.quantity)
        if not request.session.get("session_id"):
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            img_quant_list = []
            img_quant_list.append(img_quant_dict)
            cookie_data["img_quantity_list"] = img_quant_list
            Noco.post_cookie_session_id_and_cookies(session_id, cookie_data)
            return JSONResponse({"quantity": title_quantity.quantity})
        
        session_id = request.session.get("session_id")
        img_quant_list = Noco.get_cookie_from_session_id(session_id)

        for item in img_quant_list:
            if item["title"] == title_quantity.title:
                item["quantity"] = item["quantity"] + title_quantity.quantity
                total_quantity = sum(item["quantity"] for item in img_quant_list)
                item["price"] = Noco.get_art_price_from_title_and_quantity(item["title"], item["quantity"])
                cookiesJson = {
                    "img_quantity_list": img_quant_list
                }
                data = {
                    "Id": int(Noco.get_cookie_Id_from_session_id(session_id)),
                    "sessionid": session_id,
                    "cookiesJson": cookiesJson,
                }
                Noco.patch_cookies_data(data)
                logger.info(f"Updated quantity for {title_quantity.title}, new quantity: {total_quantity}")
                return JSONResponse({"quantity": total_quantity})
            

        img_quant_list.append(img_quant_dict)
        cookiesJson = {
            "img_quantity_list": img_quant_list
        }

        cookie_id = Noco.get_cookie_Id_from_session_id(session_id)

        if cookie_id == "" :
            logger.warning("Cookie could not be found for the session id")
            data = {
                "sessionid": session_id,
                "img_quantity_list": img_quant_list,
            }
            Noco.post_cookie_session_id_and_cookies(session_id, data)
            return JSONResponse({"quantity": title_quantity.quantity})

        data = {
            "Id": cookie_id,
            "sessionid": session_id,
            "cookiesJson": cookiesJson,
        }

        Noco.patch_cookies_data(data)

        total_quantity = sum(int(item["quantity"]) for item in img_quant_list)
        logger.info(f"Total cart quantity: {total_quantity}")

        return JSONResponse({"quantity": total_quantity})

    except Exception as e:
        logger.error(f"Error in shop_art_url: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_session_id")
async def get_session_id(request: Request):
    logger.info(f"Get session id by {request.client.host}")
    try:
        if request.session.get("session_id"):
            return JSONResponse({"session_id": request.session.get("session_id")})
        else:
            # Create one and store in database then return
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            cookie_data = {
                "img_quantity_list": []               
            }
            Noco.post_cookie_session_id_and_cookies(session_id, cookie_data)
            return JSONResponse({"session_id": session_id})
    except Exception as e:
        logger.error(f"Error in get_session_id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop_art/{sessionid}", response_class=HTMLResponse)
async def shop_art(request: Request, sessionid: str):
    logger.info(f"Shop art page accessed by {request.client.host}")
    try:
        Noco.refresh_cookie_cache()
        img_quant_list = Noco.get_cookie_from_session_id(sessionid)
        if img_quant_list == []:
            return RedirectResponse(url="/shop_art_menu")

        art_uris = Noco.get_artwork_data().data_uris
        titles = Noco.get_artwork_data().titles
        # Check if the title is in the cart if so, get the image url
        img_data_list = []
        for item in img_quant_list:
            for title in titles:
                if item['title'] in title:
                    img_url = art_uris[titles.index(title)]
                    img_dict = {}
                    img_dict["img_url"] = img_url
                    img_dict["img_title"] = title
                    img_dict["quantity"] = item['quantity']
                    img_dict["price"] = Noco.get_art_price_from_title_and_quantity(item['title'], item['quantity'])
                    img_data_list.append(img_dict)
                    
        context = {
            "img_data_list": img_data_list,
            "brig_logo_url": Noco.get_icon_uri_from_title("brig_logo"),
        }
        return templates.TemplateResponse(request=request, name="shop_art.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop_art_menu", response_class=HTMLResponse)
async def shop_art_menu(request: Request):
    logger.info(f"Shop art menu page accessed by {request.client.host}")
    try:
        context = {
            "art_uris":Noco.get_artwork_data().data_uris,
            "titles": Noco.get_artwork_data().titles,
            "price_list": Noco.get_artwork_data().prices,
            "brig_logo": Noco.get_icon_uri_from_title("brig_logo"),
        }
        return templates.TemplateResponse(request=request, name="shop_art_menu.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art_menu: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/giclee_prints", response_class=HTMLResponse)
async def shop_giclee_prints(request: Request):
    logger.info(f"Giclee prints page accessed by {request.client.host}")
    try:
        context = {
            "giclee_prints": Noco.get_artwork_data().data_uris,
            "brig_logo_url": Noco.get_icon_uri_from_title("brig_logo"),
        }
        return templates.TemplateResponse(request=request, name="gicle_prints.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_giclee_prints: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
@app.post("/post_total_price")
async def post_total_price(request: Request, total_price: TotalPrice):
    logger.info(f"Post total price {total_price.totalPrice} by {request.client.host}")
    try:
        # Find the total price and check if it matches
        Noco.refresh_cookie_cache()
        img_quant_list = Noco.get_cookie_from_session_id(request.session.get("session_id"))
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
        Noco.refresh_cookie_cache()
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = Noco.get_cookie_from_session_id(session_id)
        matched_price = None

        # Check if the title is already in the cart
        for each in img_quant_list:
            if title.title == each["title"]:
                each["quantity"] += 1  # Increment quantity
                each["price"] = Noco.get_art_price_from_title_and_quantity(each["title"], each["quantity"])
                matched_price = each["price"]
                break
        else:
            raise HTTPException(status_code=404, detail="Title not found in cart")

        patch_data = {
            "Id": int(Noco.get_cookie_Id_from_session_id(session_id)),
            "sessionid": session_id,
            "cookiesJson": {
                "img_quantity_list": img_quant_list
            }
        }

        Noco.patch_cookies_data(patch_data)
        return JSONResponse({"price": matched_price})

    except Exception as e:
        logger.error(f"Failed to increase quantity for {title.title} by {request.client.host}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/decrease_quantity")
async def decrease_quantity(request: Request, title: Title):
    logger.info(f"Decrease quantity for {title.title} by {request.client.host}")
    try:
        Noco.refresh_cookie_cache()
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = Noco.get_cookie_from_session_id(session_id)
        matched_price = None

        # Check if the title is already in the cart
        for each in img_quant_list:
            if title.title == each["title"]:
                each["quantity"] -= 1  # Decrement quantity
                each["price"] = Noco.get_art_price_from_title_and_quantity(each["title"], each["quantity"])
                matched_price = each["price"]
                break
        else:
            raise HTTPException(status_code=404, detail="Title not found in cart")

        patch_data = {
            "Id": int(Noco.get_cookie_Id_from_session_id(session_id)),
            "sessionid": session_id,
            "cookiesJson": {
                "img_quantity_list": img_quant_list
            }
        }

        Noco.patch_cookies_data(patch_data)
        return JSONResponse({"price": matched_price})
    
    except Exception as e:
        logger.error(f"Error in decrease_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/delete_item")
async def delete_item(request: Request, title: Title):
    logger.info(f"Delete item {title.title} by {request.client.host}")
    try:
        Noco.refresh_cookie_cache()
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = Noco.get_cookie_from_session_id(session_id)
        matched_price = None

        # Check if the title is already in the cart
        for each in img_quant_list:
            if title.title == each["title"]:
                img_quant_list.remove(each)
                matched_price = each["price"]
                break
        else:
            raise HTTPException(status_code=404, detail="Title not found in cart")

        patch_data = {
            "Id": int(Noco.get_cookie_Id_from_session_id(session_id)),
            "sessionid": session_id,
            "cookiesJson": {
                "img_quantity_list": img_quant_list
            }
        }

        Noco.patch_cookies_data(patch_data)
        return JSONResponse({"price": matched_price})
    except Exception as e:
        logger.error(f"Error in delete_item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/checkout/{sessionid}", response_class=HTMLResponse)
async def shop_checkout(request: Request, sessionid: str):
    # raise HTTPException(status_code=404, detail="Page not found")
    logger.info(f"Checkout page accessed by {request.client.host}")
    raise HTTPException(status_code=404, detail="Page not found")

    # try: 
    #     img_quant_list = Noco.get_cookie_from_session_id(sessionid)
    #     art_uris = Noco.get_artwork_data().data_uris
    #     titles = Noco.get_artwork_data().titles

    #     # Check if the title is in the cart if so, get the image url
    #     img_data_list = []
    #     for item in img_quant_list:
    #         for title in titles:
    #             if item["title"] in title:
    #                 img_uri = art_uris[titles.index(title)]
    #                 img_dict = {}
    #                 img_dict["img_uri"] = img_uri
    #                 img_dict["img_title"] = title
    #                 img_dict["quantity"] = item["quantity"]
    #                 img_dict["price"] = Noco.get_art_price_from_title_and_quantity(item["title"], item["quantity"])
    #                 img_data_list.append(img_dict)
    #     total_quantity = sum(int(item["quantity"]) for item in img_quant_list)
    #     total_price = sum(int(item["price"]) for item in img_quant_list) 
        
    #     context = {
    #         "img_data_list": img_data_list,
    #         "brig_logo_url": Noco.get_icon_uri_from_title("brig_logo"),
    #         "total_price": total_price,
    #         "total_quantity": total_quantity
    #     }

    #     return templates.TemplateResponse(request=request, name="checkout.html", context=context)
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
            if email_address in Noco.get_email_data().emails:
                logger.warning(f"Email {email_address} already subscribed")
                return {"message": "Email already subscribed"}
            
            Noco.post_email(email_address)
            logger.info(f"Email subscribed and inserted into nocodb: {email_address}")
            return {"message": "Email subscribed successfully"}           
    except Exception as e:
        logger.error(f"Error in subscribe: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/swap_image")
async def swap_image(title: str = Form(...), new_title: str = Form(...), file: UploadFile = File(...)):
    logger.info(f"Swap image for {title} to {new_title} ")
    
    try:
        Id = Noco.get_artwork_Id_from_title(title)
        if not Id:
            logger.warning(f"Image not found for title {title}")
            return {"message": "Image not found"}
        with tempfile.NamedTemporaryFile(suffix=".PNG", delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(await file.read())
            temp_file.flush()
        with open(temp_file_path, "rb") as f:
            files_to_upload = {"file": f}
            path = os.path.basename(temp_file_path)
            data = Noco.upload_image(files_to_upload, path)
            new_file_info = data[0]
            new_file_path = new_file_info.get('path')
            new_signed_path = new_file_info.get('signedPath')
            title = new_title.replace(" ", "+")
            title = title + ".png"
            update_data = {
                "Id": Id,
                "img_label": new_title,
                "img": [{
                    "title": title,
                    "mimetype": file.content_type,
                    "path": new_file_path,
                    "signedPath": new_signed_path
                }]
            }
            Noco.patch_image(update_data)
            logger.info(f"Successfully swapped image for {title} to {new_title}")
            return {"message": "Image swapped successfully"}
    except Exception as e:
        logger.error(f"Failed to swap image: {e}")
        return {"message": "Image not swapped successfully"}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        Noco.refresh_artwork_cache()

@app.get("/portal", response_class=HTMLResponse)
async def portal(request: Request):
    logger.info(f"Portal page accessed by {request.client.host}")
    try:
        context = {
            "brig_logo_url": Noco.get_icon_uri_from_title("brig_logo")
        }
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
        if not request.session.get('logged_in'):
            return RedirectResponse(url='/portal')
        context = {"brig_logo_url": Noco.get_icon_uri_from_title("brig_logo")}
        return templates.TemplateResponse(request=request, name="brig_portal.html", context=context)
    except Exception as e:
        logger.error(f"Error in brig_portal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/add_images")
async def add_images(titles: List[str] = Form(...), files: List[UploadFile] = File(...), prices: List[int] = Form(...)):
    logger.info(f"Add images for titles: {titles}")
    if len(titles) != len(files):
        logger.warning("Number of titles does not match number of files")
        return {"message": "Number of titles doesn't match number of files"}
    return_list = []
    temp_file_paths = []
    try:
        for title, file in zip(titles, files):
            try:
                id = Noco.get_last_art_Id() + 1
            except IndexError:
                id = 1
            with tempfile.NamedTemporaryFile(suffix=".PNG", delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file_paths.append(temp_file_path)
                temp_file.write(await file.read())
                temp_file.flush()
            with open(temp_file_path, "rb") as f:
                files_to_upload = {"file": f}
                path = os.path.basename(temp_file_path)
                data = Noco.upload_image(files_to_upload, path)
                new_file_info = data[0]
                new_file_path = new_file_info.get('path')
                new_signed_path = new_file_info.get('signedPath')
                new_title = title.replace(" ", "+")
                path_title = new_title + ".png"
                update_data = {
                    "Id": id,
                    "img_label": title,
                    "price": prices[titles.index(title)],
                    "img": [{
                        "title": path_title,
                        "mimetype": file.content_type,
                        "path": new_file_path,
                        "signedPath": new_signed_path
                    }]
                }
                Noco.post_image(update_data)
                return_message = {"message": "Image(s) added successfully"}
                return_list.append(return_message)
    except Exception as e:
        logger.error(f"Failed to add images: {e}")
        return {"message": "Image(s) not added successfully"}
    finally:
        for each in temp_file_paths:
            if each and os.path.exists(each):
                os.remove(each)

        Noco.refresh_artwork_cache()
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
        session_id = request.session.get("session_id")
        unique_order_number = Noco.generate_unique_order_number()
        contact_info = {
            "order_number": unique_order_number,
            "email": checkout_info.email,
            "phone": checkout_info.phone,
        }
        billing_info = {
            "fullname": checkout_info.fullname,
            "order_number" : unique_order_number,
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

        order_contents = {
            "img_quantity_list": Noco.get_cookie_from_session_id(session_id),
        }

        order_payload = {
            "order_number": unique_order_number,
            "order_contents" : order_contents,
        }

        cookiesJson = {
            "order_number": unique_order_number,
            "session_id": session_id,
            "contact_info": contact_info,
            "billing_info": billing_info,
            "img_quantity_list": Noco.get_cookie_from_session_id(session_id)
        }

        Noco.patch_order_cookie(session_id, cookiesJson, Noco.get_cookie_Id_from_session_id(session_id))
        Noco.post_order_data(contact_info)
        Noco.post_contact_data(billing_info)
        Noco.post_order_contents(order_payload)
    except Exception as e:
        logger.error(f"Error in checkout_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/confirmation/{sessionid}", response_class=HTMLResponse)
async def confirmation(request: Request, sessionid: str):
    logger.info(f"Confirmation page accessed by {request.client.host}")
    try:     
        Noco.refresh_cookie_cache()
        Noco.refresh_content_cache()
        Noco.empty_cart(sessionid)
        img_quant_list = Noco.get_cookie_from_session_id(sessionid)
        if img_quant_list is None:
            raise HTTPException(status_code=404, detail="Cart is empty")

        contact_info = Noco.get_contact_cookie_from_session_id(sessionid)
        billing_info = Noco.get_order_cookie_from_session_id(sessionid)
        order_number = contact_info['order_number']
        order_contents = Noco.get_order_contents_from_order_number(order_number)

        order_payload = {
            "email": contact_info['email'],
            "phone": contact_info['phone'],
            "shipping_name": billing_info['fullname'],
            "shipping_address": billing_info['address1'],
            "shipping_city": billing_info['city'],
            "shipping_state": billing_info['state'],
            "shipping_zip": billing_info['zip'],
            "order_number": order_number,
            "order_contents": order_contents['img_quantity_list'],
            "order_date" : datetime.datetime.now().strftime("%m/%d/%Y"),
            "total_price": Noco.get_total_price_from_order_contents(order_contents),
        }

        context = {
            "brig_logo_url": Noco.get_icon_uri_from_title("brig_logo"),
            "order_payload": order_payload,
        }
        return templates.TemplateResponse(request=request, name="confirmation.html", context=context)
    except Exception as e:
        logger.error(f"Error in confirmation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/get_order_contents")
async def get_order_contents(request: Request):
    try:
        Noco.refresh_cookie_cache()
        if not request.session.get('session_id'):
            logger.warning("Session ID not found")
            raise HTTPException(status_code=400, detail="Session ID not found")
        session_id = request.session.get('session_id')
        order_contents = Noco.get_cookie_from_session_id(session_id)
        order_payload = {
            "img_quantity_list": order_contents
        }
        return JSONResponse(order_payload)
    except Exception as e:
        logger.error(f"Error in get_order_contents: {e}")
        return JSONResponse(error=str(e)), 403

@app.post("/modify-payment-intent")
async def modify_payment(request: Request, order_contents: OrderContents):
    try:
        payment_intent = Noco.get_payment_intent_data_from_sessionid(request.session.get("session_id"))
        intent = stripe.PaymentIntent.modify(
            payment_intent["id"],
            metadata= payment_intent["metadata"],
            amount=Noco.get_total_price_from_order_contents(order_contents.order_contents) * 100,
        )
        Noco.patch_payment_intent_data(request.session.get("session_id"), intent)
        return JSONResponse({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        logger.error(f"Error in modify_order_contents: {e}")
        return JSONResponse(error=str(e)), 403

@app.post("/create-payment-intent")
async def create_payment(request: Request, order_contents: OrderContents):
    try:
        # Create a PaymentIntent with the order amount and currency

        intent = stripe.PaymentIntent.create(
            amount=Noco.get_total_price_from_order_contents(order_contents.order_contents) * 100,
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        Noco.post_payment_intent_data(request.session.get("session_id"), intent)
        return JSONResponse({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        logger.error(f"Error in create_payment: {e}")
        return JSONResponse(error=str(e)), 403
    
@app.post("/get_host_path_and_session_id")
async def get_host_path_and_session_id(request: Request):
    try:
        return JSONResponse({
            "host_path": "http://localhost:8000",
            "session_id": request.session.get("session_id")
        })
    except Exception as e:
        logger.error(f"Error in get_host_path_and_session_id: {e}")
        return JSONResponse(error=str(e)), 403