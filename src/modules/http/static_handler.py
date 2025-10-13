from aiohttp import web
from pathlib import Path
import json
from typing import Any

def apply_routing_from_json(
    server,                 # твой modules.http.server.HTTPServer
    static_root: Path,      # корень статических файлов (public/)
    routing_file: Path,     # путь к routing.json
    *,
    cache_assets: bool = True
):
    static_root = static_root.resolve()

    with open(routing_file, "r", encoding="utf-8") as f:
        cfg: dict[str, Any] = json.load(f)

    # ---------- errors ----------
    errors = {int(k): (static_root / v.lstrip("/")).resolve()
              for k, v in (cfg.get("errors") or {}).items()}

    async def _serve_error_page(status: int):
        page = errors.get(status)
        if page and page.is_file():
            # Можно добавить кэш заголовки для ошибок тоже, если нужно
            return web.FileResponse(page, status=status)
        # запасной вариант — простой текст
        return web.Response(text=str(status), status=status)

    @web.middleware
    async def error_pages_mw(request: web.Request, handler):
        try:
            return await handler(request)
        except web.HTTPException as e:
            # отдадим кастомную страницу, если известный код
            if e.status in errors:
                return await _serve_error_page(e.status)
            raise
        except Exception:
            # 500
            return await _serve_error_page(500)

    # Важно подключить middleware ДО регистрации статик/роутов
    server.app.middlewares.append(error_pages_mw)

    # ---------- assets ----------
    # Пример конфигурации:
    # "assets": "/assets"
    # Дополнительно поддержим варианты:
    # "assets": {"/assets": "assets", "/static": "static"}
    assets_cfg = cfg.get("assets")
    if isinstance(assets_cfg, str):
        # Смонтировать /assets на <root>/assets
        prefix = assets_cfg
        directory = (static_root / prefix.lstrip("/")).resolve()
        server.app.router.add_static(prefix, directory, show_index=False)
    elif isinstance(assets_cfg, dict):
        for mount, folder in assets_cfg.items():
            directory = (static_root / str(folder).lstrip("/")).resolve()
            server.app.router.add_static(str(mount), directory, show_index=False)

    # Кэш-заголовки только для ассетов (по пути-префиксу)
    if cache_assets and assets_cfg:
        assets_prefixes = []
        if isinstance(assets_cfg, str):
            assets_prefixes = [assets_cfg.rstrip("/")]
        elif isinstance(assets_cfg, dict):
            assets_prefixes = [p.rstrip("/") for p in assets_cfg.keys()]

        @web.middleware
        async def assets_cache_mw(request: web.Request, handler):
            resp = await handler(request)
            try:
                path = request.path
                if any(path.startswith(p + "/") or path == p for p in assets_prefixes):
                    # недолгий immutable-кэш — поправь под свои нужды
                    resp.headers.setdefault("Cache-Control", "public, max-age=604800, immutable")
                return resp
            except Exception:
                return resp

        server.app.middlewares.append(assets_cache_mw)

    # ---------- routes (файловые) ----------
    # Мапим произвольные пути на конкретные файлы из static_root
    routes = cfg.get("routes") or {}
    for url_path, file_path in routes.items():
        target = (static_root / str(file_path).lstrip("/")).resolve()

        def make_handler(target_path: Path):
            async def _handler(_req: web.Request):
                if target_path.is_file():
                    return web.FileResponse(target_path)
                raise web.HTTPNotFound()
            return _handler

        # GET и HEAD
        server.app.router.add_get(url_path, make_handler(target))
        # server.app.router.add_head(url_path, make_handler(target))

    # ---------- универсальный .html fallback (необязательный) ----------
    # /index -> /index.html, /docs/api -> /docs/api.html
    @web.middleware
    async def dot_html_fallback_mw(request: web.Request, handler):
        try:
            return await handler(request)
        except web.HTTPNotFound:
            raw = request.path.lstrip("/")
            if not raw:
                # "/" → index.html, если не определено в routes
                maybe = static_root / "index.html"
                if maybe.is_file():
                    return web.FileResponse(maybe)
            base = static_root / raw
            if not base.suffix:
                try_html = base.with_suffix(".html")
                if try_html.is_file():
                    return web.FileResponse(try_html)
        # отдаём 404 из кастомного набора (если есть)
        raise web.HTTPNotFound()

    server.app.middlewares.append(dot_html_fallback_mw)
