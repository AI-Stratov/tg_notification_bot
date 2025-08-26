"""Modern Telegram notification bot implementation."""

from pathlib import Path
from typing import IO, Any, Optional, Union

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.types import BufferedInputFile, FSInputFile, URLInputFile

from .exceptions import (
    BotBlockedError,
    ChatNotFoundError,
    InvalidChatIdError,
    RateLimitError,
    TelegramNotificationError,
)
from .models import DocumentData, MessageData, NotificationConfig, PhotoData


class TelegramNotificationBot:
    """Modern Telegram notification bot with type safety and proper error handling."""

    def __init__(
        self,
        token: Union[NotificationConfig, str],
        chat_id: Optional[Union[int, str]] = None,
    ):
        """
        Initialize the Telegram notification bot.

        Args:
            token: NotificationConfig instance or bot token string
            chat_id: Target chat ID (required if token is a string)

        Raises:
            ValueError: If configuration is invalid
        """
        if isinstance(token, str):
            if chat_id is None:
                raise ValueError("chat_id is required when token is a token string")
            self.config = NotificationConfig(token=token, chat_id=chat_id)
        else:
            self.config = token

        self.bot = Bot(token=self.config.token)

    async def send_message(
        self,
        message: Union[str, MessageData],
        chat_id: Optional[Union[int, str]] = None,
    ) -> None:
        """
        Send a text message.

        Args:
            message: Message text or MessageData instance
            chat_id: Override default chat ID

        Raises:
            ChatNotFoundError: If chat is not found
            BotBlockedError: If bot is blocked
            RateLimitError: If rate limit is exceeded
            TelegramNotificationError: For other Telegram errors
        """
        target_chat_id = chat_id or self.config.chat_id
        normalized_chat_id = await self._normalize_chat_id(target_chat_id)

        if isinstance(message, str):
            message_data = MessageData(text=message)
        else:
            message_data = message

        try:
            await self.bot.send_message(
                chat_id=normalized_chat_id,
                text=message_data.text,
                parse_mode=message_data.parse_mode or self.config.parse_mode,
                disable_notification=message_data.disable_notification
                or self.config.disable_notification,
                protect_content=message_data.protect_content or self.config.protect_content,
            )
        except TelegramForbiddenError:
            raise BotBlockedError(str(target_chat_id))
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                raise ChatNotFoundError(str(target_chat_id))
            raise TelegramNotificationError(f"Bad request: {e}", str(target_chat_id))
        except TelegramRetryAfter as e:
            raise RateLimitError(e.retry_after, str(target_chat_id))
        except Exception as e:
            raise TelegramNotificationError(f"Unexpected error: {e}", str(target_chat_id))

    async def send_photo(
        self,
        photo: Union[str, Path, IO[bytes], PhotoData],
        caption: Optional[str] = None,
        chat_id: Optional[Union[int, str]] = None,
    ) -> None:
        """
        Send a photo.

        Args:
            photo: Photo file path, URL, file-like object, or PhotoData instance
            caption: Photo caption (ignored if photo is PhotoData)
            chat_id: Override default chat ID

        Raises:
            ChatNotFoundError: If chat is not found
            BotBlockedError: If bot is blocked
            RateLimitError: If rate limit is exceeded
            TelegramNotificationError: For other Telegram errors
        """
        target_chat_id = chat_id or self.config.chat_id
        normalized_chat_id = await self._normalize_chat_id(target_chat_id)

        if isinstance(photo, PhotoData):
            photo_data = photo
            photo_input = self._prepare_file_input(photo_data.photo)
        else:
            photo_data = PhotoData(photo=photo, caption=caption)
            photo_input = self._prepare_file_input(photo)

        try:
            await self.bot.send_photo(
                chat_id=normalized_chat_id,
                photo=photo_input,
                caption=photo_data.caption,
                parse_mode=photo_data.parse_mode or self.config.parse_mode,
                disable_notification=photo_data.disable_notification
                or self.config.disable_notification,
                protect_content=photo_data.protect_content or self.config.protect_content,
            )
        except TelegramForbiddenError:
            raise BotBlockedError(str(target_chat_id))
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                raise ChatNotFoundError(str(target_chat_id))
            raise TelegramNotificationError(f"Bad request: {e}", str(target_chat_id))
        except TelegramRetryAfter as e:
            raise RateLimitError(e.retry_after, str(target_chat_id))
        except Exception as e:
            raise TelegramNotificationError(f"Unexpected error: {e}", str(target_chat_id))

    async def send_document(
        self,
        document: Union[str, Path, IO[bytes], DocumentData],
        caption: Optional[str] = None,
        chat_id: Optional[Union[int, str]] = None,
    ) -> None:
        """
        Send a document.

        Args:
            document: Document file path, URL, file-like object, or DocumentData
            caption: Document caption (ignored if document is DocumentData)
            chat_id: Override default chat ID

        Raises:
            ChatNotFoundError: If chat is not found
            BotBlockedError: If bot is blocked
            RateLimitError: If rate limit is exceeded
            TelegramNotificationError: For other Telegram errors
        """
        target_chat_id = chat_id or self.config.chat_id
        normalized_chat_id = await self._normalize_chat_id(target_chat_id)

        if isinstance(document, DocumentData):
            document_data = document
            document_input = self._prepare_file_input(document_data.document)
        else:
            document_data = DocumentData(document=document, caption=caption)
            document_input = self._prepare_file_input(document)

        try:
            await self.bot.send_document(
                chat_id=normalized_chat_id,
                document=document_input,
                caption=document_data.caption,
                parse_mode=document_data.parse_mode or self.config.parse_mode,
                disable_notification=document_data.disable_notification
                or self.config.disable_notification,
                protect_content=document_data.protect_content or self.config.protect_content,
            )
        except TelegramForbiddenError:
            raise BotBlockedError(str(target_chat_id))
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                raise ChatNotFoundError(str(target_chat_id))
            raise TelegramNotificationError(f"Bad request: {e}", str(target_chat_id))
        except TelegramRetryAfter as e:
            raise RateLimitError(e.retry_after, str(target_chat_id))
        except Exception as e:
            raise TelegramNotificationError(f"Unexpected error: {e}", str(target_chat_id))

    async def close(self) -> None:
        """Close the bot session."""
        await self.bot.session.close()

    async def __aenter__(self) -> "TelegramNotificationBot":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _prepare_file_input(
        self, file_input: Union[str, Path, IO[bytes]]
    ) -> Union[FSInputFile, URLInputFile, BufferedInputFile]:
        """
        Prepare file input for aiogram.

        Args:
            file_input: File path, URL, or file-like object

        Returns:
            Appropriate aiogram input file type
        """
        if hasattr(file_input, "read"):  # File-like object
            data = file_input.read()
            if hasattr(file_input, "name"):
                filename = Path(file_input.name).name
            else:
                filename = "file"
            return BufferedInputFile(data, filename=filename)

        file_str = str(file_input)
        if file_str.startswith(("http://", "https://")):
            return URLInputFile(file_str)

        file_path = Path(file_str)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        return FSInputFile(file_path)

    async def _normalize_chat_id(self, chat_id: Union[int, str]) -> str:
        """
        Normalize and validate chat ID.

        Args:
            chat_id: Chat ID to normalize

        Returns:
            Normalized chat ID as string

        Raises:
            ChatNotFoundError: If chat is not found
            InvalidChatIdError: If chat ID format is invalid
        """
        if isinstance(chat_id, int):
            return str(chat_id)

        chat_id_str = str(chat_id).strip()
        if not chat_id_str:
            raise InvalidChatIdError("empty string")

        # If already has proper group prefix, return as is
        if chat_id_str.startswith("-100") or chat_id_str.startswith("-"):
            try:
                await self.bot.get_chat(chat_id_str)
                return chat_id_str
            except TelegramBadRequest:
                raise ChatNotFoundError(chat_id_str)

        # Try original format first
        try:
            await self.bot.get_chat(chat_id_str)
            return chat_id_str
        except TelegramBadRequest:
            pass

        # Try with group prefix
        try:
            modified_chat_id = f"-{chat_id_str}"
            await self.bot.get_chat(modified_chat_id)
            return modified_chat_id
        except TelegramBadRequest:
            pass

        # Try with supergroup prefix
        try:
            modified_chat_id = f"-100{chat_id_str}"
            await self.bot.get_chat(modified_chat_id)
            return modified_chat_id
        except TelegramBadRequest:
            raise ChatNotFoundError(chat_id_str)
