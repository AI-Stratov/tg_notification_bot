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
TG_CHAT_ID=your_chat_id_here
```

```python
import os
from tg_notification_bot import TelegramNotificationBot

# Load from environment
bot = TelegramNotificationBot(
  config=os.getenv("TG_BOT_TOKEN"),
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

- `TelegramNotificationBot(config: NotificationConfig | str, chat_id: str | int = None)`

**Methods:**

- `send_message(message: str | MessageData, chat_id: str | int = None) -> None`
- `send_photo(photo: str | Path | IO | PhotoData, caption: str = None, chat_id: str | int = None) -> None`
- `send_document(document: str | Path | IO | DocumentData, caption: str = None, chat_id: str | int = None) -> None`
- `close() -> None`

#### Configuration Models

- `NotificationConfig` - Bot configuration
- `MessageData` - Message parameters
- `PhotoData` - Photo parameters
- `DocumentData` - Document parameters

#### Exceptions

- `TelegramNotificationError` - Base exception
- `ChatNotFoundError` - Chat not found
- `BotBlockedError` - Bot blocked by user
- `RateLimitError` - Rate limit exceeded
- `InvalidChatIdError` - Invalid chat ID format

## 🛠️ Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/AI-Stratov/tg-notification-bot.git
cd tg-notification-bot

# Install the project and development dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Building and Publishing

```bash
# Build the package
uv build

# Publish to PyPI (requires authentication)
uv publish
```

### Code Style

This project uses:

- **ruff** for linting and code formatting (replaces black, isort, flake8)
- **mypy** for type checking

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to
discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Modern Telegram Bot API framework
- [pydantic](https://github.com/pydantic/pydantic) - Data validation using Python type hints

## 📊 Changelog

### v0.1.0 (2024-XX-XX)

- 🎉 Initial release
- ✨ Full type safety with mypy support
- 🚀 Modern aiogram 3.x and Pydantic 2.x
- 🛡️ Comprehensive error handling
- 📝 Complete test coverage
- 📚 Full documentation
