from .utils import health_check, _callback_enabled, _callback_disabled
from ..http.server import HTTPServer

routes = [
    ('GET', '/api/health', health_check),
]

def add_payment(path, callback):
    routes.append(('POST', path, callback))
    routes.append(('GET', path, _callback_enabled))

def disabled_payment(path):
    routes.append(('GET', path, _callback_disabled))

def register_webapi(server: HTTPServer) -> None:
    """Register web API routes and middleware."""
    server.add_routes(routes)

