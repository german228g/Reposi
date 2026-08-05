"""Telegram handlers: анкета → бренд → лого → посты → канал."""

from __future__ import annotations

import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from .ai.engine import BusinessAI
from .logo_generator import generate_logo, generate_palette_card
from .posts_generator import generate_posts, write_brand_package
from . import storage

log = logging.getLogger(__name__)
ai = BusinessAI()


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚀 Запустить бизнес", callback_data="start_flow")],
            [
                InlineKeyboardButton("🎨 Бренд-пакет", callback_data="make_brand"),
                InlineKeyboardButton("📣 Посты", callback_data="show_posts"),
            ],
            [
                InlineKeyboardButton("📺 Подключить канал", callback_data="connect_channel"),
                InlineKeyboardButton("💬 Совет AI", callback_data="ask_advice"),
            ],
            [InlineKeyboardButton("ℹ️ Статус", callback_data="status")],
        ]
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    data = storage.load_user(user.id)
    data["username"] = user.username
    data["full_name"] = user.full_name
    storage.save_user(user.id, data)
    text = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я <b>Business Launch AI</b> — помогаю запустить бизнес с нуля:\n"
        "• уточняю идею вопросами\n"
        "• придумываю название и позиционирование\n"
        "• рисую лого и палитру\n"
        "• пишу посты и план канала\n"
        "• помогаю подключить Telegram-канал\n\n"
        f"Движок: <i>{ai.backend_label()}</i>\n\n"
        "Нажми «Запустить бизнес» или просто напиши идею."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Команды:\n"
        "/start — меню\n"
        "/new — новая идея с нуля\n"
        "/brand — собрать бренд-пакет\n"
        "/posts — показать посты\n"
        "/channel — как подключить канал\n"
        "/status — что уже готово\n"
        "/cancel — отменить анкету\n\n"
        "Или просто пиши — я в диалоге.",
        reply_markup=main_keyboard(),
    )


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = storage.load_user(update.effective_user.id)
    data["stage"] = "questionnaire"
    data["q_index"] = 0
    data["profile"] = {}
    data["brand"] = None
    storage.save_user(update.effective_user.id, data)
    q = ai.questions()[0]
    await update.message.reply_text(
        "Ок, начинаем с чистого листа.\n\n" + q["text"],
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]),
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = storage.load_user(update.effective_user.id)
    data["stage"] = "idle"
    storage.save_user(update.effective_user.id, data)
    await update.message.reply_text("Анкета отменена. Можешь начать снова когда угодно.", reply_markup=main_keyboard())


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_status(update, context)


async def cmd_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _build_brand(update, context, update.effective_user.id)


async def cmd_posts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_posts(update, context, update.effective_user.id)


async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _channel_help(update, context, update.effective_user.id)


