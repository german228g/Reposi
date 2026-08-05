"""Telegram handlers: профиль → анкета → бренд → посты → канал."""

from __future__ import annotations

import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.constants import ChatAction, ChatType, ParseMode
from telegram.ext import ContextTypes

from . import storage
from .ai.engine import BusinessAI
from .logo_generator import generate_logo
from .posts_generator import generate_posts, write_brand_package

log = logging.getLogger(__name__)
ai = BusinessAI()


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚀 Запустить бизнес", callback_data="start_flow")],
            [
                InlineKeyboardButton("📣 Посты", callback_data="show_posts"),
                InlineKeyboardButton("📺 Канал", callback_data="connect_channel"),
            ],
            [
                InlineKeyboardButton("💬 Совет", callback_data="ask_advice"),
                InlineKeyboardButton("ℹ️ Статус", callback_data="status"),
            ],
        ]
    )


def _target_message(update: Update):
    if update.callback_query:
        return update.callback_query.message
    return update.message


def _forward_channel(message):
    """PTB v21+: forward_origin вместо forward_from_chat."""
    origin = getattr(message, "forward_origin", None)
    if origin is None:
        return None
    chat = getattr(origin, "chat", None)
    if chat is not None and getattr(chat, "type", None) in {ChatType.CHANNEL, ChatType.SUPERGROUP, "channel", "supergroup"}:
        return chat
    return None


def _profile_connected(data: dict) -> bool:
    return bool(data.get("tg_connected"))


async def _ask_connect_profile(update: Update, user: User) -> None:
    uname = f"@{user.username}" if user.username else "без @username"
    text = (
        "<b>Подключи Telegram-профиль</b>\n\n"
        f"Имя: <b>{user.full_name}</b>\n"
        f"Юзернейм: <b>{uname}</b>\n"
        f"ID: <code>{user.id}</code>\n\n"
        "Нажми кнопку ниже — привяжу этот аккаунт к запуску бизнеса."
    )
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Подключить этот профиль", callback_data="connect_profile")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
        ]
    )
    target = _target_message(update)
    await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    data = storage.load_user(user.id)
    data["username"] = user.username
    data["full_name"] = user.full_name
    storage.save_user(user.id, data)
    linked = "✅ профиль уже подключён" if _profile_connected(data) else "сначала подключим твой Telegram-профиль"
    text = (
        f"Привет, {user.first_name}!\n\n"
        "Я помогу запустить бизнес: идея → бренд → лого → посты → канал.\n\n"
        f"Сейчас: <i>{linked}</i>\n\n"
        "Жми «Запустить бизнес»."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start — меню\n"
        "/new — новый запуск\n"
        "/posts — посты\n"
        "/channel — канал\n"
        "/publish — опубликовать в канал\n"
        "/status — статус\n"
        "/cancel — отмена",
        reply_markup=main_keyboard(),
    )


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _begin_flow(update, update.effective_user)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = storage.load_user(update.effective_user.id)
    data["stage"] = "idle"
    storage.save_user(update.effective_user.id, data)
    await update.message.reply_text("Отменено.", reply_markup=main_keyboard())


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_status(update)


async def cmd_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _build_brand(update, update.effective_user.id)


async def cmd_posts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_posts(update, update.effective_user.id)


async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _channel_help(update, update.effective_user.id)


async def cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _publish_launch(update, context, update.effective_user.id)


