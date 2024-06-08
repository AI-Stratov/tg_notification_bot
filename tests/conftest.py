from unittest.mock import AsyncMock, patch

import pytest

from tg_notification_bot import TgNotificationBot


@pytest.fixture(scope="session")
def mock_bot():
    with patch("aiogram.Bot") as mock_bot_class:
        mock_bot_instance = mock_bot_class.return_value
        mock_bot_instance.send_message = AsyncMock()
        mock_bot_instance.send_photo = AsyncMock()
        mock_bot_instance.send_document = AsyncMock()

        TgNotificationBot(token="123456:ABCDEF1234ghIkl", chat_id="-123456789")
        yield mock_bot_instance
