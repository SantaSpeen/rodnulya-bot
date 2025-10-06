# Примеры использования API

## Webhook для уведомления об оплате

### Успешная оплата

```bash
curl -X POST http://localhost:8080/webhook/payment \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your_webhook_secret" \
  -d '{
    "payment_id": "pay_123456789",
    "telegram_id": 123456789,
    "amount": "1000",
    "currency": "RUB",
    "status": "success"
  }'
```

### Ожидание оплаты

```bash
curl -X POST http://localhost:8080/webhook/payment \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your_webhook_secret" \
  -d '{
    "payment_id": "pay_987654321",
    "telegram_id": 123456789,
    "amount": "1000",
    "currency": "RUB",
    "status": "pending"
  }'
```

### Проверка здоровья сервера

```bash
curl http://localhost:8080/health
```

Ответ:
```json
{
  "status": "ok"
}
```

## Структура данных

### Payment Webhook

**Поля:**
- `payment_id` (string, обязательно) - уникальный идентификатор платежа
- `telegram_id` (integer, обязательно) - Telegram ID пользователя
- `amount` (string, обязательно) - сумма платежа
- `currency` (string, опционально) - валюта платежа (по умолчанию: RUB)
- `status` (string, обязательно) - статус платежа (success, pending, failed)

**Статусы:**
- `success` - оплата прошла успешно, подписка активируется на 30 дней
- `pending` - оплата в обработке, подписка не активируется
- `failed` - оплата не прошла, подписка не активируется

## Интеграция с платежными системами

### Пример интеграции с YooKassa

```python
from yookassa import Configuration, Payment

# Настройка
Configuration.account_id = 'your_shop_id'
Configuration.secret_key = 'your_secret_key'

# Создание платежа
payment = Payment.create({
    "amount": {
        "value": "1000.00",
        "currency": "RUB"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://example.com/return"
    },
    "capture": True,
    "description": "Подписка Remnawave",
    "metadata": {
        "telegram_id": 123456789
    }
})

# После успешной оплаты отправить webhook
import requests

webhook_data = {
    "payment_id": payment.id,
    "telegram_id": 123456789,
    "amount": "1000",
    "currency": "RUB",
    "status": "success"
}

response = requests.post(
    'http://bot-server:8080/webhook/payment',
    json=webhook_data,
    headers={'X-Webhook-Secret': 'your_webhook_secret'}
)
```

### Пример интеграции с Stripe

```python
import stripe
import requests

stripe.api_key = 'your_stripe_secret_key'

# Создание платежа
intent = stripe.PaymentIntent.create(
    amount=100000,  # в копейках
    currency='rub',
    metadata={'telegram_id': 123456789}
)

# После успешной оплаты
if intent.status == 'succeeded':
    webhook_data = {
        "payment_id": intent.id,
        "telegram_id": intent.metadata['telegram_id'],
        "amount": str(intent.amount / 100),
        "currency": intent.currency.upper(),
        "status": "success"
    }
    
    response = requests.post(
        'http://bot-server:8080/webhook/payment',
        json=webhook_data,
        headers={'X-Webhook-Secret': 'your_webhook_secret'}
    )
```

## Безопасность

Всегда используйте заголовок `X-Webhook-Secret` для валидации запросов:

```python
import hmac
import hashlib

def validate_webhook(secret, data):
    """Проверка подписи webhook (пример)"""
    # В production используйте более надежную систему подписей
    return secret == request.headers.get('X-Webhook-Secret')
```

## Тестирование

Для локального тестирования webhook можно использовать ngrok:

```bash
# Запустите ngrok
ngrok http 8080

# Используйте предоставленный URL для webhook
# Например: https://abc123.ngrok.io/webhook/payment
```
