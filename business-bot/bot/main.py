"""Точка входа Telegram-бота."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from bot.handlers import (  # noqa: E402
    cmd_brand,
    cmd_cancel,
    cmd_channel,
    cmd_help,
    cmd_new,
    cmd_posts,
    cmd_publish,
    cmd_start,
    cmd_status,
    on_callback,
    on_error,
    on_message,
)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "your_bot_token_here":
        print("ERROR: Укажи TELEGRAM_BOT_TOKEN в business-bot/.env")
        sys.exit(1)

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("brand", cmd_brand))
    app.add_handler(CommandHandler("posts", cmd_posts))
    app.add_handler(CommandHandler("channel", cmd_channel))
    app.add_handler(CommandHandler("publish", cmd_publish))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
    app.add_error_handler(on_error)

    print("Business Launch Bot запущен. Ctrl+C — стоп.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
