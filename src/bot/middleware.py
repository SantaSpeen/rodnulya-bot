from aiogram.types import Update
from loguru import logger
from sqlalchemy import select

from database import User
from shared import config, storage, i18n
from .shared import dp


@dp.update.outer_middleware()
async def db_session_middleware(handler, event, data):
    async for session in storage['db_manager'].get_session():

        # Пытаемся достать from_user из разных типов апдейтов
        tg_from = None
        if isinstance(event, Update):
            if event.message:
                tg_from = event.message.from_user
            elif event.callback_query:
                tg_from = event.callback_query.from_user
            elif event.my_chat_member:
                tg_from = event.my_chat_member.from_user
            elif event.chat_member:
                tg_from = event.chat_member.from_user
            elif event.inline_query:
                tg_from = event.inline_query.from_user
            elif event.chosen_inline_result:
                tg_from = event.chosen_inline_result.from_user
            elif event.shipping_query:
                tg_from = event.shipping_query.from_user
            elif event.pre_checkout_query:
                tg_from = event.pre_checkout_query.from_user
        else:
            # на всякий случай, если сюда прилетит уже конкретное событие
            tg_from = getattr(event, "from_user", None)

        user = None
        lang = None
        if tg_from is not None:
            result = await session.execute(
                select(User).where(User.telegram_id == tg_from.id)
            )
            user = result.scalar_one_or_none()
            if not user:
                telegram_id = tg_from.id
                # Create new user
                user = User(
                    telegram_id=telegram_id,
                    first_name=tg_from.first_name,
                    last_name=tg_from.last_name,
                    username=tg_from.username,
                    locale="--",
                    is_admin=telegram_id in config.bot.admins
                )
                session.add(user)
                await session.commit()
                logger.info(f"[middleware] New user created: {telegram_id}")
                await session.flush()  # чтобы у user появился id в текущей сессии

            if user.banned:
                logger.info(f"[middleware] Banned user {user.telegram_id} tried to interact with the bot.")

                # Пытаемся удалить сообщение от забаненного пользователя, если это возможно
                try:
                    if event.message:
                        await event.message.delete()
                    elif event.callback_query and event.callback_query.message:
                        await event.callback_query.message.delete()
                except Exception:
                    pass

                # Просто игнорируем апдейт от забаненного пользователя
                return None

            if user.locale == "--":
                lang = i18n[config.i18n.default]
            else:
                lang = i18n[user.locale]

        data["session"] = session
        data["user"] = user
        data["lang"] = lang
        return await handler(event, data)
    return None
