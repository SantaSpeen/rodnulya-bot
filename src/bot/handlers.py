"""Bot handlers for processing user messages."""
import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import User

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    """Handle /start command.
    
    Args:
        message: Telegram message
        session: Database session
    """
    telegram_id = message.from_user.id
    
    # Check if user exists
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        session.add(user)
        await session.commit()
        logger.info(f"New user created: {telegram_id}")
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я бот Роднуля для управления подписками Remnawave.\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать справку\n"
        "/status - Проверить статус подписки"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command.
    
    Args:
        message: Telegram message
    """
    await message.answer(
        "📚 Справка по боту:\n\n"
        "Этот бот предназначен для управления подписками Remnawave.\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/status - Проверить статус вашей подписки\n\n"
        "Для приобретения подписки свяжитесь с администратором."
    )


@router.message(Command("status"))
async def cmd_status(message: Message, session: AsyncSession) -> None:
    """Handle /status command.
    
    Args:
        message: Telegram message
        session: Database session
    """
    from ..database.models import Subscription
    
    telegram_id = message.from_user.id
    
    # Get user subscription
    result = await session.execute(
        select(Subscription)
        .where(Subscription.telegram_id == telegram_id)
        .where(Subscription.is_active == True)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        if subscription.expires_at:
            await message.answer(
                f"✅ Ваша подписка активна!\n"
                f"Срок действия до: {subscription.expires_at.strftime('%d.%m.%Y %H:%M')}"
            )
        else:
            await message.answer("✅ У вас есть активная подписка без срока действия!")
    else:
        await message.answer(
            "❌ У вас нет активной подписки.\n\n"
            "Для приобретения подписки свяжитесь с администратором."
        )
