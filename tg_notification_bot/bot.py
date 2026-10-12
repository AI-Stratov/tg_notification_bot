"""Telegram notification bot."""

import asyncio
import os
from collections.abc import Awaitable, Callable, Sequence
from functools import partial
from pathlib import Path
from typing import IO, Any, TypeVar

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.types import BufferedInputFile, FSInputFile, InputFile, URLInputFile

from .exceptions import (
    BotBlockedError,
    ChatNotFoundError,
    InvalidChatIdError,
    RateLimitError,
    TelegramNotificationError,
)
from .models import (
    BulkSendResult,
    ChatId,
    ChatIds,
    DocumentData,
    MessageData,
    NotificationConfig,
    PhotoData,
    SendResult,
)

FileSource = str | Path | IO[bytes]
T = TypeVar("T")
_Sender = Callable[..., Awaitable[Any]]

# Read in this order when the bot is created with a token string and no chat_id.
_CHAT_ID_ENV_VARS = ("TG_CHAT_ID", "TG_CHAT_IDS")
# Telegram clients often show group and supergroup IDs without these prefixes.
_CHAT_ID_PREFIXES = ("", "-", "-100")


class TelegramNotificationBot:
    """Send messages, photos and documents to one or more Telegram chats."""

    def __init__(self, token: NotificationConfig | str, chat_id: ChatIds | None = None):
        """
        Initialize the Telegram notification bot.

        Args:
            token: NotificationConfig instance or bot token string
            chat_id: Target chat ID(s). If omitted with a token string, TG_CHAT_ID or TG_CHAT_IDS is used.

        Raises:
            ValueError: If configuration is invalid or no chat ID is available
        """
        if isinstance(token, NotificationConfig):
            self.config = token
        else:
            chat_id = chat_id if chat_id is not None else _chat_ids_from_env()
            if chat_id is None:
                raise ValueError("chat_id is required when token is a token string and TG_CHAT_ID is not set")
            self.config = NotificationConfig(token=token, chat_id=chat_id)

        self.bot = Bot(token=self.config.token)
        self._resolved_chat_ids: dict[str, str] = {}

    async def send_message(self, message: str | MessageData, chat_id: ChatIds | None = None) -> None:
        """
        Send a text message to one chat.

        Raises:
            ChatNotFoundError, BotBlockedError, RateLimitError, TelegramNotificationError
        """
        data = message if isinstance(message, MessageData) else MessageData(text=message)
        await self._send_one(self._message_sender(data), chat_id, bulk_method="send_message_bulk")

    async def send_photo(
        self,
        photo: FileSource | PhotoData,
        caption: str | None = None,
        chat_id: ChatIds | None = None,
    ) -> None:
        """
        Send a photo to one chat. `caption` is ignored if `photo` is PhotoData.

        Raises:
            ChatNotFoundError, BotBlockedError, RateLimitError, TelegramNotificationError
        """
        data = photo if isinstance(photo, PhotoData) else PhotoData(photo=photo, caption=caption)
        await self._send_one(self._photo_sender(data), chat_id, bulk_method="send_photo_bulk")

    async def send_document(
        self,
        document: FileSource | DocumentData,
        caption: str | None = None,
        chat_id: ChatIds | None = None,
    ) -> None:
        """
        Send a document to one chat. `caption` is ignored if `document` is DocumentData.

        Raises:
            ChatNotFoundError, BotBlockedError, RateLimitError, TelegramNotificationError
        """
        data = document if isinstance(document, DocumentData) else DocumentData(document=document, caption=caption)
        await self._send_one(self._document_sender(data), chat_id, bulk_method="send_document_bulk")

    async def send_message_bulk(
        self,
        message: str | MessageData,
        chat_ids: Sequence[ChatId] | None = None,
        fail_silently: bool = True,
        max_concurrent: int = 10,
    ) -> BulkSendResult:
        """
        Send a text message to several chats concurrently.

        Args:
            message: Message text or MessageData instance
            chat_ids: Target chats, the configured chats if None
            fail_silently: Record failures in the result. If False, the first failure is raised
                and the remaining sends are cancelled.
            max_concurrent: Maximum number of sends in flight
        """
        data = message if isinstance(message, MessageData) else MessageData(text=message)
        return await self._send_many(self._message_sender(data), chat_ids, fail_silently, max_concurrent)

    async def send_photo_bulk(
        self,
        photo: FileSource | PhotoData,
        caption: str | None = None,
        chat_ids: Sequence[ChatId] | None = None,
        fail_silently: bool = True,
        max_concurrent: int = 10,
    ) -> BulkSendResult:
        """Send a photo to several chats concurrently. See send_message_bulk for the arguments."""
        data = photo if isinstance(photo, PhotoData) else PhotoData(photo=photo, caption=caption)
        return await self._send_many(self._photo_sender(data), chat_ids, fail_silently, max_concurrent)

    async def send_document_bulk(
        self,
        document: FileSource | DocumentData,
        caption: str | None = None,
        chat_ids: Sequence[ChatId] | None = None,
        fail_silently: bool = True,
        max_concurrent: int = 10,
    ) -> BulkSendResult:
        """Send a document to several chats concurrently. See send_message_bulk for the arguments."""
        data = document if isinstance(document, DocumentData) else DocumentData(document=document, caption=caption)
        return await self._send_many(self._document_sender(data), chat_ids, fail_silently, max_concurrent)

    async def close(self) -> None:
        """Close the bot session."""
        await self.bot.session.close()

    async def __aenter__(self) -> "TelegramNotificationBot":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def _message_sender(self, data: MessageData) -> _Sender:
        return partial(self.bot.send_message, text=data.text, **self._options(data))

    def _photo_sender(self, data: PhotoData) -> _Sender:
        return partial(self.bot.send_photo, photo=_input_file(data.photo), caption=data.caption, **self._options(data))

    def _document_sender(self, data: DocumentData) -> _Sender:
        return partial(
            self.bot.send_document, document=_input_file(data.document), caption=data.caption, **self._options(data)
        )

    def _options(self, data: MessageData | PhotoData | DocumentData) -> dict[str, Any]:
        """Per-message options, falling back to the config for the ones left as None."""
        return {
            "parse_mode": _or_default(data.parse_mode, self.config.parse_mode),
            "disable_notification": _or_default(data.disable_notification, self.config.disable_notification),
            "protect_content": _or_default(data.protect_content, self.config.protect_content),
        }

    async def _send_one(self, sender: _Sender, chat_id: ChatIds | None, bulk_method: str) -> None:
        targets = self._target_chat_ids(chat_id)
        if len(targets) > 1:
            raise ValueError(f"Use {bulk_method} for multiple chats")
        await self._deliver(sender, targets[0])

    async def _send_many(
        self,
        sender: _Sender,
        chat_ids: Sequence[ChatId] | None,
        fail_silently: bool,
        max_concurrent: int,
    ) -> BulkSendResult:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        targets = chat_ids if chat_ids is not None else self._target_chat_ids(None)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_to(chat_id: ChatId) -> SendResult:
            async with semaphore:
                try:
                    await self._deliver(sender, chat_id)
                except TelegramNotificationError as e:
                    if not fail_silently:
                        raise
                    return SendResult(chat_id=str(chat_id), success=False, error=str(e), exception=e)
            return SendResult(chat_id=str(chat_id), success=True)

        tasks = [asyncio.ensure_future(send_to(chat_id)) for chat_id in targets]
        try:
            results = await asyncio.gather(*tasks)
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        successful = sum(result.success for result in results)
        return BulkSendResult(
            results=results,
            total_chats=len(results),
            successful_chats=successful,
            failed_chats=len(results) - successful,
        )

    async def _deliver(self, sender: _Sender, chat_id: ChatId) -> None:
        """Send to one chat, translating aiogram errors into library exceptions."""
        resolved = await self._resolve_chat_id(chat_id)
        try:
            await sender(chat_id=resolved)
        except TelegramAPIError as e:
            raise _translate_error(e, chat_id) from e

    def _target_chat_ids(self, chat_id: ChatIds | None) -> list[ChatId]:
        target = chat_id if chat_id is not None else self.config.chat_id
        if target is None or target == []:
            raise ValueError("No chat IDs specified")
        return target if isinstance(target, list) else [target]

    async def _resolve_chat_id(self, chat_id: ChatId) -> ChatId:
        """
        Return the chat ID to send to.

        Integers and strings such as "@channel" or "-100123" are used as given. A string of digits
        is looked up with getChat as is, then with the "-" and "-100" prefixes. The result is cached.
        """
        if isinstance(chat_id, int):
            return chat_id
        text = chat_id.strip()
        if not text:
            raise InvalidChatIdError(chat_id)
        if not text.isdigit():
            return text
        if text in self._resolved_chat_ids:
            return self._resolved_chat_ids[text]

        for prefix in _CHAT_ID_PREFIXES:
            candidate = prefix + text
            try:
                await self.bot.get_chat(candidate)
            except TelegramBadRequest:
                continue
            except TelegramAPIError as e:
                raise _translate_error(e, chat_id) from e
            self._resolved_chat_ids[text] = candidate
            return candidate
        raise ChatNotFoundError(text)


