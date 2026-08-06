from __future__ import annotations

import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.config import SENDER_GMAIL, load_settings
from bot.form_steps import RECEIPT_STEPS, is_valid_email, validate_step
from bot.mailer import send_receipt_email
from bot.receipt_template import format_preview, generate_order_number
from bot.storage import UserStore

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tg-gmail-bot")

ASK_CLIENT_EMAIL = (
    "Привет. Это DEMO-чек OFFICIALBRAND.\n\n"
    "Сначала пришли email клиента (один раз, потом не меняется).\n"
    "Сменить можно только через поддержку."
)


def _store(context: ContextTypes.DEFAULT_TYPE) -> UserStore:
    return context.application.bot_data["store"]


def _settings(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["settings"]


def _reset_form(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("form_step", None)
    context.user_data.pop("receipt", None)
    context.user_data.pop("awaiting_email", None)


async def _ask_current_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step = context.user_data.get("form_step", 0)
    if step >= len(RECEIPT_STEPS):
        return
    _, prompt = RECEIPT_STEPS[step]
    if update.message:
        await update.message.reply_text(prompt)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    _reset_form(context)
    email = _store(context).get_email(update.effective_user.id)
    if email:
        context.user_data["form_step"] = 0
        context.user_data["receipt"] = {}
        await update.message.reply_text(
            f"Почта клиента: {email}\n\n"
            f"Шаг 1/11\n{RECEIPT_STEPS[0][1]}\n\n"
            "/cancel — отмена"
        )
        return
    context.user_data["awaiting_email"] = True
    await update.message.reply_text(ASK_CLIENT_EMAIL)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "/start — новый DEMO-чек\n"
        "/cancel — отменить заполнение\n"
        "/setemail <user_id> <email> — только поддержка"
    )


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    _reset_form(context)
    await update.message.reply_text("Отменено. /start — начать заново.")


async def setemail_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def _show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    receipt = context.user_data.get("receipt", {})
    receipt["order_number"] = generate_order_number()
    context.user_data["receipt"] = receipt
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📧 Send Receipt", callback_data="send_receipt"),
                InlineKeyboardButton("🔄 Start Over", callback_data="start_over"),
            ]
        ]
    )
    text = format_preview(receipt)
    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard)
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text or not update.effective_user:
        return

    store = _store(context)
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Пустое сообщение.")
        return

    if context.user_data.get("awaiting_email"):
        if not is_valid_email(text):
            await update.message.reply_text("Нужен email, например client@gmail.com")
            return
        try:
            email = store.set_email(user_id, text)
        except (ValueError, PermissionError) as exc:
            await update.message.reply_text(str(exc))
            return
        context.user_data.pop("awaiting_email", None)
        context.user_data["form_step"] = 0
        context.user_data["receipt"] = {}
        await update.message.reply_text(
            f"Почта сохранена: {email}\n\n"
            f"Шаг 1/11\n{RECEIPT_STEPS[0][1]}"
        )
        return

    client_email = store.get_email(user_id)
    if not client_email:
        context.user_data["awaiting_email"] = True
        await update.message.reply_text(ASK_CLIENT_EMAIL)
        return

    if "form_step" not in context.user_data:
        context.user_data["form_step"] = 0
        context.user_data["receipt"] = {}

    step_idx = context.user_data["form_step"]
    if step_idx >= len(RECEIPT_STEPS):
        await update.message.reply_text("Нажми кнопку под превью или /start")
        return

    field, _ = RECEIPT_STEPS[step_idx]
    error = validate_step(field, text)
    if error:
        await update.message.reply_text(error)
        return

    receipt = context.user_data.setdefault("receipt", {})
    receipt[field] = text
    step_idx += 1
    context.user_data["form_step"] = step_idx

    if step_idx < len(RECEIPT_STEPS):
        _, next_prompt = RECEIPT_STEPS[step_idx]
        await update.message.reply_text(
            f"Шаг {step_idx + 1}/11\n{next_prompt}"
        )
        return

    await _show_preview(update, context)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return
    await query.answer()

    if query.data == "start_over":
        context.user_data["form_step"] = 0
        context.user_data["receipt"] = {}
        if query.message:
            await query.message.reply_text(
                f"Заново. Шаг 1/11\n{RECEIPT_STEPS[0][1]}"
            )
        return

    if query.data != "send_receipt":
        return

    store = _store(context)
    settings = _settings(context)
    client_email = store.get_email(update.effective_user.id)
    receipt = context.user_data.get("receipt")
    if not client_email or not receipt:
        if query.message:
            await query.message.reply_text("Нет данных. Нажми /start")
        return

    try:
        send_receipt_email(settings, receipt, to_email=client_email)
    except Exception as exc:
        logger.exception("Failed to send receipt")
        if query.message:
            await query.message.reply_text(f"Ошибка отправки: {exc}")
        return

    _reset_form(context)
    if query.message:
        await query.message.reply_text(
            f"✅ DEMO-чек отправлен на {client_email}\n\n"
            "⚠️ DEMO / NOT A REAL RECEIPT\n"
            "/start — новый чек"
        )


def main() -> None:
    settings = load_settings()
    store = UserStore(Path("data/users.json"))
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings
    app.bot_data["store"] = store
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("setemail", setemail_admin))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    logger.info("Bot started. Sender: %s (DEMO receipts)", SENDER_GMAIL)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
