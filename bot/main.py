from __future__ import annotations

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.config import SENDER_GMAIL, load_settings
from bot.mailer import send_text_email
from bot.storage import UserStore, is_valid_email

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tg-gmail-bot")

ASK_EMAIL = (
    "Сначала пришли свою почту (один раз).\n"
    "Потом любой текст будет уходить тебе на этот email.\n"
    "Сменить почту сам нельзя — только через поддержку."
)


def _store(context: ContextTypes.DEFAULT_TYPE) -> UserStore:
    return context.application.bot_data["store"]


def _settings(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["settings"]


def _user_label(update: Update) -> str:
    user = update.effective_user
    if not user:
        return "unknown"
    if user.username:
        return f"@{user.username}"
    return f"id:{user.id}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    email = _store(context).get_email(update.effective_user.id)
    if email:
        await update.message.reply_text(
            f"Почта уже сохранена: {email}\n"
            "Пришли текст — отправлю на неё.\n"
            "Сменить можно только через поддержку."
        )
        return
    await update.message.reply_text(f"Привет.\n{ASK_EMAIL}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    email = _store(context).get_email(update.effective_user.id)
    if email:
        await update.message.reply_text(
            f"Твоя почта: {email}\nПришли текст — уйдёт на неё письмом."
        )
    else:
        await update.message.reply_text(ASK_EMAIL)


async def setemail_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Поддержка: /setemail <telegram_user_id> <email>"""
    if not update.message or not update.effective_user:
        return
    settings = _settings(context)
    if update.effective_user.id not in settings.admin_ids:
        await update.message.reply_text("Только для поддержки.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Формат: /setemail <user_id> <email>")
        return
    try:
        user_id = int(context.args[0])
        email = _store(context).set_email(user_id, context.args[1], force=True)
    except (ValueError, PermissionError) as exc:
        await update.message.reply_text(str(exc))
        return
    await update.message.reply_text(f"Ок. user {user_id} → {email}")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text or not update.effective_user:
        return

    store = _store(context)
    settings = _settings(context)
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Пустое сообщение.")
        return

    email = store.get_email(user_id)
    if not email:
        if not is_valid_email(text):
            await update.message.reply_text(
                "Это не похоже на email. Пришли почту, например name@gmail.com"
            )
            return
        try:
            email = store.set_email(user_id, text)
        except (ValueError, PermissionError) as exc:
            await update.message.reply_text(str(exc))
            return
        await update.message.reply_text(
            f"Почта сохранена: {email}\nТеперь пришли текст — отправлю на неё."
        )
        return

    # Если уже есть почта, а человек снова шлёт email — не даём сменить
    if is_valid_email(text) and text.strip().lower() != email:
        await update.message.reply_text(
            f"Почта уже зафиксирована: {email}\n"
            "Сменить можно только через поддержку.\n"
            "Если хотел отправить текст — напиши обычное сообщение."
        )
        return

    try:
        send_text_email(
            settings,
            text,
            to_email=email,
            from_user=_user_label(update),
        )
    except Exception as exc:
        logger.exception("Failed to send email")
        await update.message.reply_text(f"Не удалось отправить письмо: {exc}")
        return

    await update.message.reply_text(f"Отправлено на {email}")


def main() -> None:
    settings = load_settings()
    store = UserStore(Path("data/users.json"))
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings
    app.bot_data["store"] = store
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setemail", setemail_admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    logger.info("Bot started. Sender: %s", SENDER_GMAIL)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
