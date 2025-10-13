from aiohttp import web

from modules.http.utils import build_response


def yookassa_webhook(result: web.Request):
    return build_response("ok")
