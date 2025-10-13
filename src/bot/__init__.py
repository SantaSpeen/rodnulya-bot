"""Bot package."""
from .shared import router, dp

# Импортируем все обработчики, коллбэки и middleware, чтобы они зарегистрировались
from . import handlers
from . import callbacks
from . import middleware

__all__ = [
    'router',
    'dp'
]