async def cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _publish_launch(update, context, update.effective_user.id)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if data == "start_flow":
        user_data = storage.load_user(uid)
        user_data["stage"] = "questionnaire"
        user_data["q_index"] = 0
        user_data["profile"] = {}
        storage.save_user(uid, user_data)
        q = ai.questions()[0]
        await query.message.reply_text("Отлично. " + q["text"])
    elif data == "make_brand":
        await _build_brand(update, context, uid)
    elif data == "show_posts":
        await _send_posts(update, context, uid)
    elif data == "connect_channel":
        await _channel_help(update, context, uid)
    elif data == "ask_advice":
        user_data = storage.load_user(uid)
        user_data["stage"] = "advice"
        storage.save_user(uid, user_data)
        await query.message.reply_text("Спрашивай что угодно по бизнесу — отвечу конкретно.")
    elif data == "status":
        await _send_status(update, context)
    elif data == "cancel":
        user_data = storage.load_user(uid)
        user_data["stage"] = "idle"
        storage.save_user(uid, user_data)
        await query.message.reply_text("Отменено.", reply_markup=main_keyboard())
    elif data.startswith("pick_name:"):
        name = data.split(":", 1)[1]
        user_data = storage.load_user(uid)
        if user_data.get("brand"):
            user_data["brand"]["brand_name"] = name
            storage.save_user(uid, user_data)
            await query.message.reply_text(f"Название зафиксировано: <b>{name}</b>. Жми «Бренд-пакет» ещё раз, чтобы пересобрать лого.", parse_mode=ParseMode.HTML)
        else:
            await query.message.reply_text("Сначала собери бренд-пакет.")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    uid = update.effective_user.id
    text = update.message.text.strip()
    data = storage.load_user(uid)

    # Channel forward detection
    if update.message.forward_from_chat and update.message.forward_from_chat.type in {"channel", "supergroup"}:
        chat = update.message.forward_from_chat
        data["channel_id"] = chat.id
        data["channel_username"] = chat.username
        storage.save_user(uid, data)
        await update.message.reply_text(
            f"Канал привязан: {chat.title}\n"
            f"id: <code>{chat.id}</code>\n\n"
            "Добавь бота админом с правом публиковать — и напиши /publish чтобы выложить пост запуска.",
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard(),
        )
        return

    if text.lower() in {"хочу", "publish"} or text.startswith("/publish"):
        await _publish_launch(update, context, uid)
        return

    stage = data.get("stage", "idle")

    if stage == "questionnaire":
        await _handle_questionnaire(update, data, text)
        return

    if stage == "advice":
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        profile = data.get("profile") or {}
        brand = data.get("brand") or {}
        ctx = {**profile, **brand, "stage": "advice", "domain": brand.get("domain")}
        reply = await ai.chat(text, ctx)
        await update.message.reply_text(reply, reply_markup=main_keyboard())
        return

    # Free-form: start questionnaire if looks like idea, else advice
    if len(text) > 20 and not data.get("profile", {}).get("idea"):
        data["stage"] = "questionnaire"
        data["q_index"] = 1
        data["profile"] = {"idea": text}
        storage.save_user(uid, data)
        domain = ai.detect_domain(text)
        info = ai.get_domain_info(domain)
        q = ai.questions()[1]
        await update.message.reply_text(
            f"Записал идею. Похоже на нишу: <b>{info.get('ru')}</b>.\n\n{q['text']}",
            parse_mode=ParseMode.HTML,
        )
        return

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    ctx = {**(data.get("profile") or {}), **(data.get("brand") or {}), "stage": "advice"}
    reply = await ai.chat(text, ctx)
    await update.message.reply_text(reply, reply_markup=main_keyboard())


async def _handle_questionnaire(update: Update, data: dict, text: str) -> None:
    questions = ai.questions()
    idx = int(data.get("q_index", 0))
    if idx >= len(questions):
        data["stage"] = "ready"
        storage.save_user(update.effective_user.id, data)
        await update.message.reply_text("Анкета готова! Собираю бренд-пакет…")
        await _build_brand(update, None, update.effective_user.id)
        return

    key = questions[idx]["key"]
    data.setdefault("profile", {})[key] = text
    idx += 1
    data["q_index"] = idx

    if idx >= len(questions):
        data["stage"] = "ready"
        storage.save_user(update.effective_user.id, data)
        await update.message.reply_text("✅ Анкета собрана. Генерирую бренд, лого и посты…")
        await _build_brand(update, None, update.effective_user.id)
        return

    storage.save_user(update.effective_user.id, data)
    await update.message.reply_text(questions[idx]["text"])


async def _build_brand(update: Update, context: ContextTypes.DEFAULT_TYPE | None, uid: int) -> None:
    data = storage.load_user(uid)
    profile = data.get("profile") or {}
    if not profile.get("idea"):
        msg = "Сначала расскажи идею — жми «Запустить бизнес»."
        if update.callback_query:
            await update.callback_query.message.reply_text(msg, reply_markup=main_keyboard())
        else:
            await update.message.reply_text(msg, reply_markup=main_keyboard())
        return

    target = update.callback_query.message if update.callback_query else update.message
    await target.chat.send_action(ChatAction.UPLOAD_PHOTO)

    brand = ai.brand_strategy(profile)
    # keep chosen name if user already picked
    if data.get("brand", {}) and data["brand"].get("brand_name") in (brand.get("name_options") or []):
        brand["brand_name"] = data["brand"]["brand_name"]

    folder = storage.brand_dir(uid, brand["brand_name"])
    logo_path = folder / "logo.png"
    palette_path = folder / "palette.png"
    generate_logo(brand["brand_name"], brand["palette"], brand.get("style", ""), logo_path)
    generate_palette_card(brand["brand_name"], brand["palette"], palette_path)
    posts = generate_posts(brand, ai)
    write_brand_package(brand, posts, folder)

    data["brand"] = brand
    data["brand_folder"] = str(folder)
    data["posts"] = posts
    data["stage"] = "branded"
    storage.save_user(uid, data)

    name_buttons = [
        [InlineKeyboardButton(n, callback_data=f"pick_name:{n[:40]}")]
        for n in brand.get("name_options", [])[:4]
    ]
    name_buttons.append([InlineKeyboardButton("📺 Подключить канал", callback_data="connect_channel")])

    caption = (
        f"<b>{brand['brand_name']}</b>\n"
        f"{brand.get('tagline')}\n\n"
        f"{brand.get('positioning')}\n\n"
        f"Палитра: {' · '.join(brand.get('palette', []))}\n"
        f"Ниша: {brand.get('domain_ru')}"
    )
    await target.reply_photo(photo=logo_path.open("rb"), caption=caption, parse_mode=ParseMode.HTML)
    await target.reply_photo(photo=palette_path.open("rb"), caption="Дизайн-палитра бренда")
    await target.reply_document(document=(folder / "BRAND.md").open("rb"), filename="BRAND.md")
    await target.reply_document(document=(folder / "POSTS.md").open("rb"), filename="POSTS.md")
    await target.reply_text(
        "Выбери финальное название (или оставь текущее) и подключи канал:",
        reply_markup=InlineKeyboardMarkup(name_buttons),
    )


