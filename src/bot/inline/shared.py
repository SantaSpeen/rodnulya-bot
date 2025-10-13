from typing import Union, Tuple, List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def button(text: str, callback_data: str | None = None, *, url: str | None = None) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data, url=url)

def _looks_like_url(s: str) -> bool:
    return s.startswith(("http://", "https://", "tg://", "mailto:"))

ButtonTuple = Union[
    Tuple[str, str],            # (text, callback_data)  ИЛИ (text, url) — если строка похожа на URL
    Tuple[str, None, str],      # (text, None, url)
    Tuple[str, str, str],       # (text, "url", url)
]

def buttons_row(*buttons: ButtonTuple | InlineKeyboardButton) -> List[InlineKeyboardButton]:
    row: List[InlineKeyboardButton] = []
    for it in buttons:
        if isinstance(it, InlineKeyboardButton):
            row.append(it)
            continue

        # tuple cases
        if len(it) == 2:
            text, second = it
            if _looks_like_url(second):
                row.append(button(text, url=second))
            else:
                row.append(button(text, second))  # callback
        elif len(it) == 3:
            text, kind, value = it
            if kind is None or str(kind).lower() == "url":
                row.append(button(text, url=value))
            else:
                # на всякий — если вдруг передадут (text, "callback", data)
                row.append(button(text, value))
        else:
            raise ValueError(f"Unsupported button tuple: {it!r}")
    return row

def keyboard(*rows: List[ButtonTuple | InlineKeyboardButton]) -> InlineKeyboardMarkup:
    inline_keyboard: List[List[InlineKeyboardButton]] = []
    for row in rows:
        inline_keyboard.append(buttons_row(*row))
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
