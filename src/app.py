# app/main.py
from fastapi import (
    FastAPI, Request, HTTPException, Depends, Response
)
from contextlib import asynccontextmanager
from fastapi.responses import ( 
    HTMLResponse, JSONResponse, RedirectResponse
)
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import uuid
import stripe
from datetime import datetime, timezone
import asyncio
from sqlalchemy.orm import Session
from typing import List
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import requests
import base64
import ast


from src.artapi import models, crud, schemas
from src.artapi.noco import Noco
from src.artapi.noco_config import OPENAPI_URL, SHIPPING_RATE, PROD_WEBSITE
from src.artapi.stripe_connector import get_stripe_api, StripeAPI
from src.artapi.config import STRIPE_SECRET_KEY, NOCODB_PATH
from src.artapi.logger import setup_logger
from src.artapi.middleware import add_middleware, limiter
from src.artapi.postgres import engine, SessionLocal
from src.artapi.models import (
    Title, TitleQuantity, TotalPrice
)

# Create tables
models.Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Initialize FastAPI App
desc = "Backend platform for BRIG ART"

logger = setup_logger()

async def delete_expired_sessions_task():
    while True:
        try:
            Noco().delete_expired_sessions()
        except Exception as e:
            logger.error(f"Error in lifespan: {e}")
        await asyncio.sleep(60)
        
@asynccontextmanager
async def lifespan(app: FastAPI):
      # Create an instance of Noco
    task = asyncio.create_task(delete_expired_sessions_task())
    yield
    task.cancel()
    try:
        task
    except asyncio.CancelledError:
        logger.info("Background task was cancelled")

if OPENAPI_URL == "None":
    OPENAPI_URL = None
    
