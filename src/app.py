# app/main.py
from fastapi import (
    FastAPI, Request, Form, UploadFile, File, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
)
from fastapi.responses import ( 
    HTMLResponse, JSONResponse, RedirectResponse, FileResponse, StreamingResponse
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from src.artapi.config import STRIPE_SECRET_KEY, HOST, WEBSOCKET
from src.artapi.logger import logger
from src.artapi.middleware import add_middleware, limiter
from src.artapi.models import (
    Credentials, Title, TitleQuantity, TotalPrice
)
from src.artapi.noco import Noco
from src.artapi.logger import get_logs
import tempfile
import os
from typing import List
import uuid
from src.artapi.noco_config import OPENAPI_URL, BRIG_USERNAME, BRIG_PASSWORD, BEN_USERNAME, BEN_PASSWORD
import datetime
import stripe
from datetime import datetime, timezone
from src.artapi.nocodb_connector import get_noco_db
from contextlib import asynccontextmanager
import asyncio
from typing import List

# Initialize FastAPI App
desc = "Backend platform for BRIG ART"

if OPENAPI_URL == "None":
    OPENAPI_URL = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    noco_db = Noco()
    asyncio.create_task(noco_db.delete_expired_sessions())
    asyncio.create_task(noco_db.check_for_artwork_updates())
    yield
    # No spec

app = FastAPI(
    title="Brig API",
    description=desc,
    openapi_url=OPENAPI_URL,
    lifespan= lifespan
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
        return templates.TemplateResponse("error_405.html", {"request": request}, status_code=404)
    

    return HTMLResponse(content=str(exc.detail), status_code=exc.status_code)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    noco_db = Noco()
    await websocket.accept()
    noco_db.connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process the data and handle it
            if data == "Artwork data updated":
                for client in noco_db.connected_clients:
                    await client.send_text("Artwork data updated")
    except WebSocketDisconnect:
        noco_db.connected_clients.remove(websocket)

@app.get("/", response_class=HTMLResponse)
@limiter.limit("100/minute")
async def homepage(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Homepage accessed by: {request.client.host}")
    try:
        context = {
            "art_uris": noco_db.get_artwork_data().data_uris,
            "art_titles": noco_db.get_artwork_data().titles,
            "brig_logo": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version(),
            "host" : HOST,
            "websocket" : WEBSOCKET
        }
        return templates.TemplateResponse(request=request, name="index.html", context=context)
    except Exception as e:
        logger.error(f"Error in homepage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop/{title}", response_class=HTMLResponse)
@limiter.limit("100/minute")  # Public data fetching
async def shop(request: Request, title: str, noco_db: Noco = Depends(get_noco_db)):

    logger.info(f"Shop page accessed for title {title} by {request.client.host}")
    try:
        context = {
            "img_uri": noco_db.get_art_uri_from_title(title.replace("+", " ")),
            "img_title": title.replace("+", " "),
            "price": noco_db.get_art_price_from_title(title.replace("+", " ")),
            "brig_logo" : noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="shop.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_cart_quantity")
@limiter.limit("100/minute")  # Public data fetching
async def get_cart_quantity(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Get cart quantity by {request.client.host}")
    try:

        if request.session.get("session_id") is None:
            return JSONResponse({"quantity": 0})
        
        img_quantity_list = noco_db.get_cookie_from_session_id(request.session.get("session_id"))
        total_quantity = sum(int(item['quantity']) for item in img_quantity_list)
        logger.info(f"Total cart quantity: {total_quantity}")
        return JSONResponse({"quantity": total_quantity})
    except Exception as e:
        logger.error(f"Error in get_cart_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/shop_art")
@limiter.limit("100/minute")  # Public data fetching
async def shop_art_url(request: Request, title_quantity: TitleQuantity, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Shop art URL for {title_quantity.title} by {request.client.host}")
    try:
        cookie_data = {}
        img_quant_dict = {}
        img_quant_dict["title"] = title_quantity.title
        img_quant_dict["quantity"] = title_quantity.quantity
        img_quant_dict["price"] = noco_db.get_art_price_from_title_and_quantity(title_quantity.title, title_quantity.quantity)

        if request.session.get("session_id") is None:
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            img_quant_list = []
            img_quant_list.append(img_quant_dict)
            cookie_data["img_quantity_list"] = img_quant_list
            noco_db.post_cookie_session_id_and_cookies(session_id, cookie_data)
            return JSONResponse({"quantity": title_quantity.quantity})
        

        session_id = request.session.get("session_id")
        img_quant_list = noco_db.get_cookie_from_session_id(session_id)

        for item in img_quant_list:
            if item["title"] == title_quantity.title:
                item["quantity"] = item["quantity"] + title_quantity.quantity
                total_quantity = sum(item["quantity"] for item in img_quant_list)
                item["price"] = noco_db.get_art_price_from_title_and_quantity(item["title"], item["quantity"])
                cookiesJson = {
                    "img_quantity_list": img_quant_list
                }
                data = {
                    "Id": int(noco_db.get_cookie_Id_from_session_id(session_id)),
                    "sessionids": session_id,
                    "cookies": cookiesJson,
                }
                noco_db.patch_cookies_data(data)
                logger.info(f"Updated quantity for {title_quantity.title}, new quantity: {total_quantity}")
                return JSONResponse({"quantity": total_quantity})
            
        img_quant_list.append(img_quant_dict)
        cookiesJson = {
            "img_quantity_list": img_quant_list
        }
        cookie_id = noco_db.get_cookie_Id_from_session_id(session_id)

        if cookie_id == "" :
            logger.warning("Cookie could not be found for the session id")
            noco_db.post_cookie_session_id_and_cookies(session_id, cookiesJson)
            return JSONResponse({"quantity": title_quantity.quantity})

        data = {
            "Id": cookie_id,
            "sessionids": session_id,
            "cookies": cookiesJson,
        }

        noco_db.patch_cookies_data(data)
        total_quantity = sum(int(item["quantity"]) for item in img_quant_list)
        logger.info(f"Total cart quantity: {total_quantity}")
        return JSONResponse({"quantity": total_quantity})

    except Exception as e:
        logger.error(f"Error in shop_art_url: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop_art/{sessionid}", response_class=HTMLResponse)
@limiter.limit("100/minute")  # Public data fetching
async def shop_art(request: Request, sessionid: str, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Shop art page accessed by {request.client.host}")
    try:
        if request.session.get("session_id") != sessionid:
            logger.warning(f"Session ID does not match {request.client.host}")
            return RedirectResponse(url="/shop_art_menu")                        
        img_quant_list = noco_db.get_cookie_from_session_id(sessionid)
        art_uris = noco_db.get_artwork_data().data_uris
        titles = noco_db.get_artwork_data().titles
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
                    img_dict["price"] = noco_db.get_art_price_from_title_and_quantity(item['title'], item['quantity'])
                    img_data_list.append(img_dict)
                    
        context = {
            "img_data_list": img_data_list,
            "brig_logo_url": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="shop_art.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/shop_art_menu", response_class=HTMLResponse)
@limiter.limit("100/minute")  # Public data fetching
async def shop_art_menu(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Shop art menu page accessed by {request.client.host}")
    try:
        
        context = {
            "art_uris":noco_db.get_artwork_data().data_uris,
            "titles": noco_db.get_artwork_data().titles,
            "price_list": noco_db.get_artwork_data().prices,
            "brig_logo": noco_db.get_icon_uri_from_title("brig_logo"),
            "version" : noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="shop_art_menu.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art_menu: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/giclee_prints", response_class=HTMLResponse)
@limiter.limit("100/minute")  # Public data fetching
async def shop_giclee_prints(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Giclee prints page accessed by {request.client.host}")
    try:
        context = {
            "giclee_prints": noco_db.get_artwork_data().data_uris,
            "brig_logo_url": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="gicle_prints.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_giclee_prints: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/post_total_price")
@limiter.limit("100/minute")  # Public data fetching
async def post_total_price(request: Request, total_price: TotalPrice, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Post total price {total_price.totalPrice} by {request.client.host}")
    try:
        img_quant_list = noco_db.get_cookie_from_session_id(request.session.get("session_id"))
        cookie_price_total = sum(int(item["price"]) for item in img_quant_list)
        if cookie_price_total == total_price.totalPrice:
            return JSONResponse({"totalPrice": total_price.totalPrice})
        else:
            logger.warning(f"Total price {total_price} does not match {cookie_price_total}")
            raise HTTPException(status_code=400, detail="Total price does not match")
    except Exception as e:
        logger.error(f"Error in post_total_price: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/increase_quantity")
@limiter.limit("100/minute")  # Public data fetching
async def increase_quantity(request: Request, title: Title, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Increase quantity for {title.title} by {request.client.host}")
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            logger.info(f"Session ID not found from request {request.client.host}")
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = noco_db.get_cookie_from_session_id(session_id)
        matched_price = None
        # Check if the title is already in the cart
        for each in img_quant_list:
            if title.title == each["title"]:
                each["quantity"] += 1  # Increment quantity
                each["price"] = noco_db.get_art_price_from_title_and_quantity(each["title"], each["quantity"])
                matched_price = each["price"]
                break
        else:
            raise HTTPException(status_code=404, detail="Title not found in cart")

        patch_data = {
            "Id": int(noco_db.get_cookie_Id_from_session_id(session_id)),
            "sessionids": session_id,
            "cookies": {
                "img_quantity_list": img_quant_list,
            },    
        }

        noco_db.patch_cookies_data(patch_data)
        return JSONResponse({"price": matched_price})

    except Exception as e:
        logger.error(f"Failed to increase quantity for {title.title} by {request.client.host}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/decrease_quantity")
@limiter.limit("100/minute")  # Public data fetching
async def decrease_quantity(request: Request, title: Title, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Decrease quantity for {title.title} by {request.client.host}")
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            logger.info(f"Session ID not found from request {request.client.host}")
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = noco_db.get_cookie_from_session_id(session_id)
        matched_price = None

        # Check if the title is already in the cart


        for each in img_quant_list:
            if title.title == each["title"]:
                if each["quantity"] == 1:
                    img_quant_list.remove(each)
                    matched_price = each["price"]
                    break

                each["quantity"] -= 1  # Decrement quantity
                each["price"] = noco_db.get_art_price_from_title_and_quantity(each["title"], each["quantity"])
                matched_price = each["price"]
                break
        else:
            raise HTTPException(status_code=404, detail="Title not found in cart")

        if img_quant_list == []:
            noco_db.delete_session_cookie(session_id)
            request.session.pop("session_id")
            return JSONResponse({"price": 0})

        patch_data = {
            "Id": int(noco_db.get_cookie_Id_from_session_id(session_id)),
            "sessionids": session_id,
            "cookies": {
                "img_quantity_list": img_quant_list
            }
        }

        noco_db.patch_cookies_data(patch_data)
        return JSONResponse({"price": matched_price})
    except Exception as e:
        logger.error(f"Error in decrease_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/delete_item")
@limiter.limit("100/minute")  # Public data fetching
async def delete_item(request: Request, title: Title, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Delete item {title.title} by {request.client.host}")
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = noco_db.get_cookie_from_session_id(session_id)
        matched_price = None

        
        for each in img_quant_list:
            if title.title == each["title"]:
                img_quant_list.remove(each)
                matched_price = each["price"]
                break
        else:
            raise HTTPException(status_code=404, detail="Title not found in cart")
        
        if img_quant_list == []:
            noco_db.delete_session_cookie(session_id)
            request.session.pop("session_id")
            return JSONResponse({"price": 0})
        
        patch_data = {
            "Id": int(noco_db.get_cookie_Id_from_session_id(session_id)),
            "sessionids": session_id,
            "cookies": {
                "img_quantity_list": img_quant_list
            }
        }

        noco_db.patch_cookies_data(patch_data)
        return JSONResponse({"price": matched_price})
    except Exception as e:
        logger.error(f"Error in delete_item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Change checkout to be a payment link creation and then redirect to that payment link with the correct products
@app.get("/checkout/{sessionid}", response_class=HTMLResponse)
@limiter.limit("100/minute")  # Public data fetching
async def shop_checkout(request: Request, sessionid: str, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Checkout page accessed by {request.client.host}")
    try:
        # Create payment link with the items in the cart
        if request.session.get("session_id") != sessionid:
            logger.warning(f"Session ID does not match {request.client.host}")
            return RedirectResponse(url="/shop_art_menu")
               
        img_quant_list = noco_db.get_cookie_from_session_id(sessionid)
        products = stripe.Product.list(limit=300)
        line_items = []
        for product in products:
            for item in img_quant_list:
                if product.name == item["title"]:
                    line_items.append({
                        'price': product.default_price,
                        'quantity': item["quantity"],
                    })
        if line_items == []:
            logger.info("Cart is empty")
            return RedirectResponse(url="/shop_art_menu")
        
        payment_link = stripe.PaymentLink.create(
            line_items=line_items,
            automatic_tax = {
                'enabled': True,
                'liability' : {
                    'type' : 'self',
                }
            },
            shipping_address_collection={
                'allowed_countries': ['US'],
            },
            shipping_options = [{
                'shipping_rate' : "shr_1PbZ0yP7gcDRwQa3LoqgQqbK",
            }],
        )
        return RedirectResponse(url=payment_link.url)
    except Exception as e:
        logger.error(f"Error in shop_checkout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/get_session_id")
@limiter.limit("100/minute") 
async def get_session_id(request: Request):
    logger.info(f"Get session ID by {request.client.host}")
    try:
        session_id = request.session.get("session_id")
        if session_id is None:
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            logger.info(f"Session ID created: {session_id}")
        return JSONResponse({"session_id": session_id})
    except Exception as e:
        logger.error(f"Error in get_session_id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/portal", response_class=HTMLResponse)
@limiter.limit("100/minute")  # Public data fetching
async def portal(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Portal page accessed by {request.client.host}")
    try:
        context = {
            "brig_logo_url": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="login.html", context=context)
    except Exception as e:
        logger.error(f"Error in portal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/credentials_check")
@limiter.limit("100/minute")  # Public data fetching
async def credentials_check(request: Request, credentials: Credentials, noco_db: Noco = Depends(get_noco_db)):
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
@limiter.limit("100/minute")  # Public data fetching
async def get_log_file(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Logs page accessed: {request.client.host}")
    try:
        if not request.session.get('ben_logged_in'):
            return RedirectResponse(url='/portal')
        logs = get_logs()
        context = {
            "logs": logs,
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="logs.html", context=context)
    except Exception as e:
        logger.error(f"Error in get_log_file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/brig_portal", response_class=HTMLResponse)
@limiter.limit("100/minute")  # Public data fetching
async def brig_portal(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Brig portal page accessed by {request.client.host}")
    try: 
        if not request.session.get('logged_in'):
            return RedirectResponse(url='/portal')
        context = {
            "brig_logo_url": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="brig_portal.html", context=context)
    except Exception as e:
        logger.error(f"Error in brig_portal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/add_images")
@limiter.limit("100/minute")  # Public data fetching
async def add_images(request : Request, titles: List[str] = Form(...), files: List[UploadFile] = File(...), prices: List[int] = Form(...), noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Add images for titles: {titles}")
    if len(titles) != len(files):
        logger.warning("Number of titles does not match number of files")
        return {"message": "Number of titles doesn't match number of files"}
    return_list = []
    temp_file_paths = []
    try:
        for title, file in zip(titles, files):
            try:
                id = noco_db.get_last_art_Id() + 1
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
                data = noco_db.upload_image(files_to_upload, path)
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
                noco_db.post_image(update_data)
                return_message = {"message": "Image(s) added successfully"}
                return_list.append(return_message)
    except Exception as e:
        logger.error(f"Failed to add images: {e}")
        return {"message": "Image(s) not added successfully"}
    finally:
        for each in temp_file_paths:
            if each and os.path.exists(each):
                os.remove(each)

        noco_db.refresh_artwork_cache()
        return return_list[0] if return_list else {"message": "No images added"}


@app.post("/swap_image")
@limiter.limit("100/minute")  # Public data fetching
async def swap_image(request : Request, title: str = Form(...), new_title: str = Form(...), file: UploadFile = File(...), noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Swap image for {title} to {new_title} ")
    
    try:
        Id = noco_db.get_artwork_Id_from_title(title)
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
            data = noco_db.upload_image(files_to_upload, path)
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
            noco_db.patch_image(update_data)
            logger.info(f"Successfully swapped image for {title} to {new_title}")
            return {"message": "Image swapped successfully"}
    except Exception as e:
        logger.error(f"Failed to swap image: {e}")
        return {"message": "Image not swapped successfully"}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        noco_db.refresh_artwork_cache()

@app.get("/favicon.ico")
@limiter.limit("100/minute")  # Public data fetching
async def favicon(request: Request):
    return RedirectResponse(url="/static/favicon.ico")

# Also creates a file in Stripe
@app.get("/download_image/{title}")
@limiter.limit("100/minute")  # Public data fetching
async def get_image(request : Request, title: str, background_tasks: BackgroundTasks, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Get image for {title}")
    try:
        # Replace this with your actual method to get the URI
        uri = noco_db.get_art_uri_from_title(title)
        if not uri:
            logger.warning(f"Image not found for title {title}")
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Decode the data URI and get the temp file path
        temp_file_path = noco_db.decode_data_uri(uri, title)

        # Schedule the file to be deleted after the response is sent
        background_tasks.add_task(noco_db.delete_temp_file, temp_file_path)

        # Create a file in Stripe
        with open(temp_file_path, "rb") as fp:
            stripe.File.create(
                purpose="product_image",
                file=fp
            )

        return FileResponse(temp_file_path, media_type="image/png", filename=f"{title}.png", background=background_tasks)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Failed to get image: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve image")

@app.get("/stream_image/{title}")
async def get_image(title: str, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Get image for {title}")
    try:
        # Replace this with your actual method to get the URI
        uri = noco_db.get_art_uri_from_title(title)
        if not uri:
            logger.warning(f"Image not found for title {title}")
            raise HTTPException(status_code=404, detail="Image not found")
        # Decode the data URI and get the BytesIO stream
        image_stream = noco_db.decode_data_uri_to_BytesIO(uri)
        return StreamingResponse(image_stream, media_type="image/png")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Failed to get image: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve image")


@app.get("/return_policy", response_class=HTMLResponse)
@limiter.limit("100/minute")  # Public data fetching
async def return_policy(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Return policy page accessed by {request.client.host}")
    try:
        context = {
            "brig_logo": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="return_policy.html", context=context)
    except Exception as e:
        logger.error(f"Error in return_policy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/get_session_time")
@limiter.limit("100/minute")  # Public data fetching
async def get_session_time(request: Request, noco_db: Noco = Depends(get_noco_db)):
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID not found")

    try:
        session_creation_time_str = noco_db.get_cookie_session_begginging_time(session_id)
        session_creation_time = datetime.fromisoformat(session_creation_time_str.replace('Z', '+00:00'))  # Convert to datetime object
        current_time = datetime.now(timezone.utc)
        elapsed_time = (current_time - session_creation_time).total_seconds()
        remaining_time = max(0, 900 - elapsed_time)  # 30 minutes = 1800 seconds

        return JSONResponse({"remaining_time": int(remaining_time)})

    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid session creation time format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/delete_session")
@limiter.limit("100/minute")  # Public data fetching
async def delete_session(request: Request, noco_db: Noco = Depends(get_noco_db)):
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID not found")
    try:
        # Delete the session from your storage (database, cache, etc.)
        noco_db.delete_session_cookie(session_id)
        request.session.pop("session_id")
        return JSONResponse({"message": "Session deleted"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
