from aiogram.types import InlineKeyboardMarkup

from shared import i18n
from .shared import keyboard


def il_language(next_step) -> InlineKeyboardMarkup:
    langs = i18n.locales_map
    rows = []
    row = []

    # Не больше 2х кнопок в ряд
    for _, lang in langs.items():
        lang_name = f"{lang.flag} {lang.native_name}"
        row.append((lang_name, f"set_lang:{lang.code}:{next_step}"))

        if len(row) == 2:
            rows.append(row)
            row = []

    # если осталась неполная строка
    if row:
        rows.append(row)

    return keyboard(*rows)

def il_accept(callback_class: str, lang) -> InlineKeyboardMarkup:
    return keyboard(
        [(lang.buttons.accept, f"{callback_class}:accept")],
        [(lang.buttons.decline, f"{callback_class}:decline")]
    )
