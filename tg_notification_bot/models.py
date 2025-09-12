"""Pydantic models for Telegram notification bot configuration."""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationConfig(BaseModel):
    """Configuration for Telegram notification bot."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    token: str = Field(..., description="Telegram bot token")
    chat_id: Optional[Union[int, str, List[Union[int, str]]]] = Field(
        default=None, description="Target chat ID(s). Can be single ID or list of IDs"
    )
    parse_mode: Literal["HTML", "Markdown", "MarkdownV2"] = Field(default="HTML", description="Message parse mode")
    disable_notification: bool = Field(default=False, description="Send message silently")
    protect_content: bool = Field(default=False, description="Protect message content from forwarding")

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate bot token format."""
        if not v:
            raise ValueError("Token cannot be empty")
        if not v.count(":") == 1:
            raise ValueError("Invalid bot token format")
        return v

    @field_validator("chat_id")
    @classmethod
    def validate_chat_id(cls, v: Optional[Union[int, str, List[Union[int, str]]]]) -> Optional[Union[int, str, List[Union[int, str]]]]:
        """Validate chat ID(s)."""
        if v is None:
            return v

        if isinstance(v, list):
            if not v:
                raise ValueError("Chat ID list cannot be empty")
            for chat_id in v:
                if isinstance(chat_id, str) and not chat_id.strip():
                    raise ValueError("Chat ID cannot be empty string")
            return v

        if isinstance(v, str) and not v.strip():
            raise ValueError("Chat ID cannot be empty string")
        return v


class MessageData(BaseModel):
    """Message data model."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=1, max_length=4096, description="Message text")
    parse_mode: Optional[Literal["HTML", "Markdown", "MarkdownV2"]] = None
    disable_notification: Optional[bool] = None
    protect_content: Optional[bool] = None


class PhotoData(BaseModel):
    """Photo data model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    photo: Any = Field(..., description="Photo file path, URL, or file-like object")
    caption: Optional[str] = Field(None, max_length=1024, description="Photo caption")
    parse_mode: Optional[Literal["HTML", "Markdown", "MarkdownV2"]] = None
    disable_notification: Optional[bool] = None
    protect_content: Optional[bool] = None


class DocumentData(BaseModel):
    """Document data model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    document: Any = Field(..., description="Document file path, URL, or file-like object")
    caption: Optional[str] = Field(None, max_length=1024, description="Document caption")
    parse_mode: Optional[Literal["HTML", "Markdown", "MarkdownV2"]] = None
    disable_notification: Optional[bool] = None
    protect_content: Optional[bool] = None


class SendResult(BaseModel):
    """Result of sending message to a single chat."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    chat_id: str = Field(..., description="Chat ID where message was sent")
    success: bool = Field(..., description="Whether the message was sent successfully")
    error: Optional[str] = Field(None, description="Error message if failed")
    exception: Optional[Exception] = Field(None, description="Original exception if failed")


class BulkSendResult(BaseModel):
    """Result of sending messages to multiple chats."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    results: List[SendResult] = Field(..., description="Results for each chat")
    total_chats: int = Field(..., description="Total number of chats attempted")
    successful_chats: int = Field(..., description="Number of successful sends")
    failed_chats: int = Field(..., description="Number of failed sends")

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_chats == 0:
            return 0.0
        return (self.successful_chats / self.total_chats) * 100

    @property
    def successful_chat_ids(self) -> List[str]:
        """Get list of chat IDs where message was sent successfully."""
        return [result.chat_id for result in self.results if result.success]

    @property
    def failed_chat_ids(self) -> List[str]:
        """Get list of chat IDs where message failed to send."""
        return [result.chat_id for result in self.results if not result.success]
