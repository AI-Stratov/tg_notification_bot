"""Tests for multi-chat functionality."""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, patch

from tg_notification_bot import (
    TelegramNotificationBot,
    NotificationConfig,
    BulkSendResult,
    SendResult,
    MessageData,
)


class TestMultiChatBot:
    """Test multi-chat functionality."""

    @pytest.fixture
    def multi_chat_config(self):
        """Create a NotificationConfig with multiple chat IDs."""
        return NotificationConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", chat_id=["123456789", "987654321", "@testchannel"])

    @pytest.fixture
    def single_chat_config(self):
        """Create a NotificationConfig with single chat ID."""
        return NotificationConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", chat_id="123456789")

    def test_config_with_multiple_chat_ids(self, multi_chat_config):
        """Test creating config with multiple chat IDs."""
        assert multi_chat_config.chat_id == ["123456789", "987654321", "@testchannel"]

    def test_config_with_single_chat_id(self, single_chat_config):
        """Test creating config with single chat ID."""
        assert single_chat_config.chat_id == "123456789"

    def test_config_validation_empty_list(self):
        """Test validation fails for empty chat ID list."""
        with pytest.raises(ValueError, match="Chat ID list cannot be empty"):
            NotificationConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", chat_id=[])

    def test_config_validation_empty_string_in_list(self):
        """Test validation fails for empty string in chat ID list."""
        with pytest.raises(ValueError, match="Chat ID cannot be empty string"):
            NotificationConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", chat_id=["123456789", "", "987654321"])

    @patch.dict(os.environ, {"TG_CHAT_ID": "123456789,987654321,@testchannel"})
    def test_load_multiple_chat_ids_from_env(self):
        """Test loading multiple chat IDs from TG_CHAT_ID environment variable."""
        bot = TelegramNotificationBot("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        assert bot.config.chat_id == ["123456789", "987654321", "@testchannel"]

    @patch.dict(os.environ, {"TG_CHAT_ID": "123456789"})
    def test_load_single_chat_id_from_env(self):
        """Test loading single chat ID from TG_CHAT_ID environment variable."""
        bot = TelegramNotificationBot("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        assert bot.config.chat_id == "123456789"

    @patch.dict(os.environ, {"TG_CHAT_IDS": "123456789,987654321"})
    def test_load_chat_ids_from_alternative_env(self):
        """Test loading chat IDs from TG_CHAT_IDS environment variable."""
        bot = TelegramNotificationBot("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        assert bot.config.chat_id == ["123456789", "987654321"]

    @patch.dict(os.environ, {}, clear=True)
    def test_no_chat_id_provided(self):
        """Test error when no chat ID is provided."""
        with pytest.raises(ValueError, match="chat_id is required"):
            TelegramNotificationBot("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")

    def test_get_target_chat_ids_multiple(self, multi_chat_config):
        """Test getting multiple target chat IDs."""
        bot = TelegramNotificationBot(multi_chat_config)
        chat_ids = bot._get_target_chat_ids(None)
        assert chat_ids == ["123456789", "987654321", "@testchannel"]

    def test_get_target_chat_ids_single(self, single_chat_config):
        """Test getting single target chat ID."""
        bot = TelegramNotificationBot(single_chat_config)
        chat_ids = bot._get_target_chat_ids(None)
        assert chat_ids == ["123456789"]

    def test_get_target_chat_ids_override(self, multi_chat_config):
        """Test overriding target chat IDs."""
        bot = TelegramNotificationBot(multi_chat_config)
        chat_ids = bot._get_target_chat_ids(["111111111", "222222222"])
        assert chat_ids == ["111111111", "222222222"]

    def test_get_target_chat_ids_no_config(self):
        """Test error when no chat IDs are available."""
        config = NotificationConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", chat_id=None)
        bot = TelegramNotificationBot(config)
        with pytest.raises(ValueError, match="No chat IDs specified"):
            bot._get_target_chat_ids(None)

    @pytest.mark.asyncio
    async def test_send_message_bulk_success(self, multi_chat_config):
        """Test successful bulk message sending."""
        bot = TelegramNotificationBot(multi_chat_config)

        with patch.object(bot.bot, "send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(bot, "_normalize_chat_id", new_callable=AsyncMock) as mock_normalize:
                mock_normalize.side_effect = lambda x: str(x)

                result = await bot.send_message_bulk("Test message")

                assert result.total_chats == 3
                assert result.successful_chats == 3
                assert result.failed_chats == 0
                assert result.success_rate == 100.0
                assert len(result.successful_chat_ids) == 3
                assert len(result.failed_chat_ids) == 0

                assert mock_send.call_count == 3

    @pytest.mark.asyncio
    async def test_send_message_bulk_partial_failure(self, multi_chat_config):
        """Test bulk message sending with partial failures."""
        bot = TelegramNotificationBot(multi_chat_config)

        def mock_send_side_effect(chat_id, **kwargs):
            if chat_id == "987654321":
                raise Exception("Test error")
            return AsyncMock()

        with patch.object(bot.bot, "send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(bot, "_normalize_chat_id", new_callable=AsyncMock) as mock_normalize:
                mock_normalize.side_effect = lambda x: str(x)
                mock_send.side_effect = mock_send_side_effect

                result = await bot.send_message_bulk("Test message", fail_silently=True)

                assert result.total_chats == 3
                assert result.successful_chats == 2
                assert result.failed_chats == 1
                assert result.success_rate == pytest.approx(66.67, rel=1e-2)
                assert len(result.successful_chat_ids) == 2
                assert len(result.failed_chat_ids) == 1
                assert "987654321" in result.failed_chat_ids

    @pytest.mark.asyncio
    async def test_send_message_single_chat_with_multiple_config(self, multi_chat_config):
        """Test error when trying to send to single chat with multiple chat IDs in config."""
        bot = TelegramNotificationBot(multi_chat_config)

        with pytest.raises(ValueError, match="Use send_message_bulk for multiple chats"):
            await bot.send_message("Test message")

    @pytest.mark.asyncio
    async def test_send_message_single_chat_override(self, multi_chat_config):
        """Test sending to single chat by overriding chat_id."""
        bot = TelegramNotificationBot(multi_chat_config)

        with patch.object(bot.bot, "send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(bot, "_normalize_chat_id", new_callable=AsyncMock) as mock_normalize:
                mock_normalize.return_value = "123456789"

                await bot.send_message("Test message", chat_id="123456789")

                mock_send.assert_called_once()
                mock_normalize.assert_called_once_with("123456789")

    @pytest.mark.asyncio
    async def test_send_photo_bulk(self, multi_chat_config):
        """Test bulk photo sending."""
        bot = TelegramNotificationBot(multi_chat_config)

        with patch.object(bot.bot, "send_photo", new_callable=AsyncMock) as mock_send:
            with patch.object(bot, "_normalize_chat_id", new_callable=AsyncMock) as mock_normalize:
                with patch.object(bot, "_prepare_file_input") as mock_prepare:
                    mock_normalize.side_effect = lambda x: str(x)
                    mock_prepare.return_value = "mock_file"

                    result = await bot.send_photo_bulk("test.jpg", caption="Test photo")

                    assert result.total_chats == 3
                    assert result.successful_chats == 3
                    assert mock_send.call_count == 3

    @pytest.mark.asyncio
    async def test_send_document_bulk(self, multi_chat_config):
        """Test bulk document sending."""
        bot = TelegramNotificationBot(multi_chat_config)

        with patch.object(bot.bot, "send_document", new_callable=AsyncMock) as mock_send:
            with patch.object(bot, "_normalize_chat_id", new_callable=AsyncMock) as mock_normalize:
                with patch.object(bot, "_prepare_file_input") as mock_prepare:
                    mock_normalize.side_effect = lambda x: str(x)
                    mock_prepare.return_value = "mock_file"

                    result = await bot.send_document_bulk("test.pdf", caption="Test document")

                    assert result.total_chats == 3
                    assert result.successful_chats == 3
                    assert mock_send.call_count == 3

    def test_bulk_send_result_properties(self):
        """Test BulkSendResult properties."""
        results = [
            SendResult(chat_id="123", success=True),
            SendResult(chat_id="456", success=False, error="Test error"),
            SendResult(chat_id="789", success=True),
        ]

        bulk_result = BulkSendResult(results=results, total_chats=3, successful_chats=2, failed_chats=1)

        assert bulk_result.success_rate == pytest.approx(66.67, rel=1e-2)
        assert bulk_result.successful_chat_ids == ["123", "789"]
        assert bulk_result.failed_chat_ids == ["456"]

    @pytest.mark.asyncio
    async def test_concurrent_limit(self, multi_chat_config):
        """Test that concurrent sending respects max_concurrent limit."""
        # Create a config with many chat IDs
        many_chats_config = NotificationConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", chat_id=[f"chat_{i}" for i in range(20)])
        bot = TelegramNotificationBot(many_chats_config)

        call_times = []

        async def mock_send_with_timing(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate network delay

        with patch.object(bot.bot, "send_message", new_callable=AsyncMock) as mock_send:
            with patch.object(bot, "_normalize_chat_id", new_callable=AsyncMock) as mock_normalize:
                mock_normalize.side_effect = lambda x: str(x)
                mock_send.side_effect = mock_send_with_timing

                result = await bot.send_message_bulk("Test message", max_concurrent=5)

                assert result.total_chats == 20
                assert result.successful_chats == 20
                assert mock_send.call_count == 20

                # Check that not all calls started at the same time (due to semaphore)
                first_batch_end = min(call_times) + 0.05
                concurrent_calls = sum(1 for t in call_times if t <= first_batch_end)
                assert concurrent_calls <= 5  # Should not exceed max_concurrent
