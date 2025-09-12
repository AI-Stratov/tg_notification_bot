"""
Example demonstrating multi-chat functionality of tg-notification-bot.

This example shows various ways to send messages to multiple chats:
1. Using environment variables
2. Programmatic configuration
3. Bulk operations with error handling
"""

import asyncio
import os
from pathlib import Path

from tg_notification_bot import (
    TelegramNotificationBot,
    NotificationConfig,
    BulkSendResult,
    ChatNotFoundError,
    BotBlockedError,
)


async def example_env_variables():
    """Example using environment variables for multiple chats."""
    print("=== Example 1: Environment Variables ===")

    # Set example environment variables (in real usage, put these in .env file)
    os.environ["TG_BOT_TOKEN"] = "YOUR_BOT_TOKEN"
    os.environ["TG_CHAT_ID"] = "123456789,987654321,@channel_name"

    try:
        # Bot automatically loads chat IDs from environment
        bot = TelegramNotificationBot(os.getenv("TG_BOT_TOKEN"))

        # Send to all configured chats
        result = await bot.send_message_bulk("🌍 Hello to all chats from environment config!")

        print(f"Sent to {result.successful_chats}/{result.total_chats} chats")
        print(f"Success rate: {result.success_rate:.1f}%")

        if result.failed_chats > 0:
            print(f"Failed chats: {', '.join(result.failed_chat_ids)}")

        await bot.close()

    except Exception as e:
        print(f"Error in environment example: {e}")


async def example_programmatic_config():
    """Example using programmatic configuration."""
    print("\n=== Example 2: Programmatic Configuration ===")

    try:
        # Configure multiple chats programmatically
        config = NotificationConfig(
            token="YOUR_BOT_TOKEN",
            chat_id=["123456789", "987654321", "@channel_name", "@alerts"],
            parse_mode="Markdown",
            disable_notification=True,
        )

        async with TelegramNotificationBot(config) as bot:
            # Send formatted message to all chats
            result = await bot.send_message_bulk(
                "*🚀 System Update*\n\n• Version: 2.1.0\n• Features: Multi-chat support\n• Status: _Deployed successfully_"
            )

            # Detailed results
            print(f"Total chats: {result.total_chats}")
            print(f"Successful: {result.successful_chats}")
            print(f"Failed: {result.failed_chats}")

            for send_result in result.results:
                status = "✅" if send_result.success else "❌"
                print(f"{status} {send_result.chat_id}")
                if not send_result.success:
                    print(f"   Error: {send_result.error}")

    except Exception as e:
        print(f"Error in programmatic example: {e}")


async def example_bulk_with_custom_chats():
    """Example of bulk operations with custom chat lists."""
    print("\n=== Example 3: Bulk Operations with Custom Chat Lists ===")

    try:
        # Initialize with default chat
        bot = TelegramNotificationBot("YOUR_BOT_TOKEN", "default_chat_id")

        # Define different chat groups
        admin_chats = ["admin1", "admin2", "@admin_channel"]
        user_chats = ["user1", "user2", "user3", "@announcements"]
        emergency_chats = ["ops_team", "@critical_alerts"]

        async with bot:
            # Send admin notification
            admin_result = await bot.send_message_bulk(
                "🔧 Admin: Scheduled maintenance in 1 hour",
                chat_ids=admin_chats,
                fail_silently=True,
                max_concurrent=3,
            )

            # Send user announcement
            user_result = await bot.send_message_bulk(
                "📢 New feature available! Check it out in the app.",
                chat_ids=user_chats,
                max_concurrent=5,
            )

            # Send emergency alert (don't fail silently)
            try:
                emergency_result = await bot.send_message_bulk(
                    "🚨 CRITICAL: Database connection lost!",
                    chat_ids=emergency_chats,
                    fail_silently=False,  # Raise exceptions on failure
                )
                print("Emergency alert sent successfully")
            except (ChatNotFoundError, BotBlockedError) as e:
                print(f"Emergency alert failed: {e}")

            # Report results
            print(f"Admin notifications: {admin_result.successful_chats}/{admin_result.total_chats}")
            print(f"User announcements: {user_result.successful_chats}/{user_result.total_chats}")

    except Exception as e:
        print(f"Error in bulk operations example: {e}")


async def example_bulk_media():
    """Example of sending media to multiple chats."""
    print("\n=== Example 4: Bulk Media Operations ===")

    try:
        config = NotificationConfig(token="YOUR_BOT_TOKEN", chat_id=["tech_team", "qa_team", "@dev_updates"])

        async with TelegramNotificationBot(config) as bot:
            # Send photo to all chats
            photo_result = await bot.send_photo_bulk(
                "https://via.placeholder.com/800x600/0066cc/ffffff?text=Release+Notes",
                caption="📊 Release 2.1.0 Dashboard",
                max_concurrent=3,
            )

            # Send document to all chats
            # Note: In real usage, this would be an actual file path
            doc_result = await bot.send_document_bulk(
                Path("release_notes.pdf"),  # This file would need to exist
                caption="📄 Detailed release notes",
                fail_silently=True,
            )

            print(f"Photo sent to: {photo_result.successful_chats}/{photo_result.total_chats} chats")
            print(f"Document sent to: {doc_result.successful_chats}/{doc_result.total_chats} chats")

            # Show failed deliveries
            if photo_result.failed_chats > 0:
                print(f"Photo delivery failed: {', '.join(photo_result.failed_chat_ids)}")
            if doc_result.failed_chats > 0:
                print(f"Document delivery failed: {', '.join(doc_result.failed_chat_ids)}")

    except Exception as e:
        print(f"Error in media example: {e}")


async def example_error_handling():
    """Example demonstrating error handling in bulk operations."""
    print("\n=== Example 5: Error Handling ===")

    try:
        # Mix of valid and invalid chat IDs for demonstration
        mixed_chats = ["123456789", "invalid_chat", "@nonexistent_channel", "987654321"]

        bot = TelegramNotificationBot("YOUR_BOT_TOKEN", mixed_chats)

        async with bot:
            result = await bot.send_message_bulk(
                "Testing error handling",
                fail_silently=True,  # Continue even if some chats fail
            )

            print(f"Results summary:")
            print(f"  Total attempts: {result.total_chats}")
            print(f"  Successful: {result.successful_chats}")
            print(f"  Failed: {result.failed_chats}")
            print(f"  Success rate: {result.success_rate:.1f}%")

            print(f"\nDetailed results:")
            for send_result in result.results:
                if send_result.success:
                    print(f"  ✅ {send_result.chat_id}: Message sent")
                else:
                    print(f"  ❌ {send_result.chat_id}: {send_result.error}")
                    if send_result.exception:
                        print(f"     Exception: {type(send_result.exception).__name__}")

    except Exception as e:
        print(f"Error in error handling example: {e}")


async def main():
    """Run all examples."""
    print("Multi-Chat Telegram Bot Examples")
    print("=" * 40)
    print("Note: These examples use placeholder tokens and chat IDs.")
    print("Replace with your actual bot token and chat IDs to test.\n")

    await example_env_variables()
    await example_programmatic_config()
    await example_bulk_with_custom_chats()
    await example_bulk_media()
    await example_error_handling()

    print("\n" + "=" * 40)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
