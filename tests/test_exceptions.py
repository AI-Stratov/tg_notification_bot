import pytest

from tg_notification_bot import (
    BotBlockedError,
    ChatNotFoundError,
    InvalidChatIdError,
    RateLimitError,
    TelegramNotificationError,
)


def test_base_error() -> None:
    error = TelegramNotificationError("boom", "42")

    assert str(error) == "boom"
    assert error.message == "boom"
    assert error.chat_id == "42"


def test_base_error_without_chat() -> None:
    assert TelegramNotificationError("boom").chat_id is None


@pytest.mark.parametrize(
    ("error", "text"),
    [
        (ChatNotFoundError("42"), "Chat with ID '42' not found"),
        (BotBlockedError("42"), "Bot is blocked by user or has no access to chat '42'"),
        (InvalidChatIdError("42"), "Invalid chat ID format: '42'"),
        (RateLimitError(30, "42"), "Rate limit exceeded. Retry after 30 seconds"),
    ],
)
def test_subclasses(error: TelegramNotificationError, text: str) -> None:
    assert isinstance(error, TelegramNotificationError)
    assert str(error) == text
    assert error.chat_id == "42"


def test_rate_limit_retry_after() -> None:
    error = RateLimitError(30)

    assert error.retry_after == 30
    assert error.chat_id is None