async def _begin_flow(update: Update, user: User) -> None:
    data = storage.load_user(user.id)
    data["username"] = user.username
    data["full_name"] = user.full_name
    data["profile"] = {}
    data["brand"] = None
    data["posts"] = None
    data["q_index"] = 0
    if not _profile_connected(data):
        data["stage"] = "await_profile"
        storage.save_user(user.id, data)
        await _ask_connect_profile(update, user)
        return
    data["stage"] = "questionnaire"
    storage.save_user(user.id, data)
    await _target_message(update).reply_text(
        "Профиль уже подключён. Расскажи идею бизнеса своими словами.\n"
        "Чем хочешь заниматься и для кого?"
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data
    user = query.from_user

    if data == "start_flow":
        await _begin_flow(update, user)
        return

    if data == "connect_profile":
        user_data = storage.load_user(uid)
        user_data["tg_connected"] = True
        user_data["tg_user_id"] = uid
        user_data["username"] = user.username
        user_data["full_name"] = user.full_name
        pending = (user_data.pop("pending_idea", None) or "").strip()
        uname = f"@{user.username}" if user.username else user.full_name
        if pending:
            user_data["stage"] = "questionnaire"
            user_data["q_index"] = 1
            user_data["profile"] = {"idea": pending}
            storage.save_user(uid, user_data)
            domain = ai.detect_domain(pending)
            info = ai.get_domain_info(domain)
            await query.message.reply_text(
                f"✅ Профиль подключён: <b>{uname}</b>\n"
                f"Идею уже записал. Ниша: <b>{info.get('ru')}</b>.\n\n"
                f"{ai.questions()[1]['text']}",
                parse_mode=ParseMode.HTML,
            )
            return
        user_data["stage"] = "questionnaire"
        user_data["q_index"] = 0
        user_data["profile"] = {}
        storage.save_user(uid, user_data)
        await query.message.reply_text(
            f"✅ Профиль подключён: <b>{uname}</b>\n\n"
            "Расскажи идею бизнеса своими словами.\n"
            "Чем хочешь заниматься и для кого?",
            parse_mode=ParseMode.HTML,
        )
        return

    if data == "make_brand":
        await _build_brand(update, uid)
    elif data == "show_posts":
        await _send_posts(update, uid)
    elif data == "connect_channel":
        await _channel_help(update, uid)
    elif data == "ask_advice":
        user_data = storage.load_user(uid)
        user_data["stage"] = "advice"
        storage.save_user(uid, user_data)
        await query.message.reply_text("Спрашивай по бизнесу — отвечу коротко и по делу.")
    elif data == "status":
        await _send_status(update)
    elif data == "cancel":
        user_data = storage.load_user(uid)
        user_data["stage"] = "idle"
        storage.save_user(uid, user_data)
        await query.message.reply_text("Отменено.", reply_markup=main_keyboard())
    elif data == "need_posts":
        await _send_posts(update, uid)
    elif data.startswith("pick_name:"):
        name = data.split(":", 1)[1]
        user_data = storage.load_user(uid)
        if user_data.get("brand"):
            user_data["brand"]["brand_name"] = name
            storage.save_user(uid, user_data)
            await query.message.reply_text(
                f"Ок, название: <b>{name}</b>. Могу пересобрать лого — /brand",
                parse_mode=ParseMode.HTML,
                reply_markup=main_keyboard(),
            )
        else:
            await query.message.reply_text("Сначала пройди анкету идеи.")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return

    uid = update.effective_user.id
    data = storage.load_user(uid)

    # Привязка канала через пересланный пост
    channel = _forward_channel(message)
    if channel is not None:
        data["channel_id"] = channel.id
        data["channel_username"] = getattr(channel, "username", None)
        storage.save_user(uid, data)
        await message.reply_text(
            f"✅ Канал привязан: <b>{channel.title}</b>\n"
            "Добавь бота админом с правом публиковать, затем /publish",
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard(),
        )
        return

    if not message.text:
        return

    text = message.text.strip()
    if not text:
        return

    if text.lower() in {"хочу", "publish"}:
        await _publish_launch(update, context, uid)
        return

    stage = data.get("stage", "idle")

    if stage == "await_profile":
        await _ask_connect_profile(update, update.effective_user)
        return

    if stage == "questionnaire":
        await _handle_questionnaire(update, data, text)
        return

    if stage == "advice":
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        profile = data.get("profile") or {}
        brand = data.get("brand") or {}
        reply = await ai.chat(text, {**profile, **brand, "stage": "advice", "domain": brand.get("domain")})
        await message.reply_text(reply, reply_markup=main_keyboard())
        return

    # Свободный текст с идеей — но сначала профиль
    if len(text) >= 8 and not (data.get("profile") or {}).get("idea"):
        if not _profile_connected(data):
            data["stage"] = "await_profile"
            data["pending_idea"] = text
            storage.save_user(uid, data)
            await message.reply_text("Сначала подключим профиль — это нужно один раз.")
            await _ask_connect_profile(update, update.effective_user)
            return
        data["stage"] = "questionnaire"
        data["q_index"] = 1
        data["profile"] = {"idea": text}
        storage.save_user(uid, data)
        domain = ai.detect_domain(text)
        info = ai.get_domain_info(domain)
        await message.reply_text(
            f"Записал. Ниша: <b>{info.get('ru')}</b>.\n\n{ai.questions()[1]['text']}",
            parse_mode=ParseMode.HTML,
        )
        return

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    reply = await ai.chat(text, {**(data.get("profile") or {}), **(data.get("brand") or {}), "stage": "advice"})
    await message.reply_text(reply, reply_markup=main_keyboard())


async def _handle_questionnaire(update: Update, data: dict, text: str) -> None:
    questions = ai.questions()
    idx = int(data.get("q_index", 0))
    uid = update.effective_user.id

    if idx < 0 or idx >= len(questions):
        data["stage"] = "ready"
        storage.save_user(uid, data)
        await update.message.reply_text("Анкета готова — собираю бренд…")
        await _build_brand(update, uid)
        return

    key = questions[idx]["key"]
    data.setdefault("profile", {})[key] = text
    idx += 1
    data["q_index"] = idx

    # Короткое подтверждение после идеи
    if key == "idea":
        domain = ai.detect_domain(text)
        info = ai.get_domain_info(domain)
        await update.message.reply_text(f"Понял, ниша: <b>{info.get('ru')}</b>.", parse_mode=ParseMode.HTML)

    if idx >= len(questions):
        data["stage"] = "ready"
        storage.save_user(uid, data)
        await update.message.reply_text("✅ Анкета собрана. Делаю название и лого…")
        await _build_brand(update, uid)
        return

    storage.save_user(uid, data)
    await update.message.reply_text(questions[idx]["text"])


async def _build_brand(update: Update, uid: int) -> None:
    data = storage.load_user(uid)
    profile = data.get("profile") or {}
    target = _target_message(update)

    if not profile.get("idea"):
        await target.reply_text(
            "Сначала расскажи идею — жми «Запустить бизнес».",
            reply_markup=main_keyboard(),
        )
        return

    await target.chat.send_action(ChatAction.UPLOAD_PHOTO)
    brand = ai.brand_strategy(profile)
    if data.get("brand") and data["brand"].get("brand_name") in (brand.get("name_options") or []):
        brand["brand_name"] = data["brand"]["brand_name"]

    folder = storage.brand_dir(uid, brand["brand_name"])
    logo_path = folder / "logo.png"
    generate_logo(brand["brand_name"], brand["palette"], brand.get("style", ""), logo_path)
    posts = generate_posts(brand, ai)
    write_brand_package(brand, posts, folder)

    data["brand"] = brand
    data["brand_folder"] = str(folder)
    data["posts"] = posts
    data["stage"] = "branded"
    storage.save_user(uid, data)

    caption = (
        f"<b>{brand['brand_name']}</b>\n"
        f"{brand.get('tagline')}\n\n"
        f"{brand.get('positioning')}\n\n"
        f"Палитра: {' · '.join(brand.get('palette', []))}"
    )
    # Одно фото — только лого
    with logo_path.open("rb") as photo:
        await target.reply_photo(photo=photo, caption=caption, parse_mode=ParseMode.HTML)

    names = ", ".join(brand.get("name_options", [])[:4])
    await target.reply_text(
        f"Другие названия: {names}\n\n"
        "Дальше: посмотри посты или подключи канал.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📣 Показать посты", callback_data="need_posts")],
                [InlineKeyboardButton("📺 Подключить канал", callback_data="connect_channel")],
                [InlineKeyboardButton("🏠 Меню", callback_data="status")],
            ]
        ),
    )


