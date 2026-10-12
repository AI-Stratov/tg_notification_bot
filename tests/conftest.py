"""Shared fixtures. No test may reach the real Telegram API."""

from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import pytest
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from tests.helpers import CHAT_ID, TOKEN
from tg_notification_bot import TelegramNotificationBot


@pytest.fixture(autouse=True)
def block_telegram_api() -> Iterator[None]:
    """Fail any test that would send a real HTTP request to the Telegram API."""

    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Unit tests must not call the Telegram API")

    with patch.object(AiohttpSession, "make_request", refuse), patch.object(AiohttpSession, "stream_content", refuse):
        yield


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the developer's TG_CHAT_ID / TG_CHAT_IDS out of the tests."""
    monkeypatch.delenv("TG_CHAT_ID", raising=False)
    monkeypatch.delenv("TG_CHAT_IDS", raising=False)


@pytest.fixture(scope="session")
def _autospec_bot() -> MagicMock:
    # Building an autospec of aiogram.Bot is slow, so build it once and reset it per test.
    bot: MagicMock = create_autospec(Bot, instance=True)
    return bot


@pytest.fixture
def aiogram_bot(_autospec_bot: MagicMock) -> Iterator[MagicMock]:
    """Replace aiogram.Bot with a mock that checks call signatures against the real Bot."""
    _autospec_bot.reset_mock(return_value=True, side_effect=True)
    _autospec_bot.session = AsyncMock()
    with patch("tg_notification_bot.bot.Bot", return_value=_autospec_bot):
        yield _autospec_bot


@pytest.fixture
def bot(aiogram_bot: MagicMock) -> TelegramNotificationBot:
    return TelegramNotificationBot(TOKEN, CHAT_ID)
