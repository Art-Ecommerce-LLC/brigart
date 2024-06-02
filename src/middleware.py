# app/middleware.py
from starlette.middleware.sessions import SessionMiddleware
from noco import MIDDLEWARE_STRING

def add_middleware(app):
    app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_STRING)
