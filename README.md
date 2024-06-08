# tg-notification-bot
## Поддержка версий

![Python Versions](https://img.shields.io/badge/Python-3.8--3.12-black?style=for-the-badge)
![Aiogram 2.25.2](https://img.shields.io/badge/aiogram-2.25.2-black?style=for-the-badge)

Эта библиотека предоставляет собой простой способ отправки сообщений, фотографий и документов в групповой чат Telegram. Является оберткой над Aiogram.
## Установка

Установите библиотеку с помощью pip:

`pip install tg_notification_bot`

## Использование

1. Импортируйте класс `TgNotificationBot` из библиотеки:

```python
from tg_notification_bot import TgNotificationBot
```

2. Создайте экземпляр TgNotificationBot, передав токен вашего Telegram бота и идентификатор группового чата:

```python
bot = TgNotificationBot(token="YOUR_BOT_TOKEN", chat_id="-123456789")
```

3. Используйте методы класса для отправки контента в групповой чат:

```python
# Отправка текстового сообщения
from app import bot

await bot.send_message("Привет, группа!")

# Отправка фотографии
photo_path = r"C:\Users\SomeUser\Downloads\photo_2024-14-14_19-02-21.jpg"
await bot.send_photo(open(photo_path, "rb"), caption="Вот ваше фото!")

# Отправка документа
document_path = r"C:\Users\SomeUser\Downloads\document.pdf"
await bot.send_document(open(document_path, "rb"), caption="Описание документа")
```
**Важно - телеграм ограничивает размер документов - максимум 50 MB, фото - до 10 MB**
_Чтобы отправить файл больше - разбейте его на несколько частей и выполните несколько запросов_

## Интеграция с FastAPI

Вы можете инициализировать экземпляр TgNotificationBot при запуске вашего приложения FastAPI

```python
from fastapi import FastAPI
from tg_notification_bot import TgNotificationBot

app = FastAPI()
bot = TgNotificationBot(token="YOUR_BOT_TOKEN", chat_id="-123456789")
```

Затем вы можете использовать экземпляр bot в своих маршрутах или обработчиках для отправки контента в групповой чат.
