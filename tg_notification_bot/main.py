import logging
from typing import Union

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)


class TgNotificationBot:
    def __init__(self, token: str, chat_id: Union[int, str]):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)

    async def send_message(self, message: str, parse_mode: str = "HTML"):
        chat_id = await self._normalize_chat_id(self.chat_id)
        try:
            await self.bot.send_message(
                chat_id=chat_id, text=message, parse_mode=parse_mode
            )
        except TelegramForbiddenError:
            self.logger.warning(
                f"Бот заблокирован пользователем или не имеет доступа к чату с ID {self.chat_id}"
            )
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                self.logger.warning(f"Чат с ID {self.chat_id} не найден")
            else:
                self.logger.error(f"Ошибка запроса Telegram: {e}")
        except TelegramRetryAfter as e:
            self.logger.warning(
                f"Превышено ограничение на отправку сообщений. Повторите через {e.retry_after} секунд"
            )
        except Exception as e:
            self.logger.error(
                f"Ошибка при отправке сообщения в чат {self.chat_id}: {e}"
            )

    async def send_photo(self, photo, caption=None):
        chat_id = await self._normalize_chat_id(self.chat_id)
        try:
            await self.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
        except TelegramForbiddenError:
            self.logger.warning(
                f"Бот заблокирован пользователем или не имеет доступа к чату с ID {self.chat_id}"
            )
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                self.logger.warning(f"Чат с ID {self.chat_id} не найден")
            else:
                self.logger.error(f"Ошибка запроса Telegram: {e}")
        except TelegramRetryAfter as e:
            self.logger.warning(
                f"Превышено ограничение на отправку сообщений. Повторите через {e.retry_after} секунд"
            )
        except Exception as e:
            self.logger.error(f"Ошибка при отправке фото в чат {self.chat_id}: {e}")

    async def send_document(self, document, caption=None):
        chat_id = await self._normalize_chat_id(self.chat_id)
        try:
            await self.bot.send_document(
                chat_id=chat_id, document=document, caption=caption
            )
        except TelegramForbiddenError:
            self.logger.warning(
                f"Бот заблокирован пользователем или не имеет доступа к чату с ID {self.chat_id}"
            )
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                self.logger.warning(f"Чат с ID {self.chat_id} не найден")
            else:
                self.logger.error(f"Ошибка запроса Telegram: {e}")
        except TelegramRetryAfter as e:
            self.logger.warning(
                f"Превышено ограничение на отправку сообщений. Повторите через {e.retry_after} секунд"
            )
        except Exception as e:
            self.logger.error(
                f"Ошибка при отправке документа в чат {self.chat_id}: {e}"
            )

    async def _normalize_chat_id(self, chat_id: Union[int, str]) -> str:
        if isinstance(chat_id, int):
            return str(chat_id)
        if chat_id.startswith("-100") or chat_id.startswith("-"):
            return chat_id
        try:
            await self.bot.get_chat(chat_id)
            return chat_id
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                try:
                    modified_chat_id = "-" + chat_id
                    await self.bot.get_chat(modified_chat_id)
                    return modified_chat_id
                except TelegramBadRequest as e2:
                    if "chat not found" in str(e2).lower():
                        modified_chat_id = "-100" + chat_id
                        try:
                            await self.bot.get_chat(modified_chat_id)
                            return modified_chat_id
                        except Exception as e3:
                            self.logger.error(f"Telegram API error: {e3}")
                            return chat_id
                    else:
                        self.logger.error(f"Telegram API error: {e2}")
                        return chat_id
            else:
                self.logger.error(f"Telegram API error: {e}")
                return chat_id
        except Exception as e:
            self.logger.error(f"Telegram API error: {e}")
            return chat_id
