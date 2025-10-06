"""HTTP server for handling webhooks and callbacks."""
import logging
from typing import Callable

from aiohttp import web

logger = logging.getLogger(__name__)


class HTTPServer:
    """HTTP server for handling webhooks and callbacks."""
    
    def __init__(self, host: str, port: int, webhook_secret: str):
        """Initialize HTTP server.
        
        Args:
            host: Server host
            port: Server port
            webhook_secret: Secret for validating webhooks
        """
        self.host = host
        self.port = port
        self.webhook_secret = webhook_secret
        self.app = web.Application()
        self.runner = None
        self.site = None
        self._payment_callback = None
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup HTTP routes."""
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_post("/webhook/payment", self.payment_webhook)
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        return web.json_response({"status": "ok"})
    
    async def payment_webhook(self, request: web.Request) -> web.Response:
        """Handle payment webhook.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response
        """
        # Validate webhook secret
        auth_header = request.headers.get("X-Webhook-Secret", "")
        if auth_header != self.webhook_secret:
            logger.warning("Invalid webhook secret received")
            return web.json_response(
                {"error": "Invalid webhook secret"},
                status=401
            )
        
        try:
            data = await request.json()
            logger.info(f"Received payment webhook: {data}")
            
            # Call payment callback if registered
            if self._payment_callback:
                await self._payment_callback(data)
            
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Error processing payment webhook: {e}")
            return web.json_response(
                {"error": "Internal server error"},
                status=500
            )
    
    def register_payment_callback(self, callback: Callable) -> None:
        """Register payment callback.
        
        Args:
            callback: Callback function to call when payment webhook is received
        """
        self._payment_callback = callback
    
    async def start(self) -> None:
        """Start HTTP server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"HTTP server started on {self.host}:{self.port}")
    
    async def stop(self) -> None:
        """Stop HTTP server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("HTTP server stopped")
