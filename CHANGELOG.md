# Changelog

## 1.1.0 - 2026-10-12

The public API (exported names, method signatures, model fields) is unchanged. Behavior changes:

### Changed

- Python 3.10 or newer is required. Python 3.9 is end of life, and aiogram 3.23+, pydantic 2.14+, mypy 2 and pytest 9 no longer support it.
- Bulk methods translate Telegram errors the same way as single-chat methods. `SendResult.exception` is now `BotBlockedError`, `ChatNotFoundError`, `RateLimitError` or `TelegramNotificationError` instead of a raw aiogram exception, which is kept as `__cause__`.
- `fail_silently=False` raises the first failed send and cancels the sends that have not finished. Before, it re-raised only `ChatNotFoundError` from chat ID lookup and left other sends running.
- Library exceptions are raised with the aiogram exception as `__cause__`.
- Only aiogram errors (`TelegramAPIError`) are wrapped in `TelegramNotificationError`. Other exceptions, such as bugs in calling code, propagate unchanged instead of being reported as "Unexpected error". Network errors now read "Telegram API error: ...".
- Chat ID lookup: only digit-only strings are looked up with `getChat` (as given, then with `-` and `-100`), and the result is cached per bot object. Integers, `@usernames` and strings that start with `-` are sent without extra requests. Before, every send to a string ID made one to three `getChat` calls.
- `getChat` errors other than "bad request" (403, network) are translated into library exceptions.
- `InvalidChatIdError` contains the rejected value instead of the text "empty string".
- A blank entry in `TG_CHAT_ID` no longer hides `TG_CHAT_IDS`.
- `chat_ids` in bulk methods accepts any sequence, so a `list[int]` passes type checking.

### Fixed

- `disable_notification=False` and `protect_content=False` on a message now override `True` in the config. Before, the values were combined with `or`.
- `max_concurrent` below 1 raises `ValueError`. Before, it made bulk sends hang forever.
- Text-mode file objects raise `TypeError` instead of failing inside aiogram, and unsupported file sources raise `TypeError` instead of `FileNotFoundError`. A directory path raises `FileNotFoundError` before any request.
- Optional model fields (`SendResult.error`, `PhotoData.caption`, ...) are no longer reported as required by type checkers.

### Added

- `py.typed` marker, so type checkers use the package annotations.
- Python 3.14 support.

### Development

- Version is defined once, in `tg_notification_bot/__init__.py`.
- Dev tools moved from the `dev` extra to the `dev` dependency group (`uv sync`, or `pip install --group dev`). All tools and the lockfile updated.
- New test suite with 100% branch coverage, enforced by `pytest`. Tests use an autospec mock of `aiogram.Bot`, and a fixture blocks any real request to the Telegram API.
- CI: lint, mypy and tests on Python 3.10 to 3.14 plus the lowest supported dependencies; PyPI publishing on version tags.

## 1.0.0

- Bulk methods for sending to several chats, `TG_CHAT_ID` / `TG_CHAT_IDS` with comma-separated lists.
