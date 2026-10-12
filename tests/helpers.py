"""Constants and factories shared by the tests."""

from typing import Any

from aiogram.exceptions import TelegramAPIError
from aiogram.methods import GetMe

TOKEN = "123456:ABC-DEF"
CHAT_ID = 42


def api_error(error_class: type[TelegramAPIError], message: str, **kwargs: Any) -> TelegramAPIError:
    """Build an aiogram API error the way aiogram raises it."""
    method: Any = GetMe()  # aiogram annotates `method` with an unbound TypeVar
    return error_class(method=method, message=message, **kwargs)
