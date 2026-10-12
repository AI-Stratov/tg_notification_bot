"""Pydantic models for configuration, message options and send results."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ParseMode = Literal["HTML", "Markdown", "MarkdownV2"]
ChatId = int | str
ChatIds = ChatId | list[ChatId]


class NotificationConfig(BaseModel):
    """Configuration for Telegram notification bot."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    token: str = Field(..., description="Telegram bot token")
    chat_id: ChatIds | None = Field(default=None, description="Target chat ID(s). Can be single ID or list of IDs")
    parse_mode: ParseMode = Field(default="HTML", description="Message parse mode")
    disable_notification: bool = Field(default=False, description="Send message silently")
    protect_content: bool = Field(default=False, description="Protect message content from forwarding")

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate bot token format."""
        if not v:
            raise ValueError("Token cannot be empty")
        if v.count(":") != 1:
            raise ValueError("Invalid bot token format")
        return v

    @field_validator("chat_id")
    @classmethod
    def validate_chat_id(cls, v: ChatIds | None) -> ChatIds | None:
        """Validate chat ID(s)."""
        if v is None:
            return v
        chat_ids = v if isinstance(v, list) else [v]
        if not chat_ids:
            raise ValueError("Chat ID list cannot be empty")
        if any(isinstance(chat_id, str) and not chat_id.strip() for chat_id in chat_ids):
            raise ValueError("Chat ID cannot be empty string")
        return v


class _SendOptions(BaseModel):
    """Per-message options. None means "use the value from NotificationConfig"."""

    parse_mode: ParseMode | None = None
    disable_notification: bool | None = None
    protect_content: bool | None = None


class MessageData(_SendOptions):
    """Message data model."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=1, max_length=4096, description="Message text")


class PhotoData(_SendOptions):
    """Photo data model."""

    photo: Any = Field(..., description="Photo file path, URL, or file-like object")
    caption: str | None = Field(default=None, max_length=1024, description="Photo caption")


class DocumentData(_SendOptions):
    """Document data model."""

    document: Any = Field(..., description="Document file path, URL, or file-like object")
    caption: str | None = Field(default=None, max_length=1024, description="Document caption")


class SendResult(BaseModel):
    """Result of sending message to a single chat."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    chat_id: str = Field(..., description="Chat ID where message was sent")
    success: bool = Field(..., description="Whether the message was sent successfully")
    error: str | None = Field(default=None, description="Error message if failed")
    exception: Exception | None = Field(default=None, description="Original exception if failed")


class BulkSendResult(BaseModel):
    """Result of sending messages to multiple chats."""

    results: list[SendResult] = Field(..., description="Results for each chat")
    total_chats: int = Field(..., description="Total number of chats attempted")
    successful_chats: int = Field(..., description="Number of successful sends")
    failed_chats: int = Field(..., description="Number of failed sends")

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_chats == 0:
            return 0.0
        return self.successful_chats / self.total_chats * 100

    @property
    def successful_chat_ids(self) -> list[str]:
        """Get list of chat IDs where message was sent successfully."""
        return [result.chat_id for result in self.results if result.success]

    @property
    def failed_chat_ids(self) -> list[str]:
        """Get list of chat IDs where message failed to send."""
        return [result.chat_id for result in self.results if not result.success]
