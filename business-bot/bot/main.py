"""Точка входа Telegram-бота."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram.ext import (
    AIORateLimiter,
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from bot.handlers import (  # noqa: E402
    cmd_brand,
    cmd_cancel,
    cmd_connect,
    cmd_create_channel,
    cmd_help,
    cmd_logout,
    cmd_new,
    cmd_posts,
    cmd_setapi,
    cmd_start,
    cmd_status,
    on_callback,
    on_error,
    on_message,
)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "your_bot_token_here":
        print("ERROR: укажи TELEGRAM_BOT_TOKEN в business-bot/.env")
        sys.exit(1)

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Увеличенные таймауты: загрузка лого на медленной сети иначе рвётся
    request = HTTPXRequest(connect_timeout=20, read_timeout=60, write_timeout=60, pool_timeout=20)
    app = (
        Application.builder()
        .token(token)
        .request(request)
        .rate_limiter(AIORateLimiter())
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("connect", cmd_connect))
    app.add_handler(CommandHandler("logout", cmd_logout))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("brand", cmd_brand))
    app.add_handler(CommandHandler("posts", cmd_posts))
    app.add_handler(CommandHandler("createchannel", cmd_create_channel))
    app.add_handler(CommandHandler("setapi", cmd_setapi))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
    app.add_error_handler(on_error)

    print("Business Launch Bot запущен. Ctrl+C — стоп.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
