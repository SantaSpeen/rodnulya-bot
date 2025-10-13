from aiohttp import web

from shared import config
from .enum import ApiErrors, _get_code

_headers = {
    'Access-Control-Allow-Origin': config.webapi.security.cors.origin,
    'Access-Control-Allow-Methods': ", ".join(config.webapi.security.cors.methods),
    'Access-Control-Allow-Headers': 'Content-Type, X-YooKassa-Signature',
}

def build_error(message: ApiErrors, status_code=500):
    body = {
        'error': {
            'code': _get_code(message),
            'message': message.value
        }
    }
    return web.json_response(body, status=status_code)

def build_response(response, headers=None, status_code=200):
    if headers is None:
        headers = {}
    headers.update(_headers)
    body = {"response": response}
    return web.json_response(body, status=status_code, headers=headers)
