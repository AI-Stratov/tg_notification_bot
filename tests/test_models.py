import pytest
from pydantic import ValidationError

from tests.helpers import TOKEN
from tg_notification_bot import BulkSendResult, DocumentData, MessageData, NotificationConfig, PhotoData, SendResult


class TestNotificationConfig:
    def test_defaults(self) -> None:
        config = NotificationConfig(token=TOKEN)

        assert config.chat_id is None
        assert config.parse_mode == "HTML"
        assert config.disable_notification is False
        assert config.protect_content is False

    @pytest.mark.parametrize("chat_id", [None, 42, "-100123", "@channel", [1, "@channel"]])
    def test_accepts_chat_ids(self, chat_id: int | str | list[int | str] | None) -> None:
        assert NotificationConfig(token=TOKEN, chat_id=chat_id).chat_id == chat_id

    @pytest.mark.parametrize(
        ("token", "error"),
        [
            ("", "Token cannot be empty"),
            ("no-colon", "Invalid bot token format"),
            ("1:2:3", "Invalid bot token format"),
        ],
    )
    def test_rejects_bad_token(self, token: str, error: str) -> None:
        with pytest.raises(ValidationError, match=error):
            NotificationConfig(token=token)

    @pytest.mark.parametrize(
        ("chat_id", "error"),
        [
            ("", "Chat ID cannot be empty string"),
            ("   ", "Chat ID cannot be empty string"),
            ([], "Chat ID list cannot be empty"),
            ([1, " "], "Chat ID cannot be empty string"),
        ],
    )
    def test_rejects_bad_chat_id(self, chat_id: str | list[int | str], error: str) -> None:
        with pytest.raises(ValidationError, match=error):
            NotificationConfig(token=TOKEN, chat_id=chat_id)

    def test_rejects_unknown_fields(self) -> None:
        with pytest.raises(ValidationError, match="extra"):
            NotificationConfig(token=TOKEN, chat=1)  # type: ignore[call-arg]

    def test_validates_assignment(self) -> None:
        config = NotificationConfig(token=TOKEN)

        with pytest.raises(ValidationError):
            config.parse_mode = "XML"  # type: ignore[assignment]


class TestMessageModels:
    def test_message_text_is_stripped(self) -> None:
        assert MessageData(text="  hello  ").text == "hello"

    @pytest.mark.parametrize("text", ["", "   ", "x" * 4097])
    def test_message_text_length(self, text: str) -> None:
        with pytest.raises(ValidationError):
            MessageData(text=text)

    def test_message_accepts_max_length(self) -> None:
        assert len(MessageData(text="x" * 4096).text) == 4096

    def test_options_default_to_none(self) -> None:
        data = MessageData(text="hi")

        assert (data.parse_mode, data.disable_notification, data.protect_content) == (None, None, None)

    @pytest.mark.parametrize("model", [PhotoData(photo="a.png"), DocumentData(document="a.pdf")])
    def test_caption_is_optional(self, model: PhotoData | DocumentData) -> None:
        assert model.caption is None

    def test_caption_length(self) -> None:
        with pytest.raises(ValidationError):
            PhotoData(photo="a.png", caption="x" * 1025)
        with pytest.raises(ValidationError):
            DocumentData(document="a.pdf", caption="x" * 1025)


class TestBulkSendResult:
    def test_properties(self) -> None:
        result = BulkSendResult(
            results=[
                SendResult(chat_id="1", success=True),
                SendResult(chat_id="2", success=False, error="boom"),
                SendResult(chat_id="3", success=True),
                SendResult(chat_id="4", success=True),
            ],
            total_chats=4,
            successful_chats=3,
            failed_chats=1,
        )

        assert result.success_rate == 75.0
        assert result.successful_chat_ids == ["1", "3", "4"]
        assert result.failed_chat_ids == ["2"]

    def test_empty(self) -> None:
        result = BulkSendResult(results=[], total_chats=0, successful_chats=0, failed_chats=0)

        assert result.success_rate == 0.0
        assert result.successful_chat_ids == []
        assert result.failed_chat_ids == []