async def _send_posts(update: Update, context: ContextTypes.DEFAULT_TYPE | None, uid: int) -> None:
    data = storage.load_user(uid)
    posts = data.get("posts")
    target = update.callback_query.message if update.callback_query else update.message
    if not posts:
        await target.reply_text("Постов ещё нет — сначала собери бренд-пакет.", reply_markup=main_keyboard())
        return
    for p in posts[:6]:
        await target.reply_text(f"<b>{p['title']}</b>\n\n{p['text']}", parse_mode=ParseMode.HTML)
    await target.reply_text("Готово. Можешь копировать в канал или /publish", reply_markup=main_keyboard())


async def _channel_help(update: Update, context: ContextTypes.DEFAULT_TYPE | None, uid: int) -> None:
    data = storage.load_user(uid)
    brand = data.get("brand") or {}
    name = brand.get("brand_name", "Мой бизнес")
    tagline = brand.get("tagline", "Запуск бизнеса")
    target = update.callback_query.message if update.callback_query else update.message
    text = (
        f"<b>Создание канала для {name}</b>\n\n"
        "1. Telegram → Новый канал\n"
        f"2. Название: <code>{name}</code>\n"
        f"3. Описание: <code>{tagline}</code>\n"
        "4. Аватар: logo.png из бренд-пакета\n"
        "5. Добавь этого бота админом (право «Публикация сообщений»)\n"
        "6. Перешли любой пост из канала сюда — я привяжу канал\n"
        "7. Команда /publish — выложу пост запуска\n\n"
        "⚠️ Бот не может создать канал за тебя (ограничение Telegram API), "
        "но полностью готовит контент и публикует после подключения."
    )
    if data.get("channel_id"):
        text += f"\n\n✅ Уже привязан channel_id: <code>{data['channel_id']}</code>"
    await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())


async def _publish_launch(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: int) -> None:
    data = storage.load_user(uid)
    channel_id = data.get("channel_id")
    posts = data.get("posts") or []
    if not channel_id:
        await update.message.reply_text("Сначала привяжи канал: перешли сюда любой пост из канала.")
        return
    if not posts:
        await update.message.reply_text("Нет постов — собери бренд-пакет.")
        return
    try:
        folder = Path(data.get("brand_folder") or "")
        logo = folder / "logo.png"
        text = posts[0]["text"]
        if logo.exists():
            await context.bot.send_photo(chat_id=channel_id, photo=logo.open("rb"), caption=text)
        else:
            await context.bot.send_message(chat_id=channel_id, text=text)
        await update.message.reply_text("✅ Пост запуска опубликован в канале!")
    except Exception as e:
        log.exception("publish failed")
        await update.message.reply_text(
            f"Не смог опубликовать: {e}\n"
            "Проверь, что бот — админ канала с правом постить."
        )


async def _send_status(update: Update, context: ContextTypes.DEFAULT_TYPE | None) -> None:
    uid = update.effective_user.id
    data = storage.load_user(uid)
    brand = data.get("brand") or {}
    profile = data.get("profile") or {}
    text = (
        f"<b>Статус</b>\n"
        f"Этап: {data.get('stage')}\n"
        f"Идея: {profile.get('idea', '—')[:120]}\n"
        f"Бренд: {brand.get('brand_name', '—')}\n"
        f"Канал: {data.get('channel_id') or 'не подключён'}\n"
        f"AI: {ai.backend_label()}"
    )
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())
