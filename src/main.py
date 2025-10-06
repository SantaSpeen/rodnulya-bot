"""Main application entry point."""
import asyncio
import logging
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import select, update

from .bot import router
from .config import settings
from .database import DatabaseManager, Payment, Subscription, User
from .http_server import HTTPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

logger = logging.getLogger(__name__)


async def handle_payment_webhook(data: dict) -> None:
    """Handle payment webhook callback.
    
    Args:
        data: Payment data from webhook
    """
    logger.info(f"Processing payment: {data}")
    
    # Extract payment information
    payment_id = data.get("payment_id")
    telegram_id = data.get("telegram_id")
    amount = data.get("amount")
    currency = data.get("currency", "RUB")
    status = data.get("status", "pending")
    
    if not all([payment_id, telegram_id]):
        logger.error("Missing required payment data")
        return
    
    # Get database session
    db_manager = DatabaseManager(settings.database_url)
    
    async for session in db_manager.get_session():
        try:
            # Check if payment already exists
            result = await session.execute(
                select(Payment).where(Payment.payment_id == payment_id)
            )
            payment = result.scalar_one_or_none()
            
            if payment:
                # Update existing payment
                await session.execute(
                    update(Payment)
                    .where(Payment.payment_id == payment_id)
                    .values(status=status)
                )
                logger.info(f"Updated payment {payment_id} with status {status}")
            else:
                # Create new payment record
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"User not found: {telegram_id}")
                    return
                
                payment = Payment(
                    user_id=user.id,
                    telegram_id=telegram_id,
                    amount=str(amount),
                    currency=currency,
                    payment_id=payment_id,
                    status=status
                )
                session.add(payment)
                logger.info(f"Created new payment record: {payment_id}")
            
            # If payment is successful, activate subscription
            if status == "success":
                # Check if user has active subscription
                result = await session.execute(
                    select(Subscription)
                    .where(Subscription.telegram_id == telegram_id)
                    .where(Subscription.is_active == True)
                )
                subscription = result.scalar_one_or_none()
                
                # Calculate expiration date (30 days from now)
                expires_at = datetime.now() + timedelta(days=30)
                
                if subscription:
                    # Extend existing subscription
                    await session.execute(
                        update(Subscription)
                        .where(Subscription.id == subscription.id)
                        .values(expires_at=expires_at)
                    )
                    logger.info(f"Extended subscription for user {telegram_id}")
                else:
                    # Create new subscription
                    result = await session.execute(
                        select(User).where(User.telegram_id == telegram_id)
                    )
                    user = result.scalar_one_or_none()
                    
                    if user:
                        subscription = Subscription(
                            user_id=user.id,
                            telegram_id=telegram_id,
                            is_active=True,
                            expires_at=expires_at
                        )
                        session.add(subscription)
                        logger.info(f"Created new subscription for user {telegram_id}")
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error processing payment webhook: {e}")
            await session.rollback()


async def main() -> None:
    """Main application entry point."""
    logger.info("Starting Rodnulya Bot...")
    
    # Initialize database
    db_manager = DatabaseManager(settings.database_url)
    await db_manager.init_db()
    logger.info("Database initialized")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register middleware to inject database session
    @dp.update.outer_middleware()
    async def db_session_middleware(handler, event, data):
        async for session in db_manager.get_session():
            data["session"] = session
            return await handler(event, data)
    
    # Register router
    dp.include_router(router)
    
    # Initialize HTTP server
    http_server = HTTPServer(
        host=settings.http_host,
        port=settings.http_port,
        webhook_secret=settings.webhook_secret
    )
    
    # Register payment callback
    http_server.register_payment_callback(handle_payment_webhook)
    
    # Start HTTP server
    await http_server.start()
    
    try:
        # Start bot polling
        logger.info("Bot started successfully")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Cleanup
        await http_server.stop()
        await db_manager.dispose()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
