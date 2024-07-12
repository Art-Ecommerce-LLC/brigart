# app/middleware.py
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from src.artapi.noco_config import MIDDLEWARE_STRING

def add_middleware(app):
    # Session Middleware
    app.add_middleware(
        SessionMiddleware, 
        secret_key=MIDDLEWARE_STRING,
        )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['https://www.briglightart.com','http://localhost:8000'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    
    # HTTPS Redirect Middleware
    #Prod
    # app.add_middleware(HTTPSRedirectMiddleware) 
