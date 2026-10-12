import asyncio
import io
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import BufferedInputFile

from tests.helpers import TOKEN, api_error
from tg_notification_bot import (
    BotBlockedError,
    ChatNotFoundError,
    DocumentData,
    MessageData,
    NotificationConfig,
    PhotoData,
    TelegramNotificationBot,
)

CHATS: list[int | str] = [1, 2, 3]

# (bulk method, aiogram method, positional argument)
BULK_METHODS = [
    pytest.param("send_message_bulk", "send_message", "hello", id="message"),
    pytest.param("send_photo_bulk", "send_photo", "https://example.com/photo.jpg", id="photo"),
    pytest.param("send_document_bulk", "send_document", "https://example.com/report.pdf", id="document"),
]


@pytest.fixture
def bot(aiogram_bot: MagicMock) -> TelegramNotificationBot:
    return TelegramNotificationBot(TOKEN, CHATS)


def fail_for(chat_id: int, error: Exception) -> Any:
    async def send(**kwargs: Any) -> None:
        if kwargs["chat_id"] == chat_id:
            raise error

    return send


@pytest.mark.parametrize(("method", "aiogram_method", "argument"), BULK_METHODS)
async def test_sends_to_configured_chats(
    bot: TelegramNotificationBot, aiogram_bot: MagicMock, method: str, aiogram_method: str, argument: Any
) -> None:
    result = await getattr(bot, method)(argument)

    sent_to = sorted(call.kwargs["chat_id"] for call in getattr(aiogram_bot, aiogram_method).await_args_list)
    assert sent_to == CHATS
    assert (result.total_chats, result.successful_chats, result.failed_chats) == (3, 3, 0)
    assert [r.chat_id for r in result.results] == ["1", "2", "3"]
    assert all(r.success and r.error is None and r.exception is None for r in result.results)


async def test_explicit_chat_ids(aiogram_bot: MagicMock) -> None:
    bot = TelegramNotificationBot(NotificationConfig(token=TOKEN))

    result = await bot.send_message_bulk("hi", chat_ids=[10, "@channel"])

    assert result.successful_chat_ids == ["10", "@channel"]


async def test_empty_chat_ids(bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
    result = await bot.send_message_bulk("hi", chat_ids=[])

    assert result.total_chats == 0
    aiogram_bot.send_message.assert_not_awaited()


async def test_no_chat_ids(aiogram_bot: MagicMock) -> None:
    bot = TelegramNotificationBot(NotificationConfig(token=TOKEN))

    with pytest.raises(ValueError, match="No chat IDs specified"):
        await bot.send_message_bulk("hi")


async def test_message_options(bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
    await bot.send_message_bulk(MessageData(text="hi", disable_notification=True), chat_ids=[1])

    assert aiogram_bot.send_message.await_args.kwargs["disable_notification"] is True


async def test_failures_are_collected_as_library_errors(bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
    aiogram_bot.send_message.side_effect = fail_for(2, api_error(TelegramForbiddenError, "Forbidden"))

    result = await bot.send_message_bulk("hi")

    assert result.successful_chat_ids == ["1", "3"]
    assert result.failed_chat_ids == ["2"]
    failed = result.results[1]
    assert isinstance(failed.exception, BotBlockedError)
    assert failed.error == str(failed.exception)
    assert result.success_rate == pytest.approx(66.67, abs=0.01)


async def test_resolution_failures_are_collected(bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
    aiogram_bot.get_chat.side_effect = api_error(TelegramBadRequest, "chat not found")

    result = await bot.send_message_bulk("hi", chat_ids=[1, "999"])

    assert result.failed_chat_ids == ["999"]
    assert isinstance(result.results[1].exception, ChatNotFoundError)


async def test_fail_loudly_raises_and_cancels_the_rest(aiogram_bot: MagicMock) -> None:
    bot = TelegramNotificationBot(TOKEN, [1, 2])
    cancelled = asyncio.Event()

    async def send(**kwargs: Any) -> None:
        if kwargs["chat_id"] == 1:
            raise api_error(TelegramForbiddenError, "Forbidden")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    aiogram_bot.send_message.side_effect = send

    with pytest.raises(BotBlockedError):
        await bot.send_message_bulk("hi", fail_silently=False)

    assert cancelled.is_set()


async def test_unexpected_errors_propagate(bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
    aiogram_bot.send_message.side_effect = fail_for(2, RuntimeError("bug"))

    with pytest.raises(RuntimeError, match="bug"):
        await bot.send_message_bulk("hi")


@pytest.mark.parametrize("limit", [1, 3])
async def test_max_concurrent(aiogram_bot: MagicMock, limit: int) -> None:
    bot = TelegramNotificationBot(TOKEN, list(range(10)))
    active = peak = 0

    async def send(**kwargs: Any) -> None:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        for _ in range(3):
            await asyncio.sleep(0)
        active -= 1

    aiogram_bot.send_message.side_effect = send

    result = await bot.send_message_bulk("hi", max_concurrent=limit)

    assert result.successful_chats == 10
    assert peak == limit


@pytest.mark.parametrize("limit", [0, -1])
async def test_max_concurrent_must_be_positive(bot: TelegramNotificationBot, limit: int) -> None:
    with pytest.raises(ValueError, match="max_concurrent"):
        await bot.send_message_bulk("hi", max_concurrent=limit)


async def test_file_is_read_once(bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
    source = io.BytesIO(b"a,b\n")
    source.name = "status.csv"

    await bot.send_document_bulk(DocumentData(document=source, caption="report"))

    documents = [call.kwargs["document"] for call in aiogram_bot.send_document.await_args_list]
    assert len(documents) == 3
    assert all(document is documents[0] for document in documents)
    assert isinstance(documents[0], BufferedInputFile)
    assert documents[0].data == b"a,b\n"


async def test_photo_data(bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
    await bot.send_photo_bulk(PhotoData(photo="https://example.com/p.jpg", caption="chart"), caption="ignored")

    assert {call.kwargs["caption"] for call in aiogram_bot.send_photo.await_args_list} == {"chart"}
