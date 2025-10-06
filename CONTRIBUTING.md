# Руководство для разработчиков

## Структура проекта

```
rodnulya-bot/
├── src/                        # Исходный код
│   ├── __init__.py
│   ├── main.py                # Точка входа приложения
│   ├── config.py              # Конфигурация через pydantic-settings
│   ├── bot/                   # Модуль бота
│   │   ├── __init__.py
│   │   └── handlers.py        # Обработчики команд
│   ├── database/              # Модуль базы данных
│   │   ├── __init__.py
│   │   └── models.py          # SQLAlchemy модели
│   └── http_server/           # HTTP сервер
│       ├── __init__.py
│       └── server.py          # aiohttp сервер для webhooks
├── Dockerfile                 # Docker образ
├── docker-compose.yml         # Оркестрация контейнеров
├── requirements.txt           # Python зависимости
├── .env.example              # Пример конфигурации
├── .gitignore                # Игнорируемые файлы
├── .dockerignore             # Игнорируемые файлы для Docker
├── README.md                 # Основная документация
├── DEPLOYMENT.md             # Инструкции по развертыванию
├── EXAMPLES.md               # Примеры использования API
└── CONTRIBUTING.md           # Это руководство
```

## Технологический стек

- **Python 3.11+** - язык программирования
- **aiogram 3.22+** - фреймворк для Telegram ботов
- **SQLAlchemy 2.0+** - ORM для работы с базами данных
- **aiohttp 3.9+** - HTTP сервер для webhooks
- **pydantic-settings** - управление конфигурацией
- **PostgreSQL 16** - основная база данных (production)
- **SQLite** - база данных для разработки

## Настройка окружения разработки

### 1. Клонирование репозитория

```bash
git clone https://github.com/SantaSpeen/rodnulya-bot.git
cd rodnulya-bot
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации

```bash
cp .env.example .env
# Отредактируйте .env и укажите BOT_TOKEN
```

### 5. Запуск

```bash
python -m src.main
```

## Стиль кода

### Общие правила

- Используйте type hints для всех функций и методов
- Документируйте функции с помощью docstrings (Google style)
- Максимальная длина строки: 100 символов
- Используйте async/await для асинхронного кода
- Следуйте PEP 8

### Пример функции

```python
async def process_payment(
    payment_id: str,
    telegram_id: int,
    amount: str,
    session: AsyncSession
) -> bool:
    """Process payment and activate subscription.
    
    Args:
        payment_id: Unique payment identifier
        telegram_id: Telegram user ID
        amount: Payment amount as string
        session: Database session
        
    Returns:
        True if payment processed successfully, False otherwise
        
    Raises:
        ValueError: If payment_id is invalid
        DatabaseError: If database operation fails
    """
    # Implementation here
    pass
```

## Работа с базой данных

### Создание новой модели

```python
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

class NewModel(Base):
    """Description of the model."""
    
    __tablename__ = "new_models"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
```

### Работа с сессией

```python
from sqlalchemy import select

async def get_user(telegram_id: int, session: AsyncSession) -> User | None:
    """Get user by telegram ID."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()
```

## Добавление новых обработчиков бота

### Простой обработчик команды

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("mycommand"))
async def cmd_my_command(message: Message) -> None:
    """Handle /mycommand command."""
    await message.answer("Ответ на команду")
```

### Обработчик с использованием базы данных

```python
@router.message(Command("profile"))
async def cmd_profile(message: Message, session: AsyncSession) -> None:
    """Show user profile."""
    telegram_id = message.from_user.id
    
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        await message.answer(f"Имя: {user.first_name}")
    else:
        await message.answer("Пользователь не найден")
```

## Добавление новых HTTP эндпоинтов

```python
async def new_endpoint(self, request: web.Request) -> web.Response:
    """Handle new endpoint.
    
    Args:
        request: HTTP request
        
    Returns:
        HTTP response
    """
    try:
        data = await request.json()
        # Process data
        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.error(f"Error: {e}")
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )

# Регистрация в _setup_routes
self.app.router.add_post("/api/new", self.new_endpoint)
```

## Тестирование

### Проверка импортов

```bash
python test_imports.py
```

### Тестирование HTTP эндпоинтов

```bash
# Health check
curl http://localhost:8080/health

# Payment webhook
curl -X POST http://localhost:8080/webhook/payment \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your_secret" \
  -d '{"payment_id": "test", "telegram_id": 123, "amount": "100", "status": "success"}'
```

## Работа с Git

### Создание веток

```bash
# Создать ветку для новой фичи
git checkout -b feature/new-feature

# Создать ветку для исправления
git checkout -b fix/bug-description
```

### Коммиты

Используйте понятные сообщения коммитов:

```bash
git commit -m "Add payment validation"
git commit -m "Fix subscription expiration logic"
git commit -m "Update README with new instructions"
```

### Pull Request

1. Создайте форк репозитория
2. Создайте ветку для изменений
3. Внесите изменения и сделайте коммит
4. Отправьте изменения в ваш форк
5. Создайте Pull Request в основной репозиторий

## Логирование

Используйте встроенный logger:

```python
import logging

logger = logging.getLogger(__name__)

# Уровни логирования
logger.debug("Отладочная информация")
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.exception("Ошибка с traceback")
```

## Безопасность

### Переменные окружения

Никогда не коммитьте:
- Токены ботов
- Пароли от баз данных
- API ключи
- Секретные ключи webhook

Всегда используйте `.env` файл.

### Валидация входных данных

```python
from pydantic import BaseModel, Field

class PaymentData(BaseModel):
    """Payment webhook data validation."""
    payment_id: str = Field(..., min_length=1, max_length=255)
    telegram_id: int = Field(..., gt=0)
    amount: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    status: str = Field(..., pattern="^(success|pending|failed)$")
```

## Производительность

### Асинхронность

Всегда используйте async/await для I/O операций:

```python
# Правильно
async def fetch_data():
    async with session.get(url) as response:
        return await response.json()

# Неправильно
def fetch_data():
    response = requests.get(url)
    return response.json()
```

### Пулы соединений

SQLAlchemy автоматически управляет пулом соединений.
Не создавайте engine в каждом запросе.

## Документация

При добавлении новых функций:
1. Обновите README.md
2. Добавьте примеры в EXAMPLES.md
3. Обновите DEPLOYMENT.md если требуется
4. Добавьте docstrings к коду

## Получение помощи

- GitHub Issues: [https://github.com/SantaSpeen/rodnulya-bot/issues](https://github.com/SantaSpeen/rodnulya-bot/issues)
- Pull Requests: [https://github.com/SantaSpeen/rodnulya-bot/pulls](https://github.com/SantaSpeen/rodnulya-bot/pulls)

## Лицензия

Проект лицензирован под MIT License. См. [LICENSE](LICENSE) для подробностей.
