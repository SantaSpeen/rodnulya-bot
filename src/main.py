import asyncio
from pathlib import Path

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.token import TokenValidationError
from loguru import logger

from database import DatabaseManager
from modules import HTTPServer, webapi
from modules.payments import yookassa_webhook
from bot import router, dp
from shared import config, env, storage


async def _init_database():
    logger.info("[init] Initializing database...")
    db_manager = DatabaseManager(env.sql_uri())
    await db_manager.init_db()
    return db_manager

def _init_bot():
    try:
        return Bot(
            token=config.bot.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    except TokenValidationError:
        logger.error("❌ Invalid bot token. Please check your configuration.")
        return None

def _init_payments_routes():
    logger.info("[init] Initializing payment gateways...")
    payments = [
        # Telegram stars no need webhook
        (config.payments.yookassa, yookassa_webhook),
    ]
    for payment in payments:
        if payment[0].enabled:
            webapi.add_payment(payment[0].webhook_path, payment[1])
        else:
            webapi.disabled_payment(payment[0].webhook_path)

def _init_http():
    logger.info("[init] Initializing HTTP server...")
    http_server = HTTPServer(host="0.0.0.0", port=config.webhooks.port)
    webapi.register_webapi(http_server)
    if config.webapi.fronted.serve:
        http_server.serve_static(
            path_prefix="/",
            directory=Path("data/frontend/src"),
            show_index=False
        )
    return http_server

async def main() -> None:
    """Main application entry point."""
    logger.info("Starting Rodnulya Bot...")

    db_manager = await _init_database()

    if (bot := _init_bot()) is None:
        return

    _init_payments_routes()
    http_server = _init_http()
    await http_server.start()

    storage['db_manager'] = db_manager
    storage['http_server'] = http_server
    storage['bot'] = bot

    try:
        # Start bot polling
        logger.info("[init] Bot started successfully")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Cleanup
        await http_server.stop()
        await db_manager.dispose()
        await bot.session.close()
        logger.info("[init] Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[init] Bot stopped by user")
