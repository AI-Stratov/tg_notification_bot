"""Send Telegram notifications to one or more chats."""

__version__ = "1.1.0"

from .bot import TelegramNotificationBot
from .exceptions import (
    BotBlockedError,
    ChatNotFoundError,
    InvalidChatIdError,
    RateLimitError,
    TelegramNotificationError,
)
from .models import (
    BulkSendResult,
    DocumentData,
    MessageData,
    NotificationConfig,
    PhotoData,
    SendResult,
)

__all__ = [
    "BotBlockedError",
    "BulkSendResult",
    "ChatNotFoundError",
    "DocumentData",
    "InvalidChatIdError",
    "MessageData",
    "NotificationConfig",
    "PhotoData",
    "RateLimitError",
    "SendResult",
    "TelegramNotificationBot",
    "TelegramNotificationError",
]
