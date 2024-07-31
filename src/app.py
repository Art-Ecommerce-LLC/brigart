# app/main.py
from fastapi import (
    FastAPI, Request, HTTPException, Depends
)
from contextlib import asynccontextmanager
from fastapi.responses import ( 
    HTMLResponse, JSONResponse, RedirectResponse
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from src.artapi.config import STRIPE_SECRET_KEY, NOCODB_PATH
from src.artapi.logger import logger
from src.artapi.middleware import add_middleware, limiter
from src.artapi.models import (
    Title, TitleQuantity, TotalPrice
)
from src.artapi.noco import Noco
import os
import uuid
from src.artapi.noco_config import OPENAPI_URL, SHIPPING_RATE
import datetime
import stripe
from datetime import datetime, timezone
from src.artapi.nocodb_connector import get_noco_db
from src.artapi.stripe_connector import get_stripe_api, StripeAPI
import asyncio
# Initialize FastAPI App
desc = "Backend platform for BRIG ART"

if OPENAPI_URL == "None":
    OPENAPI_URL = None

noco_db = get_noco_db()

async def delete_expired_sessions_task():
    while True:
        try:
            await noco_db.delete_expired_sessions()
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
        await task
    except asyncio.CancelledError:
        logger.info("Background task was cancelled")
    
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


@app.get("/", response_class=HTMLResponse)
@limiter.limit("100/minute")
async def homepage(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Homepage accessed by: {request.client.host}")
    try:
        context = {
            "art_uris": noco_db.get_artwork_data_with_cache().data_uris,
            "art_titles": noco_db.get_artwork_data_with_cache().titles,
            "brig_logo": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="index.html", context=context)
    except Exception as e:
        logger.error(f"Error in homepage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/shop/{title}", response_class=HTMLResponse)
@limiter.limit("100/minute") 
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
@limiter.limit("100/minute") 
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
@limiter.limit("100/minute") 
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
@limiter.limit("100/minute") 
async def shop_art(request: Request, sessionid: str, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Shop art page accessed by {request.client.host}")
    try:
        if request.session.get("session_id") != sessionid:
            logger.warning(f"Session ID does not match {request.client.host}")
            return RedirectResponse(url="/shop_art_menu")       
                         
        img_quant_list = noco_db.get_cookie_from_session_id(sessionid)
        art_uris = noco_db.get_artwork_data_with_cache().data_uris
        titles = noco_db.get_artwork_data_with_cache().titles
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
@limiter.limit("100/minute") 
async def shop_art_menu(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Shop art menu page accessed by {request.client.host}")
    try:
        
        context = {
            "art_uris":noco_db.get_artwork_data_with_cache().data_uris,
            "titles": noco_db.get_artwork_data_with_cache().titles,
            "price_list": noco_db.get_artwork_data_with_cache().prices,
            "brig_logo": noco_db.get_icon_uri_from_title("brig_logo"),
            "version" : noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="shop_art_menu.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_art_menu: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/giclee_prints", response_class=HTMLResponse)
@limiter.limit("100/minute") 
async def shop_giclee_prints(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Giclee prints page accessed by {request.client.host}")
    try:
        context = {
            "giclee_prints": noco_db.get_artwork_data_with_cache().data_uris,
            "brig_logo_url": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="gicle_prints.html", context=context)
    except Exception as e:
        logger.error(f"Error in shop_giclee_prints: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/post_total_price")
@limiter.limit("100/minute") 
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
@limiter.limit("100/minute") 
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
@limiter.limit("100/minute") 
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
@limiter.limit("100/minute") 
async def delete_item(request: Request, title: Title, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Delete item by {request.client.host}")
    try:

        # Get list of artwork titles
        titles = noco_db.get_artwork_data_with_cache().titles
        if title.title not in titles:
            logger.warning(f"Title {title.title} not found")
            raise HTTPException(status_code=404, detail="Title not found")

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


@app.get("/favicon.ico")
@limiter.limit("100/minute") 
async def favicon(request: Request):
    return RedirectResponse(url="/static/favicon.ico")


@app.get("/return_policy", response_class=HTMLResponse)
@limiter.limit("100/minute") 
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

@app.get("/privacy_policy", response_class=HTMLResponse)
@limiter.limit("100/minute") 
async def return_policy(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Return policy page accessed by {request.client.host}")
    try:
        context = {
            "brig_logo": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="privacy_policy.html", context=context)
    except Exception as e:
        logger.error(f"Error in return_policy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/terms_and_conditions", response_class=HTMLResponse)
@limiter.limit("100/minute")
async def terms_and_conditions(request: Request, noco_db: Noco = Depends(get_noco_db)):
    logger.info(f"Terms and conditions page accessed by {request.client.host}")
    try:
        context = {
            "brig_logo": noco_db.get_icon_uri_from_title("brig_logo"),
            "version": noco_db.get_version()
        }
        return templates.TemplateResponse(request=request, name="terms_and_conditions.html", context=context)
    except Exception as e:
        logger.error(f"Error in terms_and_conditions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_session_time")
@limiter.limit("100/minute") 
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
@limiter.limit("100/minute") 
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

@app.get("/checkout/{sessionid}", response_class=HTMLResponse)
@limiter.limit("100/minute") 
async def shop_checkout(request: Request, sessionid: str, noco_db: Noco = Depends(get_noco_db), stripe_api: StripeAPI = Depends(get_stripe_api)):
    logger.info(f"Checkout page accessed by {request.client.host}")
    try:
        # Create payment link with the items in the cart
        if request.session.get("session_id") != sessionid:
            logger.warning(f"Session ID does not match {request.client.host}")
            return RedirectResponse(url="/shop_art_menu")
        
        img_quant_list = noco_db.get_cookie_from_session_id(sessionid)

        # Sync with stripe products
        # Search product list for title, only the active products

        img_path = noco_db.get_artwork_data_with_cache().art_paths
        titles = noco_db.get_artwork_data_with_cache().titles
        path_list = []
        for item in img_quant_list:
            if item["title"] not in titles:
                logger.warning(f"Title {item['title']} not found in titles")
                raise HTTPException(status_code=404, detail="Title not found")
            else: 
                full_path = f"{NOCODB_PATH}/{img_path[titles.index(item['title'])]}"
                path_list.append(full_path)


        line_items= stripe_api.sync_products(img_quant_list, path_list)

        # products = stripe.Product.list(limit=300)
        # line_items = []
        # for product in products:
        #     for item in img_quant_list:
        #         if product.name == item["title"]:
        #             line_items.append({
        #                 'price': product.default_price,
        #                 'quantity': item["quantity"],
        #             })
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
