from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Callable, Awaitable, Optional

from aiohttp import web
from loguru import logger

from .enum import ApiErrors
from .static_handler import apply_routing_from_json
from .utils import build_error

Handler = Callable[[web.Request], Awaitable[web.Response]]

@web.middleware
async def response_middleware(request: web.Request, handler: Handler) -> web.Response:
    """Catch unhandled exceptions and return unified JSON error."""
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as ex:
        # loguru формат лучше через f-string, чтобы не терять stacktrace
        logger.exception(f"Unhandled exception: {ex}")
        return build_error(ApiErrors.INTERNAL_SERVER_ERROR, 500)

@web.middleware
async def request_id_middleware(request: web.Request, handler: Handler) -> web.Response:
    """Attach X-Request-ID for traceability across systems."""
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request["request_id"] = rid
    resp = await handler(request)
    resp.headers["X-Request-ID"] = rid
    return resp

@web.middleware
async def access_log_middleware(request: web.Request, handler: Handler) -> web.Response:
    """Minimal access log tailored for payment callbacks."""
    start = asyncio.get_event_loop().time()
    try:
        resp = await handler(request)
        return resp
    finally:
        dur_ms = int((asyncio.get_event_loop().time() - start) * 1000)
        logger.info(
            "[HTTP] {method} {path_qs} -> {status} {ms}ms ip={ip} rid={rid}",
            method=request.method,
            path_qs=request.path_qs,
            status=getattr(request, "response", None).status if hasattr(request, "response") else getattr(locals().get('resp', None), 'status', 'unknown'),
            ms=dur_ms,
            ip=request.remote,
            rid=request.get("request_id", "-"),
        )


class HTTPServer:
    """Embeddable aiohttp server for webhooks/callbacks/static."""
    def __init__(self, host: str, port: int, app: Optional[web.Application] = None):
        self.host = host
        self.port = port
        self.app = app or web.Application(
            client_max_size=2 * 1024 * 1024,
            middlewares=[
                access_log_middleware,
                request_id_middleware,
                response_middleware
            ]
        )
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

    def add_route(self, method: str, path: str, handler: Handler) -> None:
        """Добавить обычный route (GET/POST/PUT и т.д.)"""
        self.app.router.add_route(method, path, handler)
        logger.info(f"[HTTP] Added route {method} {path}")

    def add_routes(self, routes: list[tuple[str, str, Handler]]) -> None:
        """Добавить сразу несколько маршрутов"""
        for method, path, handler in routes:
            self.add_route(method, path, handler)

    def serve_static(self, path_prefix: str, directory: Path, *, show_index: bool = False) -> None:
        """Сервим статику"""
        # self.app.router.add_static(path_prefix, directory, show_index=show_index)
        apply_routing_from_json(self, directory, directory / ".." / "routes.json")
        logger.info(f"[HTTP] Serving static files from {directory} at {path_prefix}")

    async def start(self) -> None:
        self.runner = web.AppRunner(self.app, access_log=None)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"[HTTP] HTTP server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("[HTTP] HTTP server stopped")
