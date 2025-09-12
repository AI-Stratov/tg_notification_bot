# Telegram Notification Bot 🤖

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/tg-notification-bot.svg)](https://badge.fury.io/py/tg-notification-bot)

A modern, type-safe Python library for sending notifications through Telegram bots. Built with the latest aiogram 3.x
and Pydantic 2.x for maximum reliability and developer experience.

## ✨ Features

- 🔒 **Type Safety**: Full type annotations with mypy support
- 🚀 **Modern**: Built on aiogram 3.x and Pydantic 2.x
- 🛡️ **Robust Error Handling**: Comprehensive exception handling with custom error types
- 📝 **Validation**: Input validation using Pydantic models
- 🎯 **Multiple Formats**: Send text, photos, and documents
- 🔧 **Flexible Configuration**: Support for various chat ID formats
- 📡 **Multi-Chat Support**: Send messages to multiple chats simultaneously
- 🚦 **Concurrent Control**: Configurable concurrency limits for bulk operations
- 🧪 **Well Tested**: Comprehensive test suite with high coverage
- 📦 **Zero Dependencies**: Only requires aiogram and pydantic

## 🚀 Installation

```bash
uv pip install tg-notification-bot
```

For development:

```bash
# Using uv (recommended)
uv add --dev tg-notification-bot
```

## 📖 Quick Start

### Basic Usage

```python
import asyncio
from tg_notification_bot import TelegramNotificationBot


async def main():
  # Initialize with token and chat ID
  bot = TelegramNotificationBot("YOUR_BOT_TOKEN", "YOUR_CHAT_ID")

  # Send a simple message
  await bot.send_message("Hello, World! 🌍")

  # Send a photo
  await bot.send_photo("path/to/photo.jpg", caption="Check this out!")

  # Send a document
  await bot.send_document("path/to/document.pdf", caption="Important file")

  # Don't forget to close the session
  await bot.close()


# Run the example
asyncio.run(main())
```

### Multi-Chat Support

#### Environment Variables for Multiple Chats

```bash
# .env file - Multiple chats separated by commas
TG_BOT_TOKEN=your_bot_token_here
TG_CHAT_ID=123456789,987654321,@channel_name

# Alternative variable name
TG_CHAT_IDS=123456789,987654321,@channel_name
```

```python
import asyncio
from tg_notification_bot import TelegramNotificationBot


async def main():
  # Automatically loads chat IDs from TG_CHAT_ID environment variable
  bot = TelegramNotificationBot("YOUR_BOT_TOKEN")

  # Send to all configured chats
  result = await bot.send_message_bulk("Hello to all chats! 🌍")

  print(f"Sent to {result.successful_chats}/{result.total_chats} chats")
  print(f"Success rate: {result.success_rate:.1f}%")

  if result.failed_chats > 0:
    print(f"Failed chats: {result.failed_chat_ids}")

  await bot.close()


asyncio.run(main())
```

#### Programmatic Multi-Chat Configuration

```python
import asyncio
from tg_notification_bot import TelegramNotificationBot, NotificationConfig


async def main():
  # Configure multiple chats programmatically
  config = NotificationConfig(
    token="YOUR_BOT_TOKEN",
    chat_id=["123456789", "987654321", "@channel_name"],
    parse_mode="Markdown",
    disable_notification=True
  )

  bot = TelegramNotificationBot(config)

  # Send to all configured chats
  result = await bot.send_message_bulk("*Important* notification for all chats!")

  # Detailed results
  for send_result in result.results:
    if send_result.success:
      print(f"✅ Sent to {send_result.chat_id}")
    else:
      print(f"❌ Failed to send to {send_result.chat_id}: {send_result.error}")

  await bot.close()


asyncio.run(main())
```

#### Bulk Operations with Custom Chat Lists

```python
import asyncio
from tg_notification_bot import TelegramNotificationBot


async def main():
  bot = TelegramNotificationBot("YOUR_BOT_TOKEN", "default_chat_id")

  # Override chat list for specific operations
  emergency_chats = ["admin_chat", "ops_chat", "@alerts_channel"]

  async with bot:
    # Send to specific chat list
    result = await bot.send_message_bulk(
      "🚨 System Alert: Server is down!",
      chat_ids=emergency_chats,
      fail_silently=False,  # Raise exceptions on failure
      max_concurrent=5      # Limit concurrent sends
    )

    # Send photo to multiple chats
    photo_result = await bot.send_photo_bulk(
      "monitoring_dashboard.png",
      caption="Current system status",
      chat_ids=emergency_chats
    )


asyncio.run(main())
```

### Using Configuration Object

```python
import asyncio

from tg_notification_bot import TelegramNotificationBot, NotificationConfig


async def main():
  # Create configuration
  config = NotificationConfig(
    token="YOUR_BOT_TOKEN",
    chat_id="YOUR_CHAT_ID",
    parse_mode="Markdown",
    disable_notification=True
  )

  # Initialize bot with config
  bot = TelegramNotificationBot(config)

  await bot.send_message("*Bold text* with _italic_")
  await bot.close()


asyncio.run(main())
```

### Context Manager (Recommended)

```python
import asyncio
from tg_notification_bot import TelegramNotificationBot


async def main():
  async with TelegramNotificationBot("YOUR_BOT_TOKEN", "YOUR_CHAT_ID") as bot:
    await bot.send_message("Message sent safely! ✅")
    # Session automatically closed


asyncio.run(main())
```

## 🔧 Advanced Usage

### Structured Data with Pydantic Models

```python
import asyncio
from tg_notification_bot import (
  TelegramNotificationBot,
  MessageData,
  PhotoData,
  DocumentData
)


async def main():
  async with TelegramNotificationBot("YOUR_BOT_TOKEN", "YOUR_CHAT_ID") as bot:
    # Structured message
    message = MessageData(
      text="<b>Important</b> notification!",
      parse_mode="HTML",
      disable_notification=False
    )
    await bot.send_message(message)

    # Structured photo
    photo = PhotoData(
      photo="https://example.com/image.jpg",
      caption="Remote image",
      parse_mode="Markdown"
    )
    await bot.send_photo(photo)


asyncio.run(main())
```

### Handling Bulk Send Results

```python
import asyncio
from tg_notification_bot import TelegramNotificationBot, BulkSendResult


async def main():
  async with TelegramNotificationBot("YOUR_BOT_TOKEN", ["chat1", "chat2", "chat3"]) as bot:
    result: BulkSendResult = await bot.send_message_bulk("Test message")

    # Check overall results
    print(f"Success rate: {result.success_rate:.1f}%")
    print(f"Successful chats: {len(result.successful_chat_ids)}")
    print(f"Failed chats: {len(result.failed_chat_ids)}")

    # Process individual results
    for send_result in result.results:
      if send_result.success:
        print(f"✅ {send_result.chat_id}")
      else:
        print(f"❌ {send_result.chat_id}: {send_result.error}")
        # Access original exception if needed
        if send_result.exception:
          print(f"   Exception type: {type(send_result.exception).__name__}")


asyncio.run(main())
```

### File Handling

```python
import asyncio
from pathlib import Path
from io import BytesIO
from tg_notification_bot import TelegramNotificationBot


async def main():
  async with TelegramNotificationBot("YOUR_BOT_TOKEN", "YOUR_CHAT_ID") as bot:
    # Local file
    await bot.send_photo(Path("image.jpg"))

    # URL
    await bot.send_photo("https://example.com/photo.jpg")

    # File-like object
    buffer = BytesIO(b"fake image data")
    buffer.name = "generated.jpg"
    await bot.send_photo(buffer, caption="Generated image")


asyncio.run(main())
```

### Error Handling

```python
import asyncio
from tg_notification_bot import (
  TelegramNotificationBot,
  ChatNotFoundError,
  BotBlockedError,
  RateLimitError,
  TelegramNotificationError
)


async def main():
  async with TelegramNotificationBot("YOUR_BOT_TOKEN", "YOUR_CHAT_ID") as bot:
    try:
      await bot.send_message("Test message")
    except ChatNotFoundError as e:
      print(f"Chat not found: {e.chat_id}")
    except BotBlockedError as e:
      print(f"Bot blocked in chat: {e.chat_id}")
    except RateLimitError as e:
      print(f"Rate limited. Retry after: {e.retry_after} seconds")
    except TelegramNotificationError as e:
      print(f"General error: {e}")


asyncio.run(main())
```

## 🔐 Configuration

### Environment Variables

```bash
# .env file
TG_BOT_TOKEN=your_bot_token_here

# Single chat
TG_CHAT_ID=your_chat_id_here

# Multiple chats (comma-separated)
TG_CHAT_ID=123456789,987654321,@channel_name

# Alternative for multiple chats
TG_CHAT_IDS=123456789,987654321,@channel_name
```

```python
import os
from tg_notification_bot import TelegramNotificationBot

# Load from environment
bot = TelegramNotificationBot(
  token=os.getenv("TG_BOT_TOKEN"),
  chat_id=os.getenv("TG_CHAT_ID")
)
```

### Chat ID Formats

The library supports various chat ID formats:

- `123456789` - User ID
- `-123456789` - Group chat ID
- `-100123456789` - Supergroup/channel ID
- `@username` - Public chat username

The bot automatically tries different formats if the initial one fails.

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=tg_notification_bot --cov-report=html

# Type checking
uv run mypy tg_notification_bot

# Linting and formatting with ruff
uv run ruff check tg_notification_bot
uv run ruff format --check tg_notification_bot
```

## 📝 API Reference

### Classes

#### `TelegramNotificationBot`

Main bot class for sending notifications.

**Constructor:**

- `TelegramNotificationBot(token: NotificationConfig | str, chat_id: str | int | List[str | int] = None)`

**Methods:**

##### Single Chat Methods
- `send_message(message: str | MessageData, chat_id: str | int = None) -> None`
- `send_photo(photo: str | Path | IO | PhotoData, caption: str = None, chat_id: str | int = None) -> None`
- `send_document(document: str | Path | IO | DocumentData, caption: str = None, chat_id: str | int = None) -> None`

##### Bulk Methods
- `send_message_bulk(message: str | MessageData, chat_ids: List[str | int] = None, fail_silently: bool = True, max_concurrent: int = 10) -> BulkSendResult`
- `send_photo_bulk(photo: str | Path | IO | PhotoData, caption: str = None, chat_ids: List[str | int] = None, fail_silently: bool = True, max_concurrent: int = 10) -> BulkSendResult`
- `send_document_bulk(document: str | Path | IO | DocumentData, caption: str = None, chat_ids: List[str | int] = None, fail_silently: bool = True, max_concurrent: int = 10) -> BulkSendResult`

##### Utility Methods
- `close() -> None`

#### `BulkSendResult`

Result object for bulk send operations.

**Properties:**
- `results: List[SendResult]` - Individual results for each chat
- `total_chats: int` - Total number of chats attempted
- `successful_chats: int` - Number of successful sends
- `failed_chats: int` - Number of failed sends
- `success_rate: float` - Success rate as percentage
- `successful_chat_ids: List[str]` - List of successful chat IDs
- `failed_chat_ids: List[str]` - List of failed chat IDs

#### `SendResult`

Result object for individual send operation.

**Properties:**
- `chat_id: str` - Chat ID where message was sent
- `success: bool` - Whether the operation was successful
- `error: Optional[str]` - Error message if failed
- `exception: Optional[Exception]` - Original exception if failed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Modern Telegram Bot API framework
- [pydantic](https://github.com/pydantic/pydantic) - Data validation using Python type hints
