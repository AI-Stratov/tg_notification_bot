# Usage

This page describes the behavior of tg-notification-bot 1.0.0 in detail. The [README](../README.md) has the short version.

- [Creating a bot](#creating-a-bot)
- [Chat IDs](#chat-ids)
- [Sending to one chat](#sending-to-one-chat)
- [Sending to several chats](#sending-to-several-chats)
- [Files](#files)
- [Errors](#errors)
- [Public API](#public-api)

## Creating a bot

Pass a token and chat ID(s), or a `NotificationConfig`:

```python
from tg_notification_bot import NotificationConfig, TelegramNotificationBot

bot = TelegramNotificationBot("123456:ABC...", -1001234567890)
bot = TelegramNotificationBot("123456:ABC...", [-1001234567890, "@my_channel"])

config = NotificationConfig(
    token="123456:ABC...",
    chat_id=[-1001234567890, "@my_channel"],
    parse_mode="MarkdownV2",
    disable_notification=True,
)
bot = TelegramNotificationBot(config)
```

`NotificationConfig` fields:

| Field | Type | Default | Notes |
|---|---|---|---|
| `token` | `str` | required | Must contain exactly one `:`. No other format check. |
| `chat_id` | `int`, `str`, list of them, or `None` | `None` | Default target(s). Strings must not be empty, lists must not be empty. |
| `parse_mode` | `"HTML"`, `"Markdown"`, `"MarkdownV2"` | `"HTML"` | Used when a message does not set its own. |
| `disable_notification` | `bool` | `False` | Send silently. |
| `protect_content` | `bool` | `False` | Disallow forwarding and saving. |

Unknown fields are rejected. Assignments after creation are validated too.

### Chat IDs from the environment

When the bot is created with a token string and no `chat_id`, it reads `TG_CHAT_ID`, then `TG_CHAT_IDS`. Both take one ID or a comma-separated list:

```bash
export TG_CHAT_ID="-1001234567890,@my_channel"
```

```python
bot = TelegramNotificationBot(token)  # chat IDs come from TG_CHAT_ID
```

If neither variable is set, the constructor raises `ValueError`. The token is never read from the environment, and the variables are ignored when you pass a `NotificationConfig`.

### Closing the session

The bot owns an aiohttp session. Close it with `async with` or `await bot.close()`:

```python
async with TelegramNotificationBot(token, chat_id) as bot:
    await bot.send_message("Done")
```

## Chat IDs

Chat IDs can be integers or strings. They are handled differently:

- **Integers** are sent as is. No extra requests.
- **Strings starting with `-`** are checked with one `getChat` request. If Telegram answers with a bad request, `ChatNotFoundError` is raised.
- **Other strings** (`"@my_channel"`, `"4274151810"`) are tried with `getChat` as given, then with a `-` prefix, then with a `-100` prefix. The first one that works is used. If none works, `ChatNotFoundError` is raised.

So every send to a string ID costs one to three `getChat` requests. Use integer IDs when you know the full ID.

The prefix search exists because Telegram clients often show IDs without the prefix. In Telegram Desktop, enable Settings > Advanced > Experimental settings > "Show Peer IDs in Profile". The chat profile then shows an ID such as `4 274 151 810`. Pass it as the string `"4274151810"` and the library finds the right prefix. Passed as an integer it would be sent as is and fail.

To post in a channel, the bot must be an administrator with permission to post. In a group, being a member is enough unless the group restricts sending.

## Sending to one chat

```python
await bot.send_message("text", chat_id=None)
await bot.send_photo(photo, caption=None, chat_id=None)
await bot.send_document(document, caption=None, chat_id=None)
```

- `chat_id` overrides the configured chat. If the target resolves to more than one chat, `ValueError` is raised; use the bulk methods instead.
- The methods return `None`. The sent `Message` is not returned.
- Errors are raised as library exceptions (see [Errors](#errors)).

### Message options

Instead of plain text you can pass `MessageData`, `PhotoData` or `DocumentData`:

```python
from tg_notification_bot import DocumentData, MessageData, PhotoData

await bot.send_message(MessageData(text="*Done*", parse_mode="MarkdownV2", disable_notification=True))
await bot.send_photo(PhotoData(photo="chart.png", caption="Daily chart"))
await bot.send_document(DocumentData(document="report.pdf", caption="Report", protect_content=True))
```

- `MessageData.text` is stripped of surrounding whitespace and must be 1 to 4096 characters.
- `PhotoData.caption` and `DocumentData.caption` are limited to 1024 characters.
- When you pass `PhotoData` or `DocumentData`, the `caption` argument of the method is ignored.
- `parse_mode` falls back to the config. A message is always sent with a parse mode, so with the default HTML mode, text containing `<`, `>` or `&` must be escaped (for example with `html.escape`).
- `disable_notification` and `protect_content` are combined with the config using `or`. A message can turn them on, but a `False` on the message does not override `True` in the config.

## Sending to several chats

```python
result = await bot.send_message_bulk("text", chat_ids=None, fail_silently=True, max_concurrent=10)
result = await bot.send_photo_bulk(photo, caption=None, chat_ids=None, fail_silently=True, max_concurrent=10)
result = await bot.send_document_bulk(document, caption=None, chat_ids=None, fail_silently=True, max_concurrent=10)
```

- `chat_ids` defaults to the configured chat(s). If neither is set, `ValueError` is raised.
- Sends run concurrently, at most `max_concurrent` at a time. This limits parallel requests, not requests per second.
- A file is prepared once and reused for every chat.
- A failure for one chat does not stop the others. It is recorded in the result.

`BulkSendResult`:

| Attribute | Meaning |
|---|---|
| `results` | List of `SendResult`, one per chat, in the order of `chat_ids` |
| `total_chats`, `successful_chats`, `failed_chats` | Counts |
| `success_rate` | Percentage from 0 to 100 |
| `successful_chat_ids`, `failed_chat_ids` | Chat IDs as strings |

`SendResult` has `chat_id` (the ID you passed, as a string), `success`, `error` (the exception text) and `exception`.

Unlike the single-chat methods, bulk methods do not translate Telegram errors. `SendResult.exception` holds the original aiogram exception, for example `TelegramForbiddenError` or `TelegramRetryAfter`. The exception is a `ChatNotFoundError` when string chat ID resolution failed.

`fail_silently=False` re-raises only `ChatNotFoundError` from chat ID resolution. All other errors are still collected in the result. Sends to other chats that are already running are not cancelled.

## Files

`send_photo`, `send_document` and their bulk versions accept:

- a local path as `str` or `pathlib.Path`. A missing file raises `FileNotFoundError` before any request is made;
- a `str` starting with `http://` or `https://`. aiogram downloads the file and uploads it to Telegram;
- a file-like object with `read()`. It is read into memory once. The file name comes from its `name` attribute, or `"file"` if there is none.

Telegram `file_id` strings are not supported: a string that is not a URL is treated as a path.

## Errors

All library exceptions inherit from `TelegramNotificationError`, which has `message` and `chat_id` attributes.

| Exception | When |
|---|---|
| `BotBlockedError` | Telegram returned 403 Forbidden (bot blocked by the user, removed from the chat, no rights) |
| `ChatNotFoundError` | Telegram returned "chat not found", or a string chat ID could not be resolved |
| `RateLimitError` | Telegram returned 429. `retry_after` holds the wait time in seconds |
| `InvalidChatIdError` | A chat ID override is an empty or whitespace-only string |
| `TelegramNotificationError` | Any other error during the send. The text starts with `Bad request:` or `Unexpected error:` |

This mapping applies to the single-chat methods. Some errors are raised as they are:

- `ValueError` for configuration problems, a missing chat ID, or several chats passed to a single-chat method. pydantic's `ValidationError` (a `ValueError` subclass) for invalid `NotificationConfig`, `MessageData`, `PhotoData` or `DocumentData`.
- `FileNotFoundError` for a missing local file.
- Errors other than "bad request" from the `getChat` lookup of a string chat ID, such as network errors.

The library does not retry. To retry on rate limits:

```python
try:
    await bot.send_message(text)
except RateLimitError as e:
    await asyncio.sleep(e.retry_after)
    await bot.send_message(text)
```

## Public API

Everything below is importable from `tg_notification_bot`:

- `TelegramNotificationBot`: `send_message`, `send_photo`, `send_document`, `send_message_bulk`, `send_photo_bulk`, `send_document_bulk`, `close`, async context manager. The `config` (`NotificationConfig`) and `bot` (`aiogram.Bot`) attributes are public.
- Models: `NotificationConfig`, `MessageData`, `PhotoData`, `DocumentData`, `SendResult`, `BulkSendResult`.
- Exceptions: `TelegramNotificationError`, `ChatNotFoundError`, `BotBlockedError`, `RateLimitError`, `InvalidChatIdError`.

A complete script is in [examples/multi_chat_example.py](../examples/multi_chat_example.py).
