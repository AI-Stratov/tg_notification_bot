"""Legacy tests updated for new bot architecture."""

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_send_message(mock_aiogram_bot: AsyncMock) -> None:
    """Test sending message with mock bot."""
    message = "Test message"
    await mock_aiogram_bot.send_message(chat_id="-123456789", text=message)
    mock_aiogram_bot.send_message.assert_called_once_with(
        chat_id="-123456789", text=message
    )


@pytest.mark.asyncio
async def test_send_photo(mock_aiogram_bot: AsyncMock) -> None:
    """Test sending photo with mock bot."""
    photo_bytes = b"test_photo_bytes"
    caption = "Test photo"
    await mock_aiogram_bot.send_photo(photo=photo_bytes, caption=caption)
    mock_aiogram_bot.send_photo.assert_called_once_with(
        photo=photo_bytes, caption=caption
    )


@pytest.mark.asyncio
async def test_send_document(mock_aiogram_bot: AsyncMock) -> None:
    """Test sending document with mock bot."""
    document_bytes = b"test_document_bytes"
    caption = "Test document"
    await mock_aiogram_bot.send_document(document=document_bytes, caption=caption)
    mock_aiogram_bot.send_document.assert_called_once_with(
        document=document_bytes, caption=caption
    )
