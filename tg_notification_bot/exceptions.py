"""Custom exceptions for Telegram notification bot."""

from typing import Optional


class TelegramNotificationError(Exception):
    """Base exception for Telegram notification errors."""

    def __init__(self, message: str, chat_id: Optional[str] = None):
        self.message = message
        self.chat_id = chat_id
        super().__init__(self.message)


class ChatNotFoundError(TelegramNotificationError):
    """Raised when the specified chat cannot be found."""

    def __init__(self, chat_id: str):
        message = f"Chat with ID '{chat_id}' not found"
        super().__init__(message, chat_id)


class BotBlockedError(TelegramNotificationError):
    """Raised when the bot is blocked by user or has no access to chat."""

    def __init__(self, chat_id: str):
        message = f"Bot is blocked by user or has no access to chat '{chat_id}'"
        super().__init__(message, chat_id)


class RateLimitError(TelegramNotificationError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int, chat_id: Optional[str] = None):
        self.retry_after = retry_after
        message = f"Rate limit exceeded. Retry after {retry_after} seconds"
        super().__init__(message, chat_id)


class InvalidChatIdError(TelegramNotificationError):
    """Raised when chat ID format is invalid."""

    def __init__(self, chat_id: str):
        message = f"Invalid chat ID format: '{chat_id}'"
        super().__init__(message, chat_id)
