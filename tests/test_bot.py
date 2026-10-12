import io
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.types import BufferedInputFile, FSInputFile, URLInputFile

from tests.helpers import CHAT_ID, TOKEN, api_error
from tg_notification_bot import (
    BotBlockedError,
    ChatNotFoundError,
    DocumentData,
    InvalidChatIdError,
    MessageData,
    NotificationConfig,
    PhotoData,
    RateLimitError,
    TelegramNotificationBot,
    TelegramNotificationError,
)

PHOTO_URL = "https://example.com/photo.jpg"
DOCUMENT_URL = "https://example.com/report.pdf"

# (bot method, aiogram method, positional argument)
SEND_METHODS = [
    pytest.param("send_message", "send_message", "hello", id="message"),
    pytest.param("send_photo", "send_photo", PHOTO_URL, id="photo"),
    pytest.param("send_document", "send_document", DOCUMENT_URL, id="document"),
]


async def send(bot: TelegramNotificationBot, method: str, argument: Any, **kwargs: Any) -> None:
    await getattr(bot, method)(argument, **kwargs)


class TestInit:
    def test_with_config(self, aiogram_bot: MagicMock) -> None:
        config = NotificationConfig(token=TOKEN, chat_id=CHAT_ID)

        assert TelegramNotificationBot(config).config is config

    def test_with_token_and_chat_id(self, aiogram_bot: MagicMock) -> None:
        bot = TelegramNotificationBot(TOKEN, [1, "@channel"])

        assert bot.config.token == TOKEN
        assert bot.config.chat_id == [1, "@channel"]
        assert bot.bot is aiogram_bot

    def test_invalid_token(self, aiogram_bot: MagicMock) -> None:
        with pytest.raises(ValueError, match="Invalid bot token format"):
            TelegramNotificationBot("not-a-token", CHAT_ID)

    def test_missing_chat_id(self, aiogram_bot: MagicMock) -> None:
        with pytest.raises(ValueError, match="chat_id is required"):
            TelegramNotificationBot(TOKEN)

    @pytest.mark.parametrize(
        ("env", "expected"),
        [
            ({"TG_CHAT_ID": "123"}, "123"),
            ({"TG_CHAT_ID": " 1, 2 ,@channel,"}, ["1", "2", "@channel"]),
            ({"TG_CHAT_IDS": "1,2"}, ["1", "2"]),
            ({"TG_CHAT_ID": "1", "TG_CHAT_IDS": "2"}, "1"),
            ({"TG_CHAT_ID": " , ", "TG_CHAT_IDS": "2"}, "2"),
        ],
    )
    def test_chat_ids_from_env(
        self,
        aiogram_bot: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        env: dict[str, str],
        expected: str | list[str],
    ) -> None:
        for name, value in env.items():
            monkeypatch.setenv(name, value)

        assert TelegramNotificationBot(TOKEN).config.chat_id == expected

    def test_env_ignored_when_chat_id_given(self, aiogram_bot: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TG_CHAT_ID", "1")

        assert TelegramNotificationBot(TOKEN, 2).config.chat_id == 2


class TestSendOne:
    @pytest.mark.parametrize(("method", "aiogram_method", "argument"), SEND_METHODS)
    async def test_uses_config_defaults(
        self, bot: TelegramNotificationBot, aiogram_bot: MagicMock, method: str, aiogram_method: str, argument: Any
    ) -> None:
        await send(bot, method, argument)

        call = getattr(aiogram_bot, aiogram_method)
        call.assert_awaited_once()
        kwargs = call.await_args.kwargs
        assert kwargs["chat_id"] == CHAT_ID
        assert (kwargs["parse_mode"], kwargs["disable_notification"], kwargs["protect_content"]) == (
            "HTML",
            False,
            False,
        )

    async def test_message(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        await bot.send_message("hello")

        aiogram_bot.send_message.assert_awaited_once_with(
            chat_id=CHAT_ID, text="hello", parse_mode="HTML", disable_notification=False, protect_content=False
        )

    async def test_message_options_override_config_both_ways(self, aiogram_bot: MagicMock) -> None:
        config = NotificationConfig(
            token=TOKEN, chat_id=CHAT_ID, parse_mode="MarkdownV2", disable_notification=True, protect_content=True
        )
        bot = TelegramNotificationBot(config)

        await bot.send_message(
            MessageData(text="hi", parse_mode="HTML", disable_notification=False, protect_content=False)
        )

        kwargs = aiogram_bot.send_message.await_args.kwargs
        assert (kwargs["parse_mode"], kwargs["disable_notification"], kwargs["protect_content"]) == (
            "HTML",
            False,
            False,
        )

    async def test_unset_message_options_fall_back_to_config(self, aiogram_bot: MagicMock) -> None:
        config = NotificationConfig(token=TOKEN, chat_id=CHAT_ID, parse_mode="Markdown", protect_content=True)
        bot = TelegramNotificationBot(config)

        await bot.send_message(MessageData(text="hi", disable_notification=True))

        kwargs = aiogram_bot.send_message.await_args.kwargs
        assert (kwargs["parse_mode"], kwargs["disable_notification"], kwargs["protect_content"]) == (
            "Markdown",
            True,
            True,
        )

    async def test_photo_caption(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        await bot.send_photo(PHOTO_URL, caption="chart")

        assert aiogram_bot.send_photo.await_args.kwargs["caption"] == "chart"

    async def test_photo_data_caption_wins(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        await bot.send_photo(PhotoData(photo=PHOTO_URL, caption="from data", parse_mode="Markdown"), caption="ignored")

        kwargs = aiogram_bot.send_photo.await_args.kwargs
        assert (kwargs["caption"], kwargs["parse_mode"]) == ("from data", "Markdown")

    async def test_document_data(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        await bot.send_document(DocumentData(document=DOCUMENT_URL, caption="report", protect_content=True))

        kwargs = aiogram_bot.send_document.await_args.kwargs
        assert (kwargs["caption"], kwargs["protect_content"]) == ("report", True)

    @pytest.mark.parametrize(("method", "aiogram_method", "argument"), SEND_METHODS)
    async def test_chat_id_override(
        self, bot: TelegramNotificationBot, aiogram_bot: MagicMock, method: str, aiogram_method: str, argument: Any
    ) -> None:
        await send(bot, method, argument, chat_id=7)

        assert getattr(aiogram_bot, aiogram_method).await_args.kwargs["chat_id"] == 7

    async def test_list_with_one_chat(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        await bot.send_message("hi", chat_id=[7])

        assert aiogram_bot.send_message.await_args.kwargs["chat_id"] == 7

    @pytest.mark.parametrize(("method", "aiogram_method", "argument"), SEND_METHODS)
    async def test_several_chats_rejected(
        self, aiogram_bot: MagicMock, method: str, aiogram_method: str, argument: Any
    ) -> None:
        bot = TelegramNotificationBot(TOKEN, [1, 2])

        with pytest.raises(ValueError, match=f"Use {method}_bulk for multiple chats"):
            await send(bot, method, argument)
        getattr(aiogram_bot, aiogram_method).assert_not_awaited()

    async def test_no_chat_ids(self, aiogram_bot: MagicMock) -> None:
        bot = TelegramNotificationBot(NotificationConfig(token=TOKEN))

        with pytest.raises(ValueError, match="No chat IDs specified"):
            await bot.send_message("hi")
        with pytest.raises(ValueError, match="No chat IDs specified"):
            await bot.send_message("hi", chat_id=[])


class TestErrors:
    @pytest.mark.parametrize(("method", "aiogram_method", "argument"), SEND_METHODS)
    @pytest.mark.parametrize(
        ("error", "expected_type", "expected_text"),
        [
            (api_error(TelegramForbiddenError, "Forbidden: bot was blocked by the user"), BotBlockedError, "blocked"),
            (api_error(TelegramBadRequest, "Bad Request: chat not found"), ChatNotFoundError, "not found"),
            (
                api_error(TelegramBadRequest, "Bad Request: message is too long"),
                TelegramNotificationError,
                "Bad request",
            ),
            (api_error(TelegramRetryAfter, "Too Many Requests", retry_after=30), RateLimitError, "Retry after 30"),
            (api_error(TelegramNetworkError, "timeout"), TelegramNotificationError, "Telegram API error"),
        ],
    )
    async def test_translated(
        self,
        bot: TelegramNotificationBot,
        aiogram_bot: MagicMock,
        method: str,
        aiogram_method: str,
        argument: Any,
        error: Exception,
        expected_type: type[TelegramNotificationError],
        expected_text: str,
    ) -> None:
        getattr(aiogram_bot, aiogram_method).side_effect = error

        with pytest.raises(expected_type, match=expected_text) as exc_info:
            await send(bot, method, argument)

        assert type(exc_info.value) is expected_type
        assert exc_info.value.chat_id == str(CHAT_ID)
        assert exc_info.value.__cause__ is error

    async def test_rate_limit_retry_after(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        aiogram_bot.send_message.side_effect = api_error(TelegramRetryAfter, "Too Many Requests", retry_after=12)

        with pytest.raises(RateLimitError) as exc_info:
            await bot.send_message("hi")

        assert exc_info.value.retry_after == 12

    async def test_other_errors_are_not_wrapped(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        aiogram_bot.send_message.side_effect = RuntimeError("bug")

        with pytest.raises(RuntimeError, match="bug"):
            await bot.send_message("hi")


class TestChatIdResolution:
    @pytest.mark.parametrize(
        ("chat_id", "sent_as"),
        [(42, 42), (-100123, -100123), ("@channel", "@channel"), ("-100123", "-100123"), (" -4321 ", "-4321")],
    )
    async def test_sent_as_given(
        self, bot: TelegramNotificationBot, aiogram_bot: MagicMock, chat_id: int | str, sent_as: int | str
    ) -> None:
        await bot.send_message("hi", chat_id=chat_id)

        aiogram_bot.get_chat.assert_not_awaited()
        assert aiogram_bot.send_message.await_args.kwargs["chat_id"] == sent_as

    @pytest.mark.parametrize(
        ("failures", "sent_as"),
        [(0, "123"), (1, "-123"), (2, "-100123")],
    )
    async def test_digits_try_prefixes(
        self, bot: TelegramNotificationBot, aiogram_bot: MagicMock, failures: int, sent_as: str
    ) -> None:
        aiogram_bot.get_chat.side_effect = [api_error(TelegramBadRequest, "chat not found")] * failures + [None]

        await bot.send_message("hi", chat_id="123")

        assert [call.args[0] for call in aiogram_bot.get_chat.await_args_list] == ["123", "-123", "-100123"][
            : failures + 1
        ]
        assert aiogram_bot.send_message.await_args.kwargs["chat_id"] == sent_as

    async def test_resolution_is_cached(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        aiogram_bot.get_chat.side_effect = [api_error(TelegramBadRequest, "chat not found"), None]

        await bot.send_message("first", chat_id="123")
        await bot.send_message("second", chat_id="123")

        assert aiogram_bot.get_chat.await_count == 2
        assert [call.kwargs["chat_id"] for call in aiogram_bot.send_message.await_args_list] == ["-123", "-123"]

    async def test_not_found(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        aiogram_bot.get_chat.side_effect = api_error(TelegramBadRequest, "chat not found")

        with pytest.raises(ChatNotFoundError, match="'123'"):
            await bot.send_message("hi", chat_id="123")

        assert aiogram_bot.get_chat.await_count == 3
        aiogram_bot.send_message.assert_not_awaited()

    async def test_lookup_errors_are_translated(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        aiogram_bot.get_chat.side_effect = api_error(TelegramForbiddenError, "Forbidden")

        with pytest.raises(BotBlockedError):
            await bot.send_message("hi", chat_id="123")

    @pytest.mark.parametrize("chat_id", ["", "   "])
    async def test_blank_override(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock, chat_id: str) -> None:
        with pytest.raises(InvalidChatIdError):
            await bot.send_message("hi", chat_id=chat_id)


class TestFiles:
    async def test_local_path(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock, tmp_path: Path) -> None:
        report = tmp_path / "report.pdf"
        report.write_bytes(b"%PDF")

        await bot.send_document(report)
        await bot.send_document(str(report))

        for call in aiogram_bot.send_document.await_args_list:
            document = call.kwargs["document"]
            assert isinstance(document, FSInputFile)
            assert Path(document.path) == report

    @pytest.mark.parametrize("name", ["missing.pdf", "."])
    async def test_missing_or_not_a_file(
        self, bot: TelegramNotificationBot, aiogram_bot: MagicMock, tmp_path: Path, name: str
    ) -> None:
        with pytest.raises(FileNotFoundError):
            await bot.send_document(tmp_path / name)

        aiogram_bot.send_document.assert_not_awaited()

    async def test_url(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        await bot.send_photo(PHOTO_URL)

        photo = aiogram_bot.send_photo.await_args.kwargs["photo"]
        assert isinstance(photo, URLInputFile)
        assert photo.url == PHOTO_URL

    @pytest.mark.parametrize(("name", "filename"), [("reports/status.csv", "status.csv"), (None, "file"), (3, "file")])
    async def test_file_object(
        self, bot: TelegramNotificationBot, aiogram_bot: MagicMock, name: object, filename: str
    ) -> None:
        source = io.BytesIO(b"a,b\n")
        if name is not None:
            source.name = name

        await bot.send_document(source)

        document = aiogram_bot.send_document.await_args.kwargs["document"]
        assert isinstance(document, BufferedInputFile)
        assert (document.data, document.filename) == (b"a,b\n", filename)

    async def test_text_file_object(self, bot: TelegramNotificationBot) -> None:
        with pytest.raises(TypeError, match="binary mode"):
            await bot.send_document(io.StringIO("text"))  # type: ignore[arg-type]

    async def test_unsupported_source(self, bot: TelegramNotificationBot) -> None:
        with pytest.raises(TypeError, match="Unsupported file source: bytes"):
            await bot.send_document(b"raw bytes")  # type: ignore[arg-type]


class TestLifecycle:
    async def test_close(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        await bot.close()

        aiogram_bot.session.close.assert_awaited_once()

    async def test_context_manager(self, bot: TelegramNotificationBot, aiogram_bot: MagicMock) -> None:
        async with bot as entered:
            assert entered is bot
            aiogram_bot.session.close.assert_not_awaited()

        aiogram_bot.session.close.assert_awaited_once()
