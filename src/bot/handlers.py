from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.inline.userspace import il_language, il_accept
from bot.shared import router
from database.models import User
from shared import config, i18n


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, user: User) -> None:
    if user.locale == "--":
        if config.i18n.enabled:
            await message.answer(i18n[config.i18n.default].select_lang.start, reply_markup=il_language("rules"))
            return
        else:
            user.update_lang(config.i18n.default)
            await session.commit()

    lang = i18n[user.locale]
    if not user.terms_accepted:
        await message.answer(lang.rules.greeting(), reply_markup=il_accept("rules", lang))
        return

    await message.answer(lang.commands.start(first_name=user.first_name))
