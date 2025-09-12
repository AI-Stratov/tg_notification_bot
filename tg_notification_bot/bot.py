"""Modern Telegram notification bot implementation."""

import asyncio
import os
from pathlib import Path
from typing import IO, Any, List, Optional, Union

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
from .models import (
    DocumentData,
    MessageData,
    NotificationConfig,
    PhotoData,
    SendResult,
    BulkSendResult,
)


class TelegramNotificationBot:
    """Modern Telegram notification bot with type safety and proper error handling."""

    def __init__(
        self,
        token: Union[NotificationConfig, str],
        chat_id: Optional[Union[int, str, List[Union[int, str]]]] = None,
    ):
        """
        Initialize the Telegram notification bot.

        Args:
            token: NotificationConfig instance or bot token string
            chat_id: Target chat ID(s) (required if token is a string)

        Raises:
            ValueError: If configuration is invalid
        """
        if isinstance(token, str):
            # Try to load chat_id from environment if not provided
            if chat_id is None:
                env_chat_id = self._load_chat_ids_from_env()
                if env_chat_id is None:
                    raise ValueError("chat_id is required when token is a token string and TG_CHAT_ID is not set")
                # Type cast to satisfy mypy - env_chat_id is compatible with expected type
                chat_id = env_chat_id  # type: ignore[assignment]
            self.config = NotificationConfig(token=token, chat_id=chat_id)
        else:
            self.config = token

        self.bot = Bot(token=self.config.token)

    @staticmethod
    def _load_chat_ids_from_env() -> Optional[Union[str, List[str]]]:
        """
        Load chat IDs from environment variables.

        Supports:
        - TG_CHAT_ID: Single chat ID or comma-separated list
        - TG_CHAT_IDS: Comma-separated list of chat IDs

        Returns:
            Single chat ID, list of chat IDs, or None if not found
        """
        # Try TG_CHAT_ID first
        chat_id_env = os.getenv("TG_CHAT_ID")
        if chat_id_env:
            chat_ids = [cid.strip() for cid in chat_id_env.split(",") if cid.strip()]
            return chat_ids[0] if len(chat_ids) == 1 else chat_ids

        # Try TG_CHAT_IDS as alternative
        chat_ids_env = os.getenv("TG_CHAT_IDS")
        if chat_ids_env:
            chat_ids = [cid.strip() for cid in chat_ids_env.split(",") if cid.strip()]
            return chat_ids[0] if len(chat_ids) == 1 else chat_ids

        return None

    def _get_target_chat_ids(self, chat_id: Optional[Union[int, str, List[Union[int, str]]]]) -> List[Union[int, str]]:
        """
        Get list of target chat IDs.

        Args:
            chat_id: Override chat ID(s) or None to use config

        Returns:
            List of chat IDs to send to

        Raises:
            ValueError: If no chat IDs are available
        """
        target = chat_id if chat_id is not None else self.config.chat_id

        if target is None:
            raise ValueError("No chat IDs specified")

        if isinstance(target, list):
            return target
        else:
            return [target]

    async def send_message(
        self,
        message: Union[str, MessageData],
        chat_id: Optional[Union[int, str, List[Union[int, str]]]] = None,
    ) -> None:
        """
        Send a text message to single chat.

        Args:
            message: Message text or MessageData instance
            chat_id: Override default chat ID

        Raises:
            ChatNotFoundError: If chat is not found
            BotBlockedError: If bot is blocked
            RateLimitError: If rate limit is exceeded
            TelegramNotificationError: For other Telegram errors
        """
        chat_ids = self._get_target_chat_ids(chat_id)
        if len(chat_ids) > 1:
            raise ValueError("Use send_message_bulk for multiple chats")

        target_chat_id = chat_ids[0]
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
                disable_notification=message_data.disable_notification or self.config.disable_notification,
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

    async def send_message_bulk(
        self,
        message: Union[str, MessageData],
        chat_ids: Optional[List[Union[int, str]]] = None,
        fail_silently: bool = True,
        max_concurrent: int = 10,
    ) -> BulkSendResult:
        """
        Send a text message to multiple chats.

        Args:
            message: Message text or MessageData instance
            chat_ids: List of chat IDs (uses config chat_ids if None)
            fail_silently: Continue sending to other chats if one fails
            max_concurrent: Maximum number of concurrent sends

        Returns:
            BulkSendResult with details about each send attempt
        """
        target_chat_ids = chat_ids if chat_ids is not None else self._get_target_chat_ids(None)

        if isinstance(message, str):
            message_data = MessageData(text=message)
        else:
            message_data = message

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_to_chat(chat_id: Union[int, str]) -> SendResult:
            async with semaphore:
                try:
                    normalized_chat_id = await self._normalize_chat_id(chat_id)
                    await self.bot.send_message(
                        chat_id=normalized_chat_id,
                        text=message_data.text,
                        parse_mode=message_data.parse_mode or self.config.parse_mode,
                        disable_notification=message_data.disable_notification or self.config.disable_notification,
                        protect_content=message_data.protect_content or self.config.protect_content,
                    )
                    return SendResult(chat_id=str(chat_id), success=True, error=None, exception=None)
                except Exception as e:
                    error_msg = str(e)
                    if not fail_silently:
                        # Re-raise original exception for specific error types
                        if isinstance(e, (BotBlockedError, ChatNotFoundError, RateLimitError)):
                            raise
                    return SendResult(chat_id=str(chat_id), success=False, error=error_msg, exception=e)

        # Execute all sends concurrently
        tasks = [send_to_chat(chat_id) for chat_id in target_chat_ids]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Count successes and failures
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return BulkSendResult(
            results=results,
            total_chats=len(target_chat_ids),
            successful_chats=successful,
            failed_chats=failed,
        )

    async def send_photo(
        self,
        photo: Union[str, Path, IO[bytes], PhotoData],
        caption: Optional[str] = None,
        chat_id: Optional[Union[int, str, List[Union[int, str]]]] = None,
    ) -> None:
        """
        Send a photo to single chat.

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
        chat_ids = self._get_target_chat_ids(chat_id)
        if len(chat_ids) > 1:
            raise ValueError("Use send_photo_bulk for multiple chats")

        target_chat_id = chat_ids[0]
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
                disable_notification=photo_data.disable_notification or self.config.disable_notification,
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

    async def send_photo_bulk(
        self,
        photo: Union[str, Path, IO[bytes], PhotoData],
        caption: Optional[str] = None,
        chat_ids: Optional[List[Union[int, str]]] = None,
        fail_silently: bool = True,
        max_concurrent: int = 10,
    ) -> BulkSendResult:
        """
        Send a photo to multiple chats.

        Args:
            photo: Photo file path, URL, file-like object, or PhotoData instance
            caption: Photo caption (ignored if photo is PhotoData)
            chat_ids: List of chat IDs (uses config chat_ids if None)
            fail_silently: Continue sending to other chats if one fails
            max_concurrent: Maximum number of concurrent sends

        Returns:
            BulkSendResult with details about each send attempt
        """
        target_chat_ids = chat_ids if chat_ids is not None else self._get_target_chat_ids(None)

        if isinstance(photo, PhotoData):
            photo_data = photo
        else:
            photo_data = PhotoData(photo=photo, caption=caption)

        # Prepare file input once for all chats
        photo_input = self._prepare_file_input(photo_data.photo)

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_to_chat(chat_id: Union[int, str]) -> SendResult:
            async with semaphore:
                try:
                    normalized_chat_id = await self._normalize_chat_id(chat_id)
                    await self.bot.send_photo(
                        chat_id=normalized_chat_id,
                        photo=photo_input,
                        caption=photo_data.caption,
                        parse_mode=photo_data.parse_mode or self.config.parse_mode,
                        disable_notification=photo_data.disable_notification or self.config.disable_notification,
                        protect_content=photo_data.protect_content or self.config.protect_content,
                    )
                    return SendResult(chat_id=str(chat_id), success=True, error=None, exception=None)
                except Exception as e:
                    error_msg = str(e)
                    if not fail_silently:
                        if isinstance(e, (BotBlockedError, ChatNotFoundError, RateLimitError)):
                            raise
                    return SendResult(chat_id=str(chat_id), success=False, error=error_msg, exception=e)

        # Execute all sends concurrently
        tasks = [send_to_chat(chat_id) for chat_id in target_chat_ids]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Count successes and failures
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return BulkSendResult(
            results=results,
            total_chats=len(target_chat_ids),
            successful_chats=successful,
            failed_chats=failed,
        )

    async def send_document(
        self,
        document: Union[str, Path, IO[bytes], DocumentData],
        caption: Optional[str] = None,
        chat_id: Optional[Union[int, str, List[Union[int, str]]]] = None,
    ) -> None:
        """
        Send a document to single chat.

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
        chat_ids = self._get_target_chat_ids(chat_id)
        if len(chat_ids) > 1:
            raise ValueError("Use send_document_bulk for multiple chats")

        target_chat_id = chat_ids[0]
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
                disable_notification=document_data.disable_notification or self.config.disable_notification,
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

    async def send_document_bulk(
        self,
        document: Union[str, Path, IO[bytes], DocumentData],
        caption: Optional[str] = None,
        chat_ids: Optional[List[Union[int, str]]] = None,
        fail_silently: bool = True,
        max_concurrent: int = 10,
    ) -> BulkSendResult:
        """
        Send a document to multiple chats.

        Args:
            document: Document file path, URL, file-like object, or DocumentData
            caption: Document caption (ignored if document is DocumentData)
            chat_ids: List of chat IDs (uses config chat_ids if None)
            fail_silently: Continue sending to other chats if one fails
            max_concurrent: Maximum number of concurrent sends

        Returns:
            BulkSendResult with details about each send attempt
        """
        target_chat_ids = chat_ids if chat_ids is not None else self._get_target_chat_ids(None)

        if isinstance(document, DocumentData):
            document_data = document
        else:
            document_data = DocumentData(document=document, caption=caption)

        # Prepare file input once for all chats
        document_input = self._prepare_file_input(document_data.document)

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_to_chat(chat_id: Union[int, str]) -> SendResult:
            async with semaphore:
                try:
                    normalized_chat_id = await self._normalize_chat_id(chat_id)
                    await self.bot.send_document(
                        chat_id=normalized_chat_id,
                        document=document_input,
                        caption=document_data.caption,
                        parse_mode=document_data.parse_mode or self.config.parse_mode,
                        disable_notification=document_data.disable_notification or self.config.disable_notification,
                        protect_content=document_data.protect_content or self.config.protect_content,
                    )
                    return SendResult(chat_id=str(chat_id), success=True, error=None, exception=None)
                except Exception as e:
                    error_msg = str(e)
                    if not fail_silently:
                        if isinstance(e, (BotBlockedError, ChatNotFoundError, RateLimitError)):
                            raise
                    return SendResult(chat_id=str(chat_id), success=False, error=error_msg, exception=e)

        # Execute all sends concurrently
        tasks = [send_to_chat(chat_id) for chat_id in target_chat_ids]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Count successes and failures
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return BulkSendResult(
            results=results,
            total_chats=len(target_chat_ids),
            successful_chats=successful,
            failed_chats=failed,
        )

    async def close(self) -> None:
        """Close the bot session."""
        await self.bot.session.close()

    async def __aenter__(self) -> "TelegramNotificationBot":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _prepare_file_input(self, file_input: Union[str, Path, IO[bytes]]) -> Union[FSInputFile, URLInputFile, BufferedInputFile]:
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
