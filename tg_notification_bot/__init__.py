"""
Modern Telegram notification bot library for Python projects.

This library provides a simple and efficient way to send notifications
through Telegram bots with proper error handling and type safety.
"""

__version__ = "1.0.0"

from .bot import TelegramNotificationBot
from .exceptions import (
    BotBlockedError,
    ChatNotFoundError,
    InvalidChatIdError,
    RateLimitError,
    TelegramNotificationError,
)
from .models import (
    DocumentData,
    MessageData,
    NotificationConfig,
    PhotoData,
    SendResult,
    BulkSendResult,
)

__all__ = [
    "TelegramNotificationBot",
    "TelegramNotificationError",
    "ChatNotFoundError",
    "BotBlockedError",
    "RateLimitError",
    "InvalidChatIdError",
    "NotificationConfig",
    "MessageData",
    "PhotoData",
    "DocumentData",
    "SendResult",
    "BulkSendResult",
]
