"""Pytest configuration and fixtures for Telegram notification bot tests."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.client.session.aiohttp import AiohttpSession


@pytest.fixture(autouse=True)
def block_telegram_api() -> Generator[None, None, None]:
    """Fail any test that would send a real HTTP request to the Telegram API."""

    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Unit tests must not call the Telegram API")

    with patch.object(AiohttpSession, "make_request", refuse), patch.object(AiohttpSession, "stream_content", refuse):
        yield


@pytest.fixture
def mock_aiogram_bot() -> Generator[AsyncMock, None, None]:
    """Mock aiogram Bot instance."""
    with patch("tg_notification_bot.bot.Bot") as mock_bot_class:
        bot_instance = AsyncMock()
        bot_instance.session = Mock()
        bot_instance.session.close = AsyncMock()
        mock_bot_class.return_value = bot_instance
        yield bot_instance


@pytest.fixture
def valid_token() -> str:
    """Valid bot token for testing."""
    return "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"


@pytest.fixture
def valid_chat_id() -> str:
    """Valid chat ID for testing."""
    return "123456789"