def _or_default(value: T | None, default: T) -> T:
    return default if value is None else value


def _chat_ids_from_env() -> ChatIds | None:
    for name in _CHAT_ID_ENV_VARS:
        chat_ids: list[ChatId] = [part.strip() for part in os.getenv(name, "").split(",") if part.strip()]
        if chat_ids:
            return chat_ids[0] if len(chat_ids) == 1 else chat_ids
    return None


def _input_file(source: Any) -> InputFile:
    """Wrap a path, an http(s) URL or a binary file-like object for aiogram."""
    if hasattr(source, "read"):
        data = source.read()
        if not isinstance(data, bytes):
            raise TypeError("File-like objects must be opened in binary mode")
        name = getattr(source, "name", None)
        filename = Path(name).name if isinstance(name, str) and name else "file"
        return BufferedInputFile(data, filename=filename)

    if isinstance(source, str) and source.startswith(("http://", "https://")):
        return URLInputFile(source)

    if not isinstance(source, (str, Path)):
        raise TypeError(f"Unsupported file source: {type(source).__name__}")
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    return FSInputFile(path)


def _translate_error(error: TelegramAPIError, chat_id: ChatId) -> TelegramNotificationError:
    chat = str(chat_id)
    if isinstance(error, TelegramForbiddenError):
        return BotBlockedError(chat)
    if isinstance(error, TelegramRetryAfter):
        return RateLimitError(error.retry_after, chat)
    if isinstance(error, TelegramBadRequest):
        if "chat not found" in error.message.lower():
            return ChatNotFoundError(chat)
        return TelegramNotificationError(f"Bad request: {error}", chat)
    return TelegramNotificationError(f"Telegram API error: {error}", chat)
