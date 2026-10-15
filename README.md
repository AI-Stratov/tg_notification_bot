# tg-notification-bot

[![CI](https://github.com/AI-Stratov/tg_notification_bot/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-Stratov/tg_notification_bot/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tg-notification-bot.svg)](https://pypi.org/project/tg-notification-bot/)

An async Python library for services, scripts and CI jobs that need to send text, photo and document notifications to one or more Telegram chats through a bot.

## Install

```bash
pip install tg-notification-bot
```

## Example

Create a bot with [@BotFather](https://t.me/BotFather), add it to the target chat, then set `TG_BOT_TOKEN` and `TG_CHAT_ID` (one chat ID or `@channel_username`) and run:

```python
import asyncio
import os

from tg_notification_bot import TelegramNotificationBot


async def main() -> None:
    async with TelegramNotificationBot(os.environ["TG_BOT_TOKEN"], os.environ["TG_CHAT_ID"]) as bot:
        await bot.send_message("<b>Deploy finished</b>: api 2.3.1")


asyncio.run(main())
```

To send to several chats, use the bulk methods. They return a per-chat result instead of raising:

```python
async def notify_all(token: str) -> None:
    async with TelegramNotificationBot(token, [-1001234567890, "@my_channel"]) as bot:
        result = await bot.send_message_bulk("Backup finished")
        print(f"{result.successful_chats}/{result.total_chats} delivered, failed: {result.failed_chat_ids}")
```

A longer script is in [examples/multi_chat_example.py](https://github.com/AI-Stratov/tg_notification_bot/blob/main/examples/multi_chat_example.py). Detailed behavior is described in [docs/usage.md](https://github.com/AI-Stratov/tg_notification_bot/blob/main/docs/usage.md).

## Features

- `send_message`, `send_photo` and `send_document` for one chat. Telegram errors are raised as `BotBlockedError`, `ChatNotFoundError`, `RateLimitError` (with `retry_after`) or `TelegramNotificationError`.
- `send_message_bulk`, `send_photo_bulk` and `send_document_bulk` for several chats, sent concurrently with a `max_concurrent` limit. Failures are collected in a `BulkSendResult` as the same exceptions, or with `fail_silently=False` the first one is raised and the remaining sends are cancelled.
- Files as a local path, an `http(s)` URL or a file-like object.
- Chat IDs as `int`, `str` or a list. A digit-only string is also tried with the `-` and `-100` prefixes, so IDs copied from Telegram clients without the prefix work. The result is cached.
- Default chat IDs from the `TG_CHAT_ID` or `TG_CHAT_IDS` environment variable (comma-separated) when only a token is given.
- Validation of the token format, chat IDs and message length (1 to 4096 characters) with pydantic.
- Async context manager that closes the HTTP session.
- Type annotations shipped with the package (`py.typed`).

## Limitations

- Async only.
- No retries and no rate limiting. `max_concurrent` limits parallel requests, not requests per second.
- Messages are always sent with a parse mode (HTML by default), so `<`, `>` and `&` in plain text must be escaped.
- Single-chat methods return `None`, not the sent message.
- Telegram `file_id` strings are not accepted. A string that is not a URL is treated as a local path.
- A digit-only string chat ID costs one to three `getChat` requests the first time it is used by a bot object. Integer IDs and `@usernames` are sent as is.

## Compatibility

| Dependency | Supported | Tested in CI |
|---|---|---|
| Python | 3.10 to 3.14 | 3.10, 3.11, 3.12, 3.13, 3.14 |
| aiogram | >=3.15, <4 | newest allowed release, and 3.15.0 |
| pydantic | >=2.4.1, <3 | newest allowed by aiogram, and 2.4.1 |

The lowest versions (aiogram 3.15.0, pydantic 2.4.1) are tested on Python 3.10. Python 3.9 was supported up to 1.0.0.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

With pip 25.1 or newer, use `pip install -e . --group dev` and run the same commands without `uv run`. `pre-commit install` runs ruff and mypy on every commit.

Tests never call the Telegram API: `aiogram.Bot` is replaced with an autospec mock, and a fixture in `tests/conftest.py` fails any test that tries to send a real request. `pytest` fails below 100% branch coverage.

CI runs lint, type checks and tests on every push and pull request. Dependabot proposes weekly updates for GitHub Actions, pre-commit hooks and `uv.lock`; the version ranges in `pyproject.toml` are changed by hand.

To release, update `__version__` in `tg_notification_bot/__init__.py`, add a `## X.Y.Z` section to [CHANGELOG.md](https://github.com/AI-Stratov/tg_notification_bot/blob/main/CHANGELOG.md), then push a tag `vX.Y.Z`. The publish workflow checks that the tag matches the version and that the changelog has the section, runs CI, uploads to PyPI and creates a GitHub release with the changelog section and the built files.

## License

MIT
