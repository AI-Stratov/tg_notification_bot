"""Comprehensive tests for Telegram notification bot."""

import io
from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from tg_notification_bot import (
    BotBlockedError,
    ChatNotFoundError,
    InvalidChatIdError,
    MessageData,
    NotificationConfig,
    RateLimitError,
    TelegramNotificationBot,
    TelegramNotificationError,
)


class TestNotificationConfig:
    """Test NotificationConfig model."""

    def test_valid_config(self) -> None:
        """Test valid configuration creation."""
        config = NotificationConfig(
            token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            chat_id="123456789",
        )
        assert config.token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        assert config.chat_id == "123456789"
        assert config.parse_mode == "HTML"
        assert config.disable_notification is False

    def test_invalid_token(self) -> None:
        """Test invalid token validation."""
        with pytest.raises(ValueError, match="Invalid bot token format"):
            NotificationConfig(token="invalid_token", chat_id="123")

    def test_empty_token(self) -> None:
        """Test empty token validation."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            NotificationConfig(token="", chat_id="123")

    def test_empty_chat_id(self) -> None:
        """Test empty chat ID validation."""
        with pytest.raises(ValueError, match="Chat ID cannot be empty string"):
            NotificationConfig(
                token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
                chat_id="",
            )


class TestMessageData:
    """Test MessageData model."""

    def test_valid_message(self) -> None:
        """Test valid message creation."""
        message = MessageData(text="Test message")
        assert message.text == "Test message"
        assert message.parse_mode is None

    def test_empty_message(self) -> None:
        """Test empty message validation."""
        with pytest.raises(ValueError):
            MessageData(text="")

    def test_too_long_message(self) -> None:
        """Test message length validation."""
        long_text = "x" * 4097
        with pytest.raises(ValueError):
            MessageData(text=long_text)


@pytest.fixture
def mock_bot() -> Generator[AsyncMock, None, None]:
    """Mock bot fixture."""
    with patch("tg_notification_bot.bot.Bot") as mock:
        bot_instance = AsyncMock()
        mock.return_value = bot_instance
        yield bot_instance


@pytest.fixture
def notification_bot(mock_bot: AsyncMock) -> TelegramNotificationBot:
    """Notification bot fixture."""
    config = NotificationConfig(
        token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
        chat_id="123456789",
    )
    return TelegramNotificationBot(config)


class TestTelegramNotificationBot:
    """Test TelegramNotificationBot class."""

    def test_init_with_config(self, mock_bot: AsyncMock) -> None:
        """Test initialization with config object."""
        config = NotificationConfig(
            token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            chat_id="123456789",
        )
        bot = TelegramNotificationBot(config)
        assert bot.config == config

    def test_init_with_token_and_chat_id(self, mock_bot: AsyncMock) -> None:
        """Test initialization with token and chat_id."""
        bot = TelegramNotificationBot(
            "123456789:ABCdefGHIjklMNOpqrsTUVwxyz", "123456789"
        )
        assert bot.config.token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        assert bot.config.chat_id == "123456789"

    def test_init_with_token_no_chat_id(self, mock_bot: AsyncMock) -> None:
        """Test initialization with token but no chat_id raises error."""
        with pytest.raises(ValueError, match="chat_id is required"):
            TelegramNotificationBot("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")

    @pytest.mark.asyncio
    async def test_send_message_success(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test successful message sending."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_message.return_value = Mock()

        await notification_bot.send_message("Test message")

        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[1]["text"] == "Test message"
        assert call_args[1]["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_send_message_with_message_data(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test sending message with MessageData object."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_message.return_value = Mock()

        message_data = MessageData(text="Test message", parse_mode="Markdown")
        await notification_bot.send_message(message_data)

        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[1]["text"] == "Test message"
        assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_send_message_bot_blocked(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test handling of blocked bot error."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_message.side_effect = TelegramForbiddenError(
            message="Forbidden: bot was blocked by the user"
        )

        with pytest.raises(BotBlockedError) as exc_info:
            await notification_bot.send_message("Test message")

        assert "123456789" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_message_chat_not_found(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test handling of chat not found error."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_message.side_effect = TelegramBadRequest(
            message="Bad Request: chat not found"
        )

        with pytest.raises(ChatNotFoundError) as exc_info:
            await notification_bot.send_message("Test message")

        assert "123456789" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_message_rate_limit(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test handling of rate limit error."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_message.side_effect = TelegramRetryAfter(
            message="Too Many Requests: retry after 30",
            retry_after=30,
        )

        with pytest.raises(RateLimitError) as exc_info:
            await notification_bot.send_message("Test message")

        assert exc_info.value.retry_after == 30

    @pytest.mark.asyncio
    async def test_send_photo_with_path(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test sending photo with file path."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_photo.return_value = Mock()

        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            await notification_bot.send_photo("test_image.jpg", "Test caption")

        mock_bot.send_photo.assert_called_once()
        call_args = mock_bot.send_photo.call_args
        assert call_args[1]["caption"] == "Test caption"

    @pytest.mark.asyncio
    async def test_send_photo_with_url(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test sending photo with URL."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_photo.return_value = Mock()

        await notification_bot.send_photo("https://example.com/image.jpg")

        mock_bot.send_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_photo_with_file_object(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test sending photo with file object."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_photo.return_value = Mock()

        file_obj = io.BytesIO(b"fake image data")
        file_obj.name = "test.jpg"

        await notification_bot.send_photo(file_obj)

        mock_bot.send_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_document_success(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test successful document sending."""
        mock_bot.get_chat.return_value = Mock()
        mock_bot.send_document.return_value = Mock()

        with patch("pathlib.Path.exists", return_value=True):
            await notification_bot.send_document("test.pdf", "Test document")

        mock_bot.send_document.assert_called_once()
        call_args = mock_bot.send_document.call_args
        assert call_args[1]["caption"] == "Test document"

    @pytest.mark.asyncio
    async def test_normalize_chat_id_integer(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test chat ID normalization with integer."""
        mock_bot.get_chat.return_value = Mock()

        result = await notification_bot._normalize_chat_id(123456789)
        assert result == "123456789"

    @pytest.mark.asyncio
    async def test_normalize_chat_id_with_prefix(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test chat ID normalization with existing prefix."""
        mock_bot.get_chat.return_value = Mock()

        result = await notification_bot._normalize_chat_id("-100123456789")
        assert result == "-100123456789"

    @pytest.mark.asyncio
    async def test_normalize_chat_id_try_modifications(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test chat ID normalization trying different formats."""
        # First call (original) fails, second call (with -) succeeds
        mock_bot.get_chat.side_effect = [
            TelegramBadRequest(message="chat not found"),
            Mock(),  # Success with modified chat_id
        ]

        result = await notification_bot._normalize_chat_id("123456789")
        assert result == "-123456789"

    @pytest.mark.asyncio
    async def test_normalize_chat_id_all_fail(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test chat ID normalization when all formats fail."""
        mock_bot.get_chat.side_effect = TelegramBadRequest(message="chat not found")

        with pytest.raises(ChatNotFoundError):
            await notification_bot._normalize_chat_id("invalid_chat_id")

    @pytest.mark.asyncio
    async def test_context_manager(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test async context manager usage."""
        mock_bot.session = Mock()
        mock_bot.session.close = AsyncMock()

        async with notification_bot as bot:
            assert bot is notification_bot

        mock_bot.session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(
        self, notification_bot: TelegramNotificationBot, mock_bot: AsyncMock
    ) -> None:
        """Test manual close."""
        mock_bot.session = Mock()
        mock_bot.session.close = AsyncMock()

        await notification_bot.close()

        mock_bot.session.close.assert_called_once()


class TestExceptions:
    """Test custom exceptions."""

    def test_telegram_notification_error(self) -> None:
        """Test base exception."""
        error = TelegramNotificationError("Test error", "123")
        assert str(error) == "Test error"
        assert error.chat_id == "123"

    def test_chat_not_found_error(self) -> None:
        """Test ChatNotFoundError."""
        error = ChatNotFoundError("123")
        assert "Chat with ID '123' not found" in str(error)
        assert error.chat_id == "123"

    def test_bot_blocked_error(self) -> None:
        """Test BotBlockedError."""
        error = BotBlockedError("123")
        assert "blocked" in str(error).lower()
        assert error.chat_id == "123"

    def test_rate_limit_error(self) -> None:
        """Test RateLimitError."""
        error = RateLimitError(30, "123")
        assert "30 seconds" in str(error)
        assert error.retry_after == 30
        assert error.chat_id == "123"

    def test_invalid_chat_id_error(self) -> None:
        """Test InvalidChatIdError."""
        error = InvalidChatIdError("invalid")
        assert "Invalid chat ID format" in str(error)
        assert error.chat_id == "invalid"
