"""Pydantic models for Telegram notification bot configuration."""

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationConfig(BaseModel):
    """Configuration for Telegram notification bot."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    token: str = Field(..., description="Telegram bot token")
    chat_id: Union[int, str] = Field(..., description="Target chat ID")
    parse_mode: Literal["HTML", "Markdown", "MarkdownV2"] = Field(
        default="HTML", description="Message parse mode"
    )
    disable_notification: bool = Field(default=False, description="Send message silently")
    protect_content: bool = Field(
        default=False, description="Protect message content from forwarding"
    )

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
    def validate_chat_id(cls, v: Union[int, str]) -> Union[int, str]:
        """Validate chat ID."""
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
