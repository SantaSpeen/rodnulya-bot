import datetime

from aiohttp import web

from modules.http.utils import build_response


async def health_check(_) -> web.Response:
    now = datetime.datetime.now(datetime.timezone.utc)
    body = {
        "healthy": True,
        "time_iso": now.isoformat(),
        "time_unix": now.timestamp(),
    }
    return build_response(body)

async def _callback_enabled(result: web.Request) -> web.Response:
    body = {
        "message": "Enabled!",
        "callback": {
            "enabled": True,
            "path": result.path,
        }
    }
    return build_response(body)

async def _callback_disabled(result: web.Request) -> web.Response:
    body = {
        "message": "This payment method is currently disabled. Ensure you have configured it correctly.",
        "callback": {
            "enabled": False,
            "path": result.path,
        }
    }
    return build_response(body)