async def _send_posts(update: Update, uid: int) -> None:
    data = storage.load_user(uid)
    posts = data.get("posts") or []
    target = _target_message(update)
    if not posts:
        await target.reply_text("Постов ещё нет — сначала пройди «Запустить бизнес».", reply_markup=main_keyboard())
        return
    # Не спамим: 1 сообщение со всеми постами
    chunks = [f"<b>{p['title']}</b>\n{p['text']}" for p in posts[:4]]
    text = "\n\n————\n\n".join(chunks)
    if len(text) > 3500:
        text = text[:3490] + "…"
    await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())


async def _channel_help(update: Update, uid: int) -> None:
    data = storage.load_user(uid)
    brand = data.get("brand") or {}
    name = brand.get("brand_name", "Мой бизнес")
    tagline = brand.get("tagline", "Запуск бизнеса")
    target = _target_message(update)
    text = (
        f"<b>Канал для {name}</b>\n\n"
        "1. Создай канал в Telegram\n"
        f"2. Название: <code>{name}</code>\n"
        f"3. Описание: <code>{tagline}</code>\n"
        "4. Аватар — лого, которое я прислал\n"
        "5. Добавь бота админом (публикация сообщений)\n"
        "6. Перешли сюда любой пост из канала\n"
        "7. /publish — выложу запуск\n"
    )
    if data.get("channel_id"):
        text += f"\n✅ Уже привязан: <code>{data['channel_id']}</code>"
    await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())


async def _publish_launch(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: int) -> None:
    data = storage.load_user(uid)
    channel_id = data.get("channel_id")
    posts = data.get("posts") or []
    if not channel_id:
        await update.message.reply_text("Сначала привяжи канал: перешли сюда пост из канала.")
        return
    if not posts:
        await update.message.reply_text("Нет постов — сначала собери бренд.")
        return
    try:
        folder = Path(data.get("brand_folder") or "")
        logo = folder / "logo.png"
        text = posts[0]["text"]
        if logo.exists():
            with logo.open("rb") as photo:
                await context.bot.send_photo(chat_id=channel_id, photo=photo, caption=text)
        else:
            await context.bot.send_message(chat_id=channel_id, text=text)
        await update.message.reply_text("✅ Пост запуска опубликован!")
    except Exception as e:
        log.exception("publish failed")
        await update.message.reply_text(
            f"Не смог опубликовать: {e}\nПроверь, что бот — админ канала."
        )


async def _send_status(update: Update) -> None:
    uid = update.effective_user.id
    data = storage.load_user(uid)
    brand = data.get("brand") or {}
    profile = data.get("profile") or {}
    uname = data.get("username")
    text = (
        f"<b>Статус</b>\n"
        f"Профиль: {'✅ @' + uname if data.get('tg_connected') and uname else ('✅ подключён' if data.get('tg_connected') else '❌ не подключён')}\n"
        f"Этап: {data.get('stage')}\n"
        f"Идея: {(profile.get('idea') or '—')[:120]}\n"
        f"Бренд: {brand.get('brand_name') or '—'}\n"
        f"Канал: {data.get('channel_id') or 'не подключён'}"
    )
    await _target_message(update).reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Update error: %s", context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Что-то сломалось на моей стороне. Нажми /start и попробуй ещё раз."
            )
        except Exception:
            pass