app = FastAPI(
    title="Brig API",
    description=desc,
    openapi_url=OPENAPI_URL,
    lifespan=lifespan
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


# Figure out why email get's locked out
# Make better templates
@app.exception_handler(StarletteHTTPException)
@limiter.limit("100/minute")
def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse("error_500.html", {"request": request}, status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
@limiter.limit("100/minute")
def validation_exception_handler(request: Request, exc: RequestValidationError):
    return templates.TemplateResponse("error_500.html", {"request": request}, status_code=400)

@app.exception_handler(Exception)
@limiter.limit("100/minute")
def global_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("error_500.html", {"request": request}, status_code=500)

noco_db = Noco()

@app.get("/", response_class=HTMLResponse)
def homepage(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Homepage accessed by: {request.client.host}")
    try:
        artwork_data = noco_db.get_artwork_data_with_cache(db, crud)
        
        # Sort artwork by sortorder
        sorted_artwork = sorted(
            zip(artwork_data.sortorder, artwork_data.data_uris, artwork_data.titles),
            key=lambda x: x[0]
        )
        
        art_uris, art_titles = zip(*[(art[1], art[2]) for art in sorted_artwork])

        context = {
            "art_uris": art_uris,
            "art_titles": art_titles,
            "brig_logo": noco_db.get_icon_uri_from_title(db, crud, "brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="index.html", context=context)
    except Exception as e:
        logger.error(f"Error in homepage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop/{title}", response_class=HTMLResponse)
@limiter.limit("100/minute") 
def shop(request: Request, title: str, db: Session = Depends(get_db)):
    logger.info(f"Shop page accessed for title {title} by {request.client.host}")
    try:
        height = noco_db.get_artwork_height_from_title(db, crud, title.replace("+", " "))
        width = noco_db.get_artwork_width_from_title(db, crud, title.replace("+", " "))
        context = {
            "img_uri": noco_db.get_art_uri_from_title(db, crud, title.replace("+", " ")),
            "img_title": title.replace("+", " "),
            "price": noco_db.get_art_price_from_title(db, crud, title.replace("+", " ")),
            "brig_logo" : noco_db.get_icon_uri_from_title(db, crud, "brig_logo"),
            "height": str(float(height)),
            "width": str(float(width)),
            "version": noco_db.get_version(),
            "heightmargin": str(float(height) + 1),
            "widthmargin": str(float(width) + 1),
            "fireplacesize": noco_db.get_icon_uri_from_title(db, crud, "collage6")
        }
        return templates.TemplateResponse(request=request, name="shop.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_cart_quantity")
@limiter.limit("100/minute") 
def get_cart_quantity(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Get cart quantity by {request.client.host}")
    try:

        if request.session.get("session_id") is None:
            return JSONResponse({"quantity": 0})
        
        img_quantity_list = noco_db.get_cookie_from_session_id(db, crud, request.session.get("session_id"))
        total_quantity = sum(int(item['quantity']) for item in img_quantity_list)
        logger.info(f"Total cart quantity: {total_quantity}")
        return JSONResponse({"quantity": total_quantity})
    except Exception as e:
        logger.error(f"Error in get_cart_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/shop_art")
@limiter.limit("100/minute") 
def shop_art_url(request: Request, title_quantity: TitleQuantity, db: Session = Depends(get_db)):
    logger.info(f"Shop art URL for {title_quantity.title} by {request.client.host}")
    try:

        cookie_data = {}
        img_quant_dict = {}
        img_quant_dict["title"] = title_quantity.title
        img_quant_dict["quantity"] = title_quantity.quantity
        img_quant_dict["price"] = noco_db.get_art_price_from_title_and_quantity(db, crud, title_quantity.title, title_quantity.quantity)

        if request.session.get("session_id") is None:
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            img_quant_list = []
            img_quant_list.append(img_quant_dict)
            cookie_data["img_quantity_list"] = img_quant_list
            noco_db.post_cookie_session_id_and_cookies(db, crud, session_id, cookie_data)
            return JSONResponse({"quantity": title_quantity.quantity})
        

        session_id = request.session.get("session_id")
        img_quant_list = noco_db.get_cookie_from_session_id(db, crud, session_id)

        for item in img_quant_list:
            if item["title"] == title_quantity.title:
                item["quantity"] = item["quantity"] + title_quantity.quantity
                total_quantity = sum(item["quantity"] for item in img_quant_list)
                item["price"] = noco_db.get_art_price_from_title_and_quantity(db, crud, item["title"], item["quantity"])
                cookiesJson = {
                    "img_quantity_list": img_quant_list
                }
                data = {
                    "Id": int(noco_db.get_cookie_Id_from_session_id(db, crud, session_id)),
                    "sessionids": session_id,
                    "cookies": cookiesJson,
                }
                noco_db.patch_cookies_data(db, crud, data)
                logger.info(f"Updated quantity for {title_quantity.title}, new quantity: {total_quantity}")
                return JSONResponse({"quantity": total_quantity})

        max_items = len(img_quant_list) + 1
        if max_items > 20:
            return JSONResponse({"quantity": "Max items in cart reached"})

        img_quant_list.append(img_quant_dict)
        cookiesJson = {
            "img_quantity_list": img_quant_list
        }
        cookie_id = noco_db.get_cookie_Id_from_session_id(db, crud, session_id)

        if cookie_id == "" :
            noco_db.post_cookie_session_id_and_cookies(db, crud, session_id, cookiesJson)
            return JSONResponse({"quantity": title_quantity.quantity})

        data = {
            "Id": cookie_id,
            "sessionids": session_id,
            "cookies": cookiesJson,
        }

        noco_db.patch_cookies_data(db, crud, data)
        total_quantity = sum(int(item["quantity"]) for item in img_quant_list)
        logger.info(f"Total cart quantity: {total_quantity}")
        return JSONResponse({"quantity": total_quantity})

    except Exception as e:
        logger.error(f"Error in shop_art_url: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop_art/{sessionid}", response_class=HTMLResponse)
@limiter.limit("100/minute") 
def shop_art(request: Request, sessionid: str, db: Session = Depends(get_db)):
    logger.info(f"Shop art page accessed by {request.client.host}")
    try:
   
        if request.session.get("session_id") != sessionid:
            return RedirectResponse(url="/shop_art_menu")       
                         
        img_quant_list = noco_db.get_cookie_from_session_id(db, crud, sessionid)
        art_uris = noco_db.get_artwork_data_with_cache(db, crud, ).data_uris
        titles = noco_db.get_artwork_data_with_cache(db, crud).titles
        img_data_list = []
        for item in img_quant_list: 
            for title in titles:
                if item['title'] in title:
                    img_url = art_uris[titles.index(title)]
                    img_dict = {}
                    img_dict["img_url"] = img_url
                    img_dict["img_title"] = title
                    img_dict["quantity"] = item['quantity']
                    img_dict["price"] = noco_db.get_art_price_from_title_and_quantity(db, crud, item['title'], item['quantity'])
                    img_data_list.append(img_dict)
                    
        context = {
            "img_data_list": img_data_list,
            "brig_logo_url": noco_db.get_icon_uri_from_title(db, crud, "brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="shop_art.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/shop_art_menu", response_class=HTMLResponse)
@limiter.limit("100/minute") 
def shop_art_menu(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Shop art menu page accessed by {request.client.host}")
    try:

        context = {
            "art_uris":noco_db.get_artwork_data_with_cache(db, crud).data_uris,
            "titles": noco_db.get_artwork_data_with_cache(db, crud).titles,
            "price_list": noco_db.get_artwork_data_with_cache(db, crud).prices,
            "brig_logo": noco_db.get_icon_uri_from_title(db, crud, "brig_logo"),
            "version" : noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="shop_art_menu.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art_menu: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/giclee_prints", response_class=HTMLResponse)
@limiter.limit("100/minute") 
def shop_giclee_prints(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Giclee prints page accessed by {request.client.host}")
    try:

        context = {
            "giclee_prints": noco_db.get_artwork_data_with_cache(db, crud).data_uris,
            "brig_logo_url": noco_db.get_icon_uri_from_title(db, crud,"brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="gicle_prints.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_giclee_prints: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/post_total_price")
@limiter.limit("100/minute") 
def post_total_price(request: Request, total_price: TotalPrice, db: Session = Depends(get_db)):
    logger.info(f"Post total price {total_price.totalPrice} by {request.client.host}")
    try:
        
        img_quant_list = noco_db.get_cookie_from_session_id(db, crud, request.session.get("session_id"))
        cookie_price_total = sum(int(item["price"]) for item in img_quant_list)
        if cookie_price_total == total_price.totalPrice:
            return JSONResponse({"totalPrice": total_price.totalPrice})
        else:
            return JSONResponse({"totalPrice": cookie_price_total})
        
    except Exception as e:
        logger.error(f"Error in post_total_price: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/increase_quantity")
@limiter.limit("100/minute") 
def increase_quantity(request: Request, title: Title, db: Session = Depends(get_db)):
    logger.info(f"Increase quantity for {title.title} by {request.client.host}")
    try:

        session_id = request.session.get("session_id")
        if not session_id:
            logger.info(f"Session ID not found from request {request.client.host}")
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = noco_db.get_cookie_from_session_id(db, crud, session_id)
        matched_price = None
        # Check if the title is already in the cart
        for each in img_quant_list:
            if title.title == each["title"]:
                each["quantity"] += 1  # Increment quantity
                each["price"] = noco_db.get_art_price_from_title_and_quantity(db, crud, each["title"], each["quantity"])
                matched_price = each["price"]
                break
        else:
            raise HTTPException(status_code=404, detail="Title not found in cart")

        patch_data = {
            "Id": int(noco_db.get_cookie_Id_from_session_id(db, crud, session_id)),
            "sessionids": session_id,
            "cookies": {
                "img_quantity_list": img_quant_list,
            },    
        }

        noco_db.patch_cookies_data(db, crud, patch_data)
        return JSONResponse({"price": matched_price})

    except Exception as e:
        logger.error(f"Failed to increase quantity for {title.title} by {request.client.host}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/decrease_quantity")
@limiter.limit("100/minute") 
def decrease_quantity(request: Request, title: Title, db: Session = Depends(get_db)):
    logger.info(f"Decrease quantity for {title.title} by {request.client.host}")
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            logger.info(f"Session ID not found from request {request.client.host}")
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = noco_db.get_cookie_from_session_id(db, crud, session_id)
        matched_price = None

        for each in img_quant_list:
            if title.title == each["title"]:
                if each["quantity"] == 1:
                    img_quant_list.remove(each)
                    matched_price = each["price"]
                    break

                each["quantity"] -= 1  
                each["price"] = noco_db.get_art_price_from_title_and_quantity(db, crud, each["title"], each["quantity"])
                matched_price = each["price"]
                break
        else:
            raise HTTPException(status_code=404, detail="Title not found in cart")

        if img_quant_list == []:
            noco_db.delete_session_cookie(db, crud, session_id)
            request.session.pop("session_id")
            return JSONResponse({"price": 0})

        patch_data = {
            "Id": int(noco_db.get_cookie_Id_from_session_id(db, crud, session_id)),
            "sessionids": session_id,
            "cookies": {
                "img_quantity_list": img_quant_list
            }
        }

        noco_db.patch_cookies_data(db, crud, patch_data)
        return JSONResponse({"price": matched_price})
    
    except Exception as e:
        logger.error(f"Error in decrease_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/delete_item")
@limiter.limit("100/minute") 
def delete_item(request: Request, title: Title, db: Session = Depends(get_db)):
    logger.info(f"Delete item by {request.client.host}")
    try:

        titles = noco_db.get_artwork_data_with_cache(db, crud).titles
        if title.title not in titles:
            logger.warning(f"Title {title.title} not found")
            raise HTTPException(status_code=404, detail="Title not found")

        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID not found")

        img_quant_list = noco_db.get_cookie_from_session_id(db, crud, session_id)
        matched_price = None

        for each in img_quant_list:
            if title.title == each["title"]:
                img_quant_list.remove(each)
                matched_price = each["price"]
                break

        if img_quant_list == []:
            noco_db.delete_session_cookie(db, crud, session_id)
            request.session.pop("session_id")
            return JSONResponse({"price": 0})
        
        patch_data = {
            "Id": int(noco_db.get_cookie_Id_from_session_id(db, crud, session_id)),
            "sessionids": session_id,
            "cookies": {
                "img_quantity_list": img_quant_list
            }
        }

        noco_db.patch_cookies_data(db, crud, patch_data)
        return JSONResponse({"price": matched_price})
    except Exception as e:
        logger.error(f"Error in delete_item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_session_id")
@limiter.limit("100/minute") 
def get_session_id(request: Request, db: Session = Depends(get_db)):
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

@app.get("/favicon.ico")
@limiter.limit("100/minute") 
def favicon(request: Request):
    return RedirectResponse(url="/static/favicon.ico")

@app.get("/return_policy", response_class=HTMLResponse)
@limiter.limit("100/minute") 
def return_policy(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Return policy page accessed by {request.client.host}")
    try:
        context = {
            "brig_logo": noco_db.get_icon_uri_from_title(db, crud, "brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="return_policy.html", context=context)
    except Exception as e:
        logger.error(f"Error in return_policy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/privacy_policy", response_class=HTMLResponse)
@limiter.limit("100/minute") 
def return_policy(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Return policy page accessed by {request.client.host}")
    try:
        context = {
            "brig_logo": noco_db.get_icon_uri_from_title(db, crud, "brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="privacy_policy.html", context=context)
    except Exception as e:
        logger.error(f"Error in return_policy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/terms_and_conditions", response_class=HTMLResponse)
@limiter.limit("100/minute")
def terms_and_conditions(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Terms and conditions page accessed by {request.client.host}")
    try:
        context = {
            "brig_logo": noco_db.get_icon_uri_from_title(db, crud, "brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="terms_and_conditions.html", context=context)
    except Exception as e:
        logger.error(f"Error in terms_and_conditions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_session_time")
@limiter.limit("100/minute") 
def get_session_time(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Get session time by {request.client.host}")
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID not found")

        session_creation_time = noco_db.get_cookie_session_begginging_time(db, crud, session_id)
        if session_creation_time == "":
            return JSONResponse({"remaining_time": 0})

        current_time = datetime.now(timezone.utc)
        elapsed_time = (current_time - session_creation_time.replace(tzinfo=timezone.utc)).total_seconds()
        remaining_time = max(0, 900 - elapsed_time)  # 30 minutes = 1800 seconds

        return JSONResponse({"remaining_time": int(remaining_time)})

    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid session creation time format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/delete_session")
@limiter.limit("100/minute") 
def delete_session(request: Request, db: Session = Depends(get_db)):
    logger.info(f"Delete session by {request.client.host}")
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID not found")
        
        noco_db.delete_session_cookie(db, crud, session_id)
        request.session.pop("session_id")
        return JSONResponse({"message": "Session deleted"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/checkout/{sessionid}", response_class=HTMLResponse)
@limiter.limit("100/minute") 
def shop_checkout(request: Request, sessionid: str, db: Session = Depends(get_db), stripe_api: StripeAPI = Depends(get_stripe_api)):
    logger.info(f"Checkout page accessed by {request.client.host}")
    try:
        if request.session.get("session_id") != sessionid:
            return RedirectResponse(url="/shop_art_menu")
        
        img_quant_list = noco_db.get_cookie_from_session_id(db, crud, sessionid)
        img_path = noco_db.get_artwork_data_with_cache(db, crud).art_paths
        titles = noco_db.get_artwork_data_with_cache(db, crud).titles
        path_list = []

        for item in img_quant_list:
            if item["title"] not in titles:
                raise HTTPException(status_code=404, detail=f"Title not found, Abuse detected {request.client.host}")
            else: 
                full_path = f"{NOCODB_PATH}/{img_path[titles.index(item['title'])]}"
                path_list.append(full_path)

        line_items = stripe_api.sync_products(img_quant_list, path_list)

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
                'shipping_rate' : SHIPPING_RATE,
            }],
        )
        return RedirectResponse(url=payment_link.url)
    
    except Exception as e:
        logger.error(f"Error in shop_checkout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
# Dev APIS
# Update the artwork order in the database and sync there uris
# @app.get("/sync-uris", response_class=JSONResponse)
# def sync_uris_endpoint(request: Request, db: Session = Depends(get_db)):
#     """
#     Endpoint to synchronize artwork URIs by generating reduced-resolution Data URIs
#     from existing images and updating the database accordingly.
#     """
#     logger.info(f"/sync-uris endpoint accessed by: {request.client.host}")
#     try:
#         noco_db.sync_data_uris(db, crud)
#         return {"message": "Artwork URIs synchronized successfully."}
#     except Exception as e:
#         logger.error(f"Error syncing artwork URIs: {e}")
#         raise HTTPException(status_code=500, detail="An error occurred while syncing artwork URIs.")
    

# @app.get("/reorder_artwork", response_class=HTMLResponse)
# @limiter.limit("100/minute")
# def reorder_artwork_page(request: Request, db: Session = Depends(get_db)):
#     try:
#         # Fetch artwork URIs and titles from the database
#         art_uris = noco_db.get_artwork_data_with_cache(db, crud).data_uris
#         art_titles = noco_db.get_artwork_data_with_cache(db, crud).titles
        
#         context = {
#             "art_uris": art_uris,
#             "art_titles": art_titles,
#             "version": noco_db.get_version()
#         }
        
#         return templates.TemplateResponse("drag_and_drop.html", {"request": request, **context})
    
#     except Exception as e:
#         logger.error(f"Error in reorder_artwork_page: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
# @app.post("/update_artwork_order")
# @limiter.limit("100/minute")
# async def update_artwork_order(request: Request, db: Session = Depends(get_db)):
#     form_data = await request.form()
#     new_order = form_data.getlist("art_order[]")
#     logger.info(f"New artwork order: {new_order}")
    
#     try:
#         # Update the artwork order in the database
#         noco_db.update_artwork_order(db, new_order)
        
#         return RedirectResponse(url="/", status_code=302)
    
#     except Exception as e:
#         logger.error(f"Failed to update artwork order: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
# @app.post("/update_artwork_order")
# def update_artwork_order(order: list[schemas.ArtworkOrder], db: Session = Depends(get_db)) -> None:
#     try:
#         # Temporarily disable autoflush
#         with db.no_autoflush:
#             # Update the sort order in the database using the provided title and new sortOrder
#             for item in order:
#                 artwork = crud.get_artwork_by_title(db, item.title)
#                 if artwork:
#                     artwork.sortorder = item.sortOrder  # Set the new sort order
#                     artwork.updated_at = datetime.now(timezone.utc)  # Ensure updated_at is set correctly

#             # Commit the changes to the database
#             db.commit()

#         # Clear cache to reflect changes if using caching
#         noco_db.clear_artwork_data_cache()
#     except Exception as e:
#         db.rollback()  # Rollback in case of error
#         raise HTTPException(status_code=500, detail=f"Internal server error")
    
# @app.get("/reorder_artwork", response_class=HTMLResponse)
# def reorder_artwork_page(request: Request, db: Session = Depends(get_db)):
#     try:
#         # Fetch artwork URIs, titles, and sort order from the database
#         artwork_data = noco_db.get_artwork_data_with_cache(db, crud)
        
#         # Sort artwork by sortorder
#         sorted_artwork = sorted(
#             zip(artwork_data.sortorder, artwork_data.data_uris, artwork_data.titles),
#             key=lambda x: x[0]
#         )
        
#         artworks = list(zip([art[1] for art in sorted_artwork], [art[2] for art in sorted_artwork]))
        
#         context = {
#             "artworks": artworks,
#             "version": noco_db.get_version()
#         }
#         return templates.TemplateResponse("drag_and_drop.html", {"request": request, **context})
#     except Exception as e:
#         logger.error(f"Error in reorder_artwork_page: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/stream_image/{artwork_id}")
@limiter.limit("100/minute")
def stream_reduced_image(artwork_id: int, db: Session = Depends(get_db)):
    try:
        # Fetch the artwork data by ID
        artwork = crud.get_artwork_by_id(db, artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail="Artwork not found")
        
        # Reduce the resolution of the image
        img_path = ast.literal_eval(artwork.img)
        img_data = requests.get(f"{noco_db.base_url}/{img_path[0]['path']}").content
        reduced_res_image = noco_db.convert_to_data_uri(img_data)

        # Decode the base64 image data
        image_data = base64.b64decode(reduced_res_image.split(',')[1])
        
        # Stream the image
        return Response(content=image_data, media_type="image/jpeg")
    
    except Exception as e:
        logger.error(f"Error streaming image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

# @app.get("/download_image/{artwork_id}")
# def download_reduced_image(artwork_id: int, db: Session = Depends(get_db)):
#     try:
#         # Fetch the artwork data by ID
#         artwork = crud.get_artwork_by_id(db, artwork_id)
#         if not artwork:
#             raise HTTPException(status_code=404, detail="Artwork not found")
        
#         # Reduce the resolution of the image
#         img_path = ast.literal_eval(artwork.img)
#         img_data = requests.get(f"{noco_db.base_url}/{img_path[0]['path']}").content
#         reduced_res_image = noco_db.convert_to_data_uri(img_data)

#         # Decode the base64 image data
#         image_data = base64.b64decode(reduced_res_image.split(',')[1])
        
#         # Prepare the response headers for download
#         headers = {
#             'Content-Disposition': f'attachment; filename="{artwork.img_label}_reduced.jpg"'
#         }
#         return Response(content=image_data, media_type="image/jpeg", headers=headers)
    
#     except Exception as e:
#         logger.error(f"Error downloading image: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/export_google_feed/")
@limiter.limit("100/minute")
def export_google_feed(db: Session = Depends(get_db)):
    try:
        # Fetch artwork data from the backend
        artwork_data = noco_db.get_artwork_data_with_cache(db, crud)
        
        # Create the root RSS element and associate the Google namespace with the "g" prefix
        ET.register_namespace('g', "http://base.google.com/ns/1.0")
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        
        # Channel info (customize as needed)
        ET.SubElement(channel, 'title').text = "Brig Light Art"
        ET.SubElement(channel, 'link').text = PROD_WEBSITE
        ET.SubElement(channel, 'description').text = "Brig Light Art products"
        
        # Iterate through the artwork data and create items
        for title, price, id, height, width in zip(artwork_data.titles, artwork_data.prices, artwork_data.Ids, artwork_data.heights, artwork_data.widths):
            item = ET.SubElement(channel, 'item')
            ET.SubElement(item, '{http://base.google.com/ns/1.0}id').text = str(id)
            ET.SubElement(item, '{http://base.google.com/ns/1.0}title').text = title
            # Make the description the size of the artwork
            cutheight = str(float(height) + 1)
            cutwidth = str(float(width) + 1)
            description = f"Size: ~{str(float(height))} W x ~{str(float(width))} H inches. Cut to size: ~{cutheight} W x ~{cutwidth} H inches with a 1 inch white border."
            ET.SubElement(item, '{http://base.google.com/ns/1.0}description').text = description # Customize as needed

            ET.SubElement(item, '{http://base.google.com/ns/1.0}link').text = f"{PROD_WEBSITE}/shop/{str(title).replace(' ', '+')}"
            ET.SubElement(item, '{http://base.google.com/ns/1.0}image_link').text = f"{PROD_WEBSITE}/stream_image/{str(id)}"  # Replace with actual image link
            ET.SubElement(item, '{http://base.google.com/ns/1.0}price').text = f"{price} USD"
            ET.SubElement(item, '{http://base.google.com/ns/1.0}condition').text = "new"  # Example condition
            ET.SubElement(item, '{http://base.google.com/ns/1.0}availability').text = "in stock"  # Example availability
        
        # Convert the XML tree to a string
        xml_str = ET.tostring(rss, encoding='utf-8')
        
        # Parse the string for pretty printing
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Return the pretty-printed XML as a response
        return Response(content=pretty_xml, media_type="application/xml")
    
    except Exception as e:
        logger.error(f"Error in export_google_feed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
