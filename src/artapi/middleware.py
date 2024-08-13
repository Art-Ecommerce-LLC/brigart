from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .noco_config import MIDDLEWARE_STRING
from .config import DEVELOPMENT_ORIGINS, PRODUCTION_ORIGINS, ENVIORNMENT, CSP_POLICY, DEVELOPMENT_HOSTS, PRODUCTION_HOSTS

# Initialize the Limiter
limiter = Limiter(key_func=get_remote_address)

class ContentSecurityPolicyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, csp_policy: str):
        super().__init__(app)
        self.csp_policy = csp_policy

    async def dispatch(self, request: Receive, call_next):
        response: Response = await call_next(request)
        response.headers['Content-Security-Policy'] = self.csp_policy
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Receive, call_next):
        try:
            response = await call_next(request)
        except Exception as e:
            raise
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Receive, call_next):
        response = await call_next(request)
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

def get_allowed_origins() -> list:
    """Get the list of allowed origins based on the environment."""
    if ENVIORNMENT == "production":
        origins = PRODUCTION_ORIGINS.split(",")
    else:
        origins = DEVELOPMENT_ORIGINS.split(",")
    return origins

def get_allowed_hosts() -> list:
    """Get the list of allowed hosts based on the environment."""
    if ENVIORNMENT == "production":
        hosts = PRODUCTION_HOSTS.split(",")
    else:
        hosts = DEVELOPMENT_HOSTS.split(",")
    return hosts

def add_middleware(app: FastAPI):
    # Rate Limit Middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Session Middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=MIDDLEWARE_STRING,
    )

    # CORS Middleware
    if ENVIORNMENT == "production":
        origins = PRODUCTION_ORIGINS.split(",")
        app.add_middleware(HTTPSRedirectMiddleware)
    else:
        origins = DEVELOPMENT_ORIGINS.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=get_allowed_hosts()
    )

    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
        compresslevel=9,
    )
    app.add_middleware(
        ContentSecurityPolicyMiddleware,
        csp_policy=CSP_POLICY
    )

    # Additional Middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)