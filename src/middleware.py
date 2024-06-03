# app/middleware.py
from starlette.middleware.sessions import SessionMiddleware
import os
import sys
# Add the parent directory of src to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noco import MIDDLEWARE_STRING

def add_middleware(app):
    app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_STRING)
