# tg-notification-bot

Эта библиотека предоставляет простой способ отправки сообщений, фотографий и документов в групповой чат Telegram.

## Установка

Установите библиотеку с помощью pip:

`pip install python-telegram-bot`

## Использование

1. Импортируйте класс `GroupChatBot` из библиотеки:

```python
from tg_notification_bot import GroupChatBot
```

2. Создайте экземпляр GroupChatBot, передав токен вашего Telegram бота и идентификатор группового чата:

```python
bot = GroupChatBot(token="YOUR_BOT_TOKEN", chat_id="-123456789")
```

3. Используйте методы класса для отправки контента в групповой чат:

```python
# Отправка текстового сообщения
bot.send_message("Привет, группа!")

# Отправка фотографии
with open("photo.jpg", "rb") as f:
  photo = f.read()
  bot.send_photo(photo, caption="Описание фотографии")

# Отправка документа
with open("document.pdf", "rb") as f:
  document = f.read()
  bot.send_document(document, caption="Описание документа")
```

## Интеграция с FastAPI

Вы можете инициализировать экземпляр GroupChatBot при запуске вашего приложения FastAPI

```python
from fastapi import FastAPI
from tg_notification_bot import GroupChatBot

app = FastAPI()
bot = GroupChatBot(token="YOUR_BOT_TOKEN", chat_id="-123456789")
```

Затем вы можете использовать экземпляр bot в своих маршрутах или обработчиках для отправки контента в групповой чат.

## Обработка ошибок

Библиотека обрабатывает следующие типы ошибок:

1. Если бот не имеет доступа к групповому чату, выводится соответствующее сообщение.
2. Для других ошибок при отправке контента выводится общее сообщение об ошибке.
