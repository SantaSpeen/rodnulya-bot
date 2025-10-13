from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot import router
from bot.inline.userspace import il_accept
from database import User
from shared import i18n


@router.callback_query(F.data.startswith("set_lang:"))
async def on_set_lang(callback: CallbackQuery, session: AsyncSession, user: User):
    lang_code, next_step = callback.data.split(":", 2)[1:]

    # Проверяем, что язык поддерживается
    if lang_code not in i18n.locales_map:
        await callback.answer("❌ Unsupported language", show_alert=True)
        return

    user.update_lang(lang_code)
    await session.commit()

    lang = i18n[lang_code]

    await callback.message.edit_text(lang.select_lang.selected(), reply_markup=None)
    match next_step:
        case "rules":
            await callback.message.answer(lang.rules.greeting(), reply_markup=il_accept("rules", lang))
        case _:
            await callback.message.answer(lang.error.internal_error())

@router.callback_query(F.data.startswith("rules:"))
async def on_set_rules_status(callback: CallbackQuery, session: AsyncSession, user: User, lang):
    mode = callback.data.split(":", 1)[1]

    match mode:
        case "accept":
            user.accept_terms()
            await session.commit()
            await callback.message.edit_text(lang.commands.start(), reply_markup=None)
        case "decline":
            await callback.message.edit_text(lang.rules.decline, reply_markup=None)
