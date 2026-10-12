"""Run the examples against a fake Telegram session to keep them in sync with the API."""

import runpy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.methods import GetChat, SendDocument, SendMessage, TelegramMethod

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def telegram_calls() -> Any:
    """Record Bot API calls instead of sending them."""
    calls: list[TelegramMethod[Any]] = []

    async def fake_make_request(
        self: AiohttpSession, bot: Any, method: TelegramMethod[Any], timeout: Any = None
    ) -> None:
        calls.append(method)

    with patch.object(AiohttpSession, "make_request", fake_make_request):
        yield calls


async def test_multi_chat_example(telegram_calls: list[TelegramMethod[Any]], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TG_BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("TG_CHAT_ID", "-1001234567890,@example_channel")
    module = runpy.run_path(str(EXAMPLES_DIR / "multi_chat_example.py"))

    await module["main"]()

    sent_messages = [c for c in telegram_calls if isinstance(c, SendMessage)]
    sent_documents = [c for c in telegram_calls if isinstance(c, SendDocument)]
    assert len(sent_messages) == 5
    assert len(sent_documents) == 2
    assert {c.chat_id for c in sent_documents} == {"-1001234567890", "@example_channel"}
    assert sum(1 for c in sent_messages if c.disable_notification) == 2
    assert all(isinstance(c, (GetChat, SendMessage, SendDocument)) for c in telegram_calls)


async def test_multi_chat_example_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TG_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TG_CHAT_ID", raising=False)
    module = runpy.run_path(str(EXAMPLES_DIR / "multi_chat_example.py"))

    with pytest.raises(SystemExit):
        await module["main"]()
