"""
Send notifications to several Telegram chats.

Usage:
    export TG_BOT_TOKEN="123456:ABC..."
    export TG_CHAT_ID="-1001234567890,@my_channel"
    python examples/multi_chat_example.py

TG_CHAT_ID is a comma-separated list of chat IDs or @usernames. The library
reads it when the bot is created with a token string and no chat_id.
"""

import asyncio
import io
import os
import sys

from tg_notification_bot import (
    BotBlockedError,
    BulkSendResult,
    ChatNotFoundError,
    DocumentData,
    MessageData,
    RateLimitError,
    TelegramNotificationBot,
    TelegramNotificationError,
)


def print_report(title: str, result: BulkSendResult) -> None:
    print(f"{title}: {result.successful_chats}/{result.total_chats} delivered ({result.success_rate:.0f}%)")
    for send_result in result.results:
        if not send_result.success:
            print(f"  {send_result.chat_id}: {send_result.error}")


async def main() -> None:
    token = os.getenv("TG_BOT_TOKEN")
    if not token or not os.getenv("TG_CHAT_ID"):
        sys.exit("Set TG_BOT_TOKEN and TG_CHAT_ID before running this example.")

    # Chat IDs are loaded from TG_CHAT_ID.
    async with TelegramNotificationBot(token) as bot:
        result = await bot.send_message_bulk("<b>Deploy finished</b>\nservice: api\nversion: 2.3.1")
        print_report("Text message", result)

        # MessageData sets the parse mode and silent delivery for one message.
        silent = MessageData(text="*Nightly backup completed*", parse_mode="MarkdownV2", disable_notification=True)
        result = await bot.send_message_bulk(silent, max_concurrent=2)
        print_report("Silent message", result)

        # File-like objects are read once and sent to every chat.
        report = io.BytesIO(b"service,status\napi,ok\nworker,ok\n")
        report.name = "status.csv"
        result = await bot.send_document_bulk(DocumentData(document=report, caption="Status report"))
        print_report("Document", result)

        # Single-chat methods raise exceptions instead of returning a result.
        first_chat = result.results[0].chat_id
        try:
            await bot.send_message("Single-chat message", chat_id=first_chat)
            print(f"Single message: delivered to {first_chat}")
        except (ChatNotFoundError, BotBlockedError) as e:
            print(f"Single message: {first_chat} is unreachable: {e}")
        except RateLimitError as e:
            print(f"Single message: rate limited, retry after {e.retry_after} s")
        except TelegramNotificationError as e:
            print(f"Single message: failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
