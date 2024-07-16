from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.artapi.noco_config import MIDDLEWARE_STRING
from fastapi import FastAPI
import os
# Initialize the Limiter
limiter = Limiter(key_func=get_remote_address)

origin = os.getenv("origin")

def add_middleware(app : FastAPI):
    # Rate Limit Middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Session Middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=MIDDLEWARE_STRING,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origin,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # HTTPS Redirect Middleware
    # app.add_middleware(HTTPSRedirectMiddleware)
