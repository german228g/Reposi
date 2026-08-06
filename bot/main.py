from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.config import load_settings
from bot.mailer import send_text_email

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tg-gmail-bot")

HELP_TEXT = (
    "Пришли любой текст — я отправлю его на почту.\n"
    "Адрес получателя зафиксирован и меняется только через поддержку."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(f"Привет.\n{HELP_TEXT}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(HELP_TEXT)


async def relay_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    settings = context.application.bot_data["settings"]
    user = update.effective_user
    from_user = (
        f"@{user.username}" if user and user.username else f"id:{user.id if user else '?'}"
    )
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Пустое сообщение — нечего отправлять.")
        return

    try:
        send_text_email(settings, text, from_user=from_user)
    except Exception as exc:
        logger.exception("Failed to send email")
        detail = str(exc)
        hint = ""
        if "BadCredentials" in detail or "Username and Password not accepted" in detail:
            hint = (
                "\nGmail не принял пароль. Нужен пароль приложения "
                "(Google Аккаунт → Безопасность → Пароли приложений)."
            )
        await update.message.reply_text(
            f"Не удалось отправить письмо. Напиши в поддержку.{hint}"
        )
        return

    await update.message.reply_text("Отправлено на почту.")


def main() -> None:
    settings = load_settings()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay_text))
    logger.info("Bot started. Recipient fixed: %s", settings.recipient_email)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
