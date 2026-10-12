# Usage

This page describes the behavior of tg-notification-bot in detail. Changes between releases are listed in the [changelog](../CHANGELOG.md). The [README](../README.md) has the short version.

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

Empty entries are skipped. If neither variable has a value, the constructor raises `ValueError`. The token is never read from the environment, and the variables are ignored when you pass a `NotificationConfig`.

### Closing the session

The bot owns an aiohttp session. Close it with `async with` or `await bot.close()`:

```python
async with TelegramNotificationBot(token, chat_id) as bot:
    await bot.send_message("Done")
```

## Chat IDs

Chat IDs can be integers or strings:

- **Integers** are sent as is.
- **Strings** are stripped of surrounding whitespace. `"@my_channel"`, `"-1001234567890"` and any other string that is not made of digits only are sent as is.
- **Strings made of digits only** (`"4274151810"`) are looked up with `getChat`: first as given, then with a `-` prefix, then with a `-100` prefix. The first one that works is used and remembered for the lifetime of the bot object, so the lookup costs one to three requests once per chat. If none works, `ChatNotFoundError` is raised.
- **Empty or blank strings** passed as a `chat_id` override raise `InvalidChatIdError`.

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
- `parse_mode`, `disable_notification` and `protect_content` left as `None` fall back to the config. Any other value, including `False`, wins over the config.

## Sending to several chats

```python
result = await bot.send_message_bulk("text", chat_ids=None, fail_silently=True, max_concurrent=10)
result = await bot.send_photo_bulk(photo, caption=None, chat_ids=None, fail_silently=True, max_concurrent=10)
result = await bot.send_document_bulk(document, caption=None, chat_ids=None, fail_silently=True, max_concurrent=10)
```

- `chat_ids` is any sequence of chat IDs and defaults to the configured chat(s). If neither is set, `ValueError` is raised. An empty sequence returns an empty result.
- Sends run concurrently, at most `max_concurrent` at a time. This limits parallel requests, not requests per second. `max_concurrent` must be at least 1.
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

`SendResult.exception` holds the same library exception a single-chat method would raise (see [Errors](#errors)). The original aiogram exception is its `__cause__`.

With `fail_silently=False`, the first failure is raised instead of collected, and the sends that have not finished yet are cancelled.

Errors that do not come from Telegram, such as a bug in your code or a `TypeError` for an unsupported file, are never collected. They propagate and cancel the remaining sends.

## Files

`send_photo`, `send_document` and their bulk versions accept:

- a local path as `str` or `pathlib.Path`. A missing file raises `FileNotFoundError` before any request is made;
- a `str` starting with `http://` or `https://`. aiogram downloads the file and uploads it to Telegram;
- a binary file-like object with `read()`. It is read into memory once. The file name comes from its `name` attribute, or `"file"` if there is none. A text-mode file raises `TypeError`.

A path that is a directory raises `FileNotFoundError`. Any other type raises `TypeError`. Telegram `file_id` strings are not supported: a string that is not a URL is treated as a path.

## Errors

All library exceptions inherit from `TelegramNotificationError`, which has `message` and `chat_id` attributes. Errors returned by Telegram are translated as follows, both by the single-chat methods and in bulk results. The original aiogram exception is kept as `__cause__`.

| aiogram error | Library exception |
|---|---|
| `TelegramForbiddenError` (bot blocked by the user, removed from the chat, no rights) | `BotBlockedError` |
| `TelegramBadRequest` with "chat not found" | `ChatNotFoundError` |
| other `TelegramBadRequest` | `TelegramNotificationError`, text starts with `Bad request:` |
| `TelegramRetryAfter` (HTTP 429) | `RateLimitError`, `retry_after` holds the wait time in seconds |
| any other `TelegramAPIError`, including `TelegramNetworkError` | `TelegramNotificationError`, text starts with `Telegram API error:` |

The same translation applies to the `getChat` lookups of digit-only chat IDs. `ChatNotFoundError` is also raised when that lookup finds nothing, and `InvalidChatIdError` for a blank chat ID.

Other errors are raised as they are:

- `ValueError` for configuration problems, a missing chat ID, several chats passed to a single-chat method, or `max_concurrent` below 1. pydantic's `ValidationError` (a `ValueError` subclass) for invalid `NotificationConfig`, `MessageData`, `PhotoData` or `DocumentData`.
- `FileNotFoundError` for a missing local file, `TypeError` for an unsupported file source.
- Anything that does not come from aiogram is not wrapped.

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

The package ships a `py.typed` marker, so type checkers use its annotations.
- Models: `NotificationConfig`, `MessageData`, `PhotoData`, `DocumentData`, `SendResult`, `BulkSendResult`.
- Exceptions: `TelegramNotificationError`, `ChatNotFoundError`, `BotBlockedError`, `RateLimitError`, `InvalidChatIdError`.

A complete script is in [examples/multi_chat_example.py](../examples/multi_chat_example.py).
