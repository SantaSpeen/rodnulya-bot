# rodnulya-bot
Роднуля бот для администрирование и продажи подписок Remnawave

## Описание

Telegram-бот на базе aiogram 3.22+ для управления подписками Remnawave с поддержкой:
- Базы данных (PostgreSQL и SQLite) через SQLAlchemy
- HTTP-сервера для обработки вебхуков (например, уведомления об оплате)
- Docker и Docker Compose для развертывания

## Требования

- Python 3.11+
- Docker и Docker Compose (для контейнеризации)
- PostgreSQL 16 (опционально, если используется через docker-compose)

## Установка

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/SantaSpeen/rodnulya-bot.git
cd rodnulya-bot
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Отредактируйте `.env` и укажите ваш токен бота:
```env
BOT_TOKEN=your_bot_token_here
```

5. Запустите бота:
```bash
python -m src.main
```

### Установка через Docker Compose

1. Клонируйте репозиторий:
```bash
git clone https://github.com/SantaSpeen/rodnulya-bot.git
cd rodnulya-bot
```

2. Создайте файл `.env` и укажите ваш токен бота:
```bash
echo "BOT_TOKEN=your_bot_token_here" > .env
echo "WEBHOOK_SECRET=your_secure_secret_here" >> .env
```

3. Запустите через Docker Compose:
```bash
docker-compose up -d
```

4. Проверьте логи:
```bash
docker-compose logs -f bot
```

## Конфигурация

Все настройки задаются через переменные окружения в файле `.env`:

- `BOT_TOKEN` - токен Telegram бота (обязательно)
- `DATABASE_TYPE` - тип базы данных: `sqlite` или `postgresql` (по умолчанию: `sqlite`)
- `DATABASE_URL` - URL подключения к базе данных
- `HTTP_HOST` - хост HTTP-сервера (по умолчанию: `0.0.0.0`)
- `HTTP_PORT` - порт HTTP-сервера (по умолчанию: `8080`)
- `WEBHOOK_SECRET` - секретный ключ для валидации вебхуков

## Структура проекта

```
rodnulya-bot/
├── src/
│   ├── __init__.py
│   ├── main.py              # Основной файл приложения
│   ├── config.py            # Управление конфигурацией
│   ├── bot/
│   │   ├── __init__.py
│   │   └── handlers.py      # Обработчики команд бота
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py        # Модели базы данных
│   └── http_server/
│       ├── __init__.py
│       └── server.py        # HTTP-сервер для вебхуков
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Использование

### Команды бота

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/status` - Проверить статус подписки

### API для вебхуков

HTTP-сервер принимает POST-запросы на следующие эндпоинты:

#### Проверка здоровья
```
GET /health
```

Ответ:
```json
{
  "status": "ok"
}
```

#### Вебхук оплаты
```
POST /webhook/payment
Header: X-Webhook-Secret: your_webhook_secret
```

Тело запроса:
```json
{
  "payment_id": "unique_payment_id",
  "telegram_id": 123456789,
  "amount": "1000",
  "currency": "RUB",
  "status": "success"
}
```

При успешной оплате бот автоматически активирует подписку на 30 дней.

## База данных

Проект использует SQLAlchemy с поддержкой PostgreSQL и SQLite.

### Модели данных

- `User` - информация о пользователях Telegram
- `Subscription` - подписки пользователей
- `Payment` - информация о платежах

### Миграции

База данных автоматически инициализируется при первом запуске бота.

## Разработка

### Запуск в режиме разработки

```bash
python -m src.main
```

### Использование SQLite для разработки

В файле `.env`:
```env
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite+aiosqlite:///./bot.db
```

### Использование PostgreSQL

В файле `.env`:
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

## Лицензия

MIT License - см. файл [LICENSE](LICENSE)
