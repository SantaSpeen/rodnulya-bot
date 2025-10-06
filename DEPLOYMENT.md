# Руководство по развертыванию

## Локальная разработка

### 1. Подготовка окружения

```bash
# Клонирование репозитория
git clone https://github.com/SantaSpeen/rodnulya-bot.git
cd rodnulya-bot

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Конфигурация

Создайте файл `.env`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваш токен бота:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite+aiosqlite:///./bot.db
HTTP_HOST=0.0.0.0
HTTP_PORT=8080
WEBHOOK_SECRET=my_secure_secret_key
```

### 3. Запуск

```bash
python -m src.main
```

## Развертывание через Docker Compose

### 1. Подготовка

```bash
# Клонирование репозитория
git clone https://github.com/SantaSpeen/rodnulya-bot.git
cd rodnulya-bot

# Создание .env файла
cat > .env << EOF
BOT_TOKEN=your_bot_token_here
WEBHOOK_SECRET=$(openssl rand -hex 32)
EOF
```

### 2. Запуск

```bash
# Сборка и запуск
docker compose up -d

# Просмотр логов
docker compose logs -f bot

# Остановка
docker compose down
```

### 3. Обновление

```bash
# Получить последние изменения
git pull

# Пересобрать и перезапустить
docker compose up -d --build
```

## Развертывание на VPS (Ubuntu/Debian)

### 1. Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка установки
docker --version
```

### 2. Клонирование и настройка

```bash
# Клонирование репозитория
git clone https://github.com/SantaSpeen/rodnulya-bot.git
cd rodnulya-bot

# Создание .env файла
nano .env
# Вставьте свои настройки и сохраните (Ctrl+O, Enter, Ctrl+X)
```

### 3. Запуск

```bash
# Запуск в фоновом режиме
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f bot
```

### 4. Настройка автозапуска

Создайте systemd service:

```bash
sudo nano /etc/systemd/system/rodnulya-bot.service
```

Содержимое файла:

```ini
[Unit]
Description=Rodnulya Telegram Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/YOUR_USER/rodnulya-bot
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=YOUR_USER

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
sudo systemctl daemon-reload
sudo systemctl enable rodnulya-bot
sudo systemctl start rodnulya-bot
```

## Развертывание на хостинге с Docker

### Railway.app

1. Зарегистрируйтесь на [railway.app](https://railway.app)
2. Создайте новый проект из GitHub репозитория
3. Добавьте переменные окружения:
   - `BOT_TOKEN`
   - `WEBHOOK_SECRET`
4. Railway автоматически определит Dockerfile и развернет бот

### Render.com

1. Зарегистрируйтесь на [render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите ваш GitHub репозиторий
4. Настройте:
   - Environment: Docker
   - Build Command: (оставьте пустым)
   - Start Command: (оставьте пустым, используется CMD из Dockerfile)
5. Добавьте переменные окружения
6. Создайте PostgreSQL базу данных (опционально)

### DigitalOcean App Platform

1. Зарегистрируйтесь на [digitalocean.com](https://digitalocean.com)
2. Создайте новое приложение из Docker Hub или GitHub
3. Настройте переменные окружения
4. Добавьте PostgreSQL базу данных (опционально)

## Мониторинг и логирование

### Просмотр логов Docker

```bash
# Последние 100 строк
docker compose logs --tail=100 bot

# В режиме реального времени
docker compose logs -f bot

# Логи конкретного контейнера
docker logs rodnulya-bot
```

### Проверка работоспособности

```bash
# Проверка HTTP эндпоинта
curl http://localhost:8080/health

# Проверка статуса контейнеров
docker compose ps
```

### Резервное копирование базы данных

#### PostgreSQL

```bash
# Создание бэкапа
docker compose exec postgres pg_dump -U rodnulya rodnulya > backup.sql

# Восстановление
cat backup.sql | docker compose exec -T postgres psql -U rodnulya rodnulya
```

#### SQLite

```bash
# Просто скопируйте файл базы данных
cp bot.db bot.db.backup
```

## Обновление бота

### Без простоя (рекомендуется)

```bash
# Получить изменения
git pull

# Пересобрать образ
docker compose build

# Перезапустить с новым образом
docker compose up -d --no-deps bot
```

### С остановкой

```bash
# Остановить бот
docker compose down

# Получить изменения
git pull

# Запустить заново
docker compose up -d --build
```

## Решение проблем

### Бот не запускается

1. Проверьте логи:
```bash
docker compose logs bot
```

2. Проверьте переменные окружения:
```bash
docker compose config
```

3. Проверьте токен бота и доступ к Telegram API

### База данных не подключается

1. Проверьте статус PostgreSQL:
```bash
docker compose ps postgres
```

2. Проверьте логи PostgreSQL:
```bash
docker compose logs postgres
```

3. Убедитесь, что DATABASE_URL правильный

### HTTP сервер недоступен

1. Проверьте, что порт 8080 открыт:
```bash
netstat -tulpn | grep 8080
```

2. Проверьте firewall:
```bash
sudo ufw status
sudo ufw allow 8080
```

3. Проверьте логи HTTP сервера в логах бота
