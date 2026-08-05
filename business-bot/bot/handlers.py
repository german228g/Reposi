"""Telegram handlers: подключение аккаунта → умный опрос → бренд → авто-канал."""

from __future__ import annotations

import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.constants import ChatAction, ChatType, ParseMode
from telegram.ext import ContextTypes

from . import storage, telegram_account as account
from .ai.engine import BusinessAI
from .logo_generator import generate_logo
from .posts_generator import generate_posts, write_brand_package

log = logging.getLogger(__name__)
ai = BusinessAI()


def main_keyboard(connected: bool = False) -> InlineKeyboardMarkup:
    first = (
        InlineKeyboardButton("🚀 Запустить бизнес", callback_data="start_flow")
        if connected
        else InlineKeyboardButton("🔗 Подключить аккаунт", callback_data="connect_account")
    )
    return InlineKeyboardMarkup(
        [
            [first],
            [
                InlineKeyboardButton("📣 Посты", callback_data="show_posts"),
                InlineKeyboardButton("📺 Канал", callback_data="channel_menu"),
            ],
            [
                InlineKeyboardButton("💬 Совет", callback_data="ask_advice"),
                InlineKeyboardButton("ℹ️ Статус", callback_data="status"),
            ],
        ]
    )


def _options_keyboard(options: list[str], key: str) -> InlineKeyboardMarkup | None:
    if not options:
        return None
    rows = [[InlineKeyboardButton(o, callback_data=f"ans:{key}:{o[:48]}")] for o in options[:4]]
    return InlineKeyboardMarkup(rows)


def _target(update: Update):
    return update.callback_query.message if update.callback_query else update.message


def _forward_channel(message):
    origin = getattr(message, "forward_origin", None)
    chat = getattr(origin, "chat", None) if origin else None
    if chat is not None and getattr(chat, "type", None) in {
        ChatType.CHANNEL, ChatType.SUPERGROUP, "channel", "supergroup",
    }:
        return chat
    return None


# ---------- команды ----------


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    data = storage.load_user(user.id)
    data["username"] = user.username
    data["full_name"] = user.full_name
    storage.save_user(user.id, data)
    connected = account.has_session(user.id)
    stats = ai.backend_label()
    if connected:
        head = "✅ Аккаунт подключён — могу сам создать канал и всё в него выложить."
    else:
        head = "Сначала подключим твой Telegram-аккаунт: тогда я сам создам канал, поставлю аватар, описание и выложу посты."
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n\n{head}\n\n<i>AI: {stats}</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(connected),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/connect — подключить Telegram-аккаунт\n"
        "/new — новый запуск бизнеса\n"
        "/createchannel — создать канал автоматически\n"
        "/posts — посты\n"
        "/status — статус\n"
        "/logout — отключить аккаунт\n"
        "/cancel — отмена",
        reply_markup=main_keyboard(account.has_session(update.effective_user.id)),
    )


async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _start_account_login(update, update.effective_user)


async def cmd_logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    account.drop_session(uid)
    data = storage.load_user(uid)
    data["account_name"] = None
    data["stage"] = "idle"
    storage.save_user(uid, data)
    await update.message.reply_text("Аккаунт отключён, сессия удалена.", reply_markup=main_keyboard(False))


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _begin_flow(update, update.effective_user)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    data = storage.load_user(uid)
    data["stage"] = "idle"
    storage.save_user(uid, data)
    await update.message.reply_text("Отменено.", reply_markup=main_keyboard(account.has_session(uid)))


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_status(update)


async def cmd_posts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_posts(update, update.effective_user.id)


async def cmd_create_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _auto_create_channel(update, context, update.effective_user.id)


async def cmd_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _build_brand(update, update.effective_user.id)


# ---------- подключение аккаунта ----------


async def _start_account_login(update: Update, user: User) -> None:
    target = _target(update)
    if not account.is_configured():
        await target.reply_text(
            "<b>Нужны API-ключи Telegram</b>\n\n"
            "Чтобы я мог создавать канал и постить от твоего имени, нужен доступ MTProto:\n\n"
            "1. Зайди на my.telegram.org\n"
            "2. API development tools → создай приложение\n"
            "3. Скопируй <code>api_id</code> и <code>api_hash</code>\n"
            "4. Впиши в <code>business-bot/.env</code>:\n"
            "<code>TG_API_ID=1234567\nTG_API_HASH=abcdef...</code>\n"
            "5. Перезапусти бота и снова нажми «Подключить аккаунт»\n\n"
            "Без этого я работаю в режиме помощника: готовлю бренд, лого и посты, "
            "но канал придётся создать вручную.",
            parse_mode=ParseMode.HTML,
        )
        return

    if account.has_session(user.id):
        name = await account.account_name(user.id)
        if name:
            data = storage.load_user(user.id)
            data["account_name"] = name
            storage.save_user(user.id, data)
            await target.reply_text(
                f"Аккаунт уже подключён: <b>{name}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=main_keyboard(True),
            )
            return
        account.drop_session(user.id)

    data = storage.load_user(user.id)
    data["stage"] = "await_phone"
    storage.save_user(user.id, data)
    await target.reply_text(
        "<b>Подключение аккаунта</b>\n\n"
        "Пришли номер телефона этого Telegram-аккаунта в формате <code>+380971234567</code>.\n\n"
        "Я отправлю код подтверждения в Telegram. Сессия хранится локально на твоём сервере, "
        "отключить можно командой /logout.",
        parse_mode=ParseMode.HTML,
    )


async def _handle_phone(update: Update, uid: int, text: str) -> None:
    phone = text.replace(" ", "").replace("-", "")
    if not phone.startswith("+") or not phone[1:].isdigit() or len(phone) < 10:
        await update.message.reply_text("Формат номера: +380971234567")
        return
    try:
        started = await account.start_login(phone)
    except account.AccountError as exc:
        await update.message.reply_text(str(exc))
        return
    except Exception as exc:
        log.exception("send_code failed")
        await update.message.reply_text(f"Не смог отправить код: {exc}")
        return

    data = storage.load_user(uid)
    data["stage"] = "await_code"
    data["login_phone"] = phone
    data["login_hash"] = started.phone_code_hash
    data["login_session"] = started.session_string
    storage.save_user(uid, data)
    await update.message.reply_text(
        "Код отправлен в Telegram. Пришли его сюда (например <code>12345</code>).\n"
        "Если код пришёл в этот чат от Telegram — просто перепечатай цифры.",
        parse_mode=ParseMode.HTML,
    )


async def _handle_code(update: Update, uid: int, text: str) -> None:
    code = "".join(ch for ch in text if ch.isdigit())
    if len(code) < 4:
        await update.message.reply_text("Пришли код цифрами, например 12345")
        return
    data = storage.load_user(uid)
    try:
        session_string, name, need_password = await account.complete_login(
            phone=data.get("login_phone", ""),
            code=code,
            phone_code_hash=data.get("login_hash", ""),
            session_string=data.get("login_session", ""),
        )
    except account.AccountError as exc:
        await update.message.reply_text(str(exc))
        return
    except Exception as exc:
        log.exception("sign_in failed")
        await update.message.reply_text(f"Ошибка входа: {exc}")
        return

    if need_password:
        data["stage"] = "await_password"
        data["login_session"] = session_string
        storage.save_user(uid, data)
        await update.message.reply_text("У аккаунта включена двухфакторная защита. Пришли пароль (облачный пароль).")
        return

    await _finish_login(update, uid, session_string, name)


async def _handle_password(update: Update, uid: int, text: str) -> None:
    data = storage.load_user(uid)
    try:
        session_string, name, _ = await account.complete_login(
            phone=data.get("login_phone", ""),
            code="",
            phone_code_hash=data.get("login_hash", ""),
            session_string=data.get("login_session", ""),
            password=text,
        )
    except account.AccountError as exc:
        await update.message.reply_text(str(exc))
        return
    except Exception as exc:
        log.exception("2fa failed")
        await update.message.reply_text(f"Пароль не подошёл: {exc}")
        return
    await _finish_login(update, uid, session_string, name)


async def _finish_login(update: Update, uid: int, session_string: str, name: str) -> None:
    account.save_session(uid, session_string)
    data = storage.load_user(uid)
    data["account_name"] = name
    for key in ("login_phone", "login_hash", "login_session"):
        data.pop(key, None)
    data["stage"] = "questionnaire"
    data["profile"] = {}
    storage.save_user(uid, data)
    try:
        await update.message.delete()
    except Exception:
        pass
    await update.effective_chat.send_message(
        f"✅ Аккаунт подключён: <b>{name or 'готово'}</b>\n\n"
        "Теперь расскажи идею: что продаёшь и кому? Одним предложением.",
        parse_mode=ParseMode.HTML,
    )


# ---------- флоу бизнеса ----------


async def _begin_flow(update: Update, user: User) -> None:
    uid = user.id
    data = storage.load_user(uid)
    data["profile"] = {}
    data["brand"] = None
    data["posts"] = None
    if account.is_configured() and not account.has_session(uid):
        await _start_account_login(update, user)
        return
    data["stage"] = "questionnaire"
    storage.save_user(uid, data)
    await _target(update).reply_text("Расскажи идею: что продаёшь и кому? Одним предложением.")


async def _ask_next(update: Update, uid: int, data: dict) -> bool:
    """Задаёт следующий нужный вопрос. True — если вопрос задан."""
    question = ai.next_question(data.get("profile") or {})
    if question is None:
        return False
    data["awaiting_key"] = question["key"]
    storage.save_user(uid, data)
    await _target(update).reply_text(
        question["text"],
        reply_markup=_options_keyboard(question.get("options") or [], question["key"]),
    )
    return True


async def _accept_answer(update: Update, uid: int, key: str, value: str) -> None:
    data = storage.load_user(uid)
    profile = data.setdefault("profile", {})
    profile[key] = value

    if key == "idea":
        analysis = ai.analyze(value)
        profile["domain"] = analysis["domain"]
        for field in ("geo", "age", "audience", "budget", "model", "product"):
            if analysis.get(field) and not profile.get(field):
                profile[field] = analysis[field]
        understood = [f"ниша: <b>{analysis['domain_ru']}</b>"]
        if analysis.get("geo"):
            understood.append(f"гео: <b>{analysis['geo']}</b>")
        if analysis.get("age"):
            understood.append(f"возраст: <b>{analysis['age']}</b>")
        if analysis.get("group"):
            understood.append(f"аудитория: <b>{analysis['group']}</b>")
        await _target(update).reply_text(
            "Понял: " + ", ".join(understood),
            parse_mode=ParseMode.HTML,
        )

    data["stage"] = "questionnaire"
    storage.save_user(uid, data)

    if await _ask_next(update, uid, data):
        return

    data["stage"] = "ready"
    data.pop("awaiting_key", None)
    storage.save_user(uid, data)
    await _target(update).reply_text("Данных хватает. Собираю бренд и посты…")
    await _build_brand(update, uid)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data
    user = query.from_user

    if data == "connect_account":
        await _start_account_login(update, user)
        return
    if data == "start_flow":
        await _begin_flow(update, user)
        return
    if data.startswith("ans:"):
        _, key, value = data.split(":", 2)
        await _accept_answer(update, uid, key, value)
        return
    if data == "make_brand":
        await _build_brand(update, uid)
        return
    if data in {"show_posts", "need_posts"}:
        await _send_posts(update, uid)
        return
    if data == "channel_menu":
        await _channel_menu(update, uid)
        return
    if data == "auto_channel":
        await _auto_create_channel(update, context, uid)
        return
    if data == "ask_advice":
        user_data = storage.load_user(uid)
        user_data["stage"] = "advice"
        storage.save_user(uid, user_data)
        await query.message.reply_text("Спрашивай по бизнесу — отвечу по твоей нише.")
        return
    if data == "status":
        await _send_status(update)
        return
    if data == "cancel":
        user_data = storage.load_user(uid)
        user_data["stage"] = "idle"
        storage.save_user(uid, user_data)
        await query.message.reply_text("Отменено.", reply_markup=main_keyboard(account.has_session(uid)))
        return
    if data.startswith("pick_name:"):
        name = data.split(":", 1)[1]
        user_data = storage.load_user(uid)
        if user_data.get("brand"):
            user_data["brand"]["brand_name"] = name
            storage.save_user(uid, user_data)
            await query.message.reply_text(
                f"Название: <b>{name}</b>. Пересобрать лого — /brand",
                parse_mode=ParseMode.HTML,
                reply_markup=main_keyboard(account.has_session(uid)),
            )
        return


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return
    uid = update.effective_user.id
    data = storage.load_user(uid)

    channel = _forward_channel(message)
    if channel is not None:
        data["channel_id"] = channel.id
        data["channel_username"] = getattr(channel, "username", None)
        storage.save_user(uid, data)
        await message.reply_text(
            f"✅ Канал привязан: <b>{channel.title}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard(account.has_session(uid)),
        )
        return

    if not message.text:
        return
    text = message.text.strip()
    if not text:
        return

    stage = data.get("stage", "idle")

    if stage == "await_phone":
        await _handle_phone(update, uid, text)
        return
    if stage == "await_code":
        await _handle_code(update, uid, text)
        return
    if stage == "await_password":
        await _handle_password(update, uid, text)
        return

    if stage == "questionnaire":
        key = data.get("awaiting_key") or ("idea" if not (data.get("profile") or {}).get("idea") else None)
        if key:
            await _accept_answer(update, uid, key, text)
            return

    if stage == "advice":
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        reply = await ai.chat(text, {**(data.get("profile") or {}), **(data.get("brand") or {})})
        await message.reply_text(reply, reply_markup=main_keyboard(account.has_session(uid)))
        return

    # свободный текст: если идеи ещё нет — считаем это идеей
    if len(text) >= 6 and not (data.get("profile") or {}).get("idea"):
        data["stage"] = "questionnaire"
        storage.save_user(uid, data)
        await _accept_answer(update, uid, "idea", text)
        return

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    reply = await ai.chat(text, {**(data.get("profile") or {}), **(data.get("brand") or {})})
    await message.reply_text(reply, reply_markup=main_keyboard(account.has_session(uid)))


# ---------- бренд, посты, канал ----------


async def _build_brand(update: Update, uid: int) -> None:
    data = storage.load_user(uid)
    profile = data.get("profile") or {}
    target = _target(update)
    if not profile.get("idea"):
        await target.reply_text("Сначала расскажи идею.", reply_markup=main_keyboard(account.has_session(uid)))
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

    plan = "\n".join(f"{i+1}. {s}" for i, s in enumerate(brand.get("launch_plan", [])[:6]))
    caption = (
        f"<b>{brand['brand_name']}</b>\n"
        f"{brand.get('tagline')}\n\n"
        f"{brand.get('positioning')}\n\n"
        f"<b>План на 7 дней</b>\n{plan}"
    )
    if len(caption) > 1024:
        with logo_path.open("rb") as photo:
            await target.reply_photo(photo=photo, caption=f"<b>{brand['brand_name']}</b>\n{brand.get('tagline')}", parse_mode=ParseMode.HTML)
        await target.reply_text(f"{brand.get('positioning')}\n\n<b>План на 7 дней</b>\n{plan}", parse_mode=ParseMode.HTML)
    else:
        with logo_path.open("rb") as photo:
            await target.reply_photo(photo=photo, caption=caption, parse_mode=ParseMode.HTML)

    connected = account.has_session(uid)
    buttons = []
    if connected:
        buttons.append([InlineKeyboardButton("🤖 Создать канал автоматически", callback_data="auto_channel")])
    else:
        buttons.append([InlineKeyboardButton("🔗 Подключить аккаунт для авто-канала", callback_data="connect_account")])
    buttons.append([InlineKeyboardButton("📣 Посты", callback_data="need_posts")])
    buttons.append([InlineKeyboardButton("📺 Инструкция по каналу", callback_data="channel_menu")])
    names = ", ".join(brand.get("name_options", [])[1:4])
    await target.reply_text(
        f"Другие варианты названия: {names}\n\nЧто дальше?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _send_posts(update: Update, uid: int) -> None:
    data = storage.load_user(uid)
    posts = data.get("posts") or []
    target = _target(update)
    if not posts:
        await target.reply_text("Постов ещё нет — начни с «Запустить бизнес».", reply_markup=main_keyboard(account.has_session(uid)))
        return
    text = "\n\n————\n\n".join(f"<b>{p['title']}</b>\n{p['text']}" for p in posts[:4])
    if len(text) > 3500:
        text = text[:3490] + "…"
    await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard(account.has_session(uid)))


async def _channel_menu(update: Update, uid: int) -> None:
    data = storage.load_user(uid)
    brand = data.get("brand") or {}
    name = brand.get("brand_name", "Мой бизнес")
    target = _target(update)
    connected = account.has_session(uid)
    if connected and brand:
        await target.reply_text(
            f"Могу создать канал «{name}» сам: поставлю аватар, описание и выложу посты.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🤖 Создать канал сейчас", callback_data="auto_channel")]]
            ),
        )
        return
    text = (
        f"<b>Канал для {name}</b>\n\n"
        "Автоматически я создам его после подключения аккаунта (/connect).\n\n"
        "Вручную:\n"
        "1. Создай канал\n"
        f"2. Название: <code>{name}</code>\n"
        f"3. Описание: <code>{brand.get('channel_description', '')}</code>\n"
        "4. Аватар — лого выше\n"
        "5. Перешли сюда пост из канала\n"
    )
    if data.get("channel_id"):
        text += f"\n✅ Привязан: <code>{data['channel_id']}</code>"
    await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard(connected))


async def _auto_create_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: int) -> None:
    data = storage.load_user(uid)
    brand = data.get("brand")
    posts = data.get("posts") or []
    target = _target(update)

    if not brand:
        await target.reply_text("Сначала собери бренд: «Запустить бизнес».")
        return
    if not account.has_session(uid):
        await _start_account_login(update, update.effective_user)
        return

    await target.reply_text("Создаю канал, ставлю аватар и описание, публикую посты…")
    logo = Path(data.get("brand_folder") or ".") / "logo.png"
    bot_username = None
    try:
        me = await context.bot.get_me()
        bot_username = f"@{me.username}" if me.username else None
    except Exception:
        pass

    try:
        result = await account.create_channel_with_content(
            user_id=uid,
            title=brand["brand_name"],
            about=brand.get("channel_description") or brand.get("tagline") or "",
            logo_path=logo if logo.exists() else None,
            posts=[p["text"] for p in posts],
            bot_username=bot_username,
        )
    except account.AccountError as exc:
        await target.reply_text(str(exc))
        return
    except Exception as exc:
        log.exception("auto channel failed")
        await target.reply_text(f"Не получилось создать канал: {exc}")
        return

    data["channel_id"] = result["channel_id"]
    data["channel_title"] = result["title"]
    data["channel_invite"] = result.get("invite_link")
    data["stage"] = "launched"
    storage.save_user(uid, data)

    lines = [
        f"✅ Канал создан: <b>{result['title']}</b>",
        f"Аватар: {'поставлен' if result['logo_set'] else 'не удалось'}",
        f"Постов опубликовано: {result['posts_published']}",
        f"Бот админом: {'да' if result['bot_admin'] else 'нет'}",
    ]
    if result.get("invite_link"):
        lines.append(f"Ссылка: {result['invite_link']}")
    await target.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=main_keyboard(True))


async def _send_status(update: Update) -> None:
    uid = update.effective_user.id
    data = storage.load_user(uid)
    brand = data.get("brand") or {}
    profile = data.get("profile") or {}
    connected = account.has_session(uid)
    text = (
        "<b>Статус</b>\n"
        f"Аккаунт: {'✅ ' + str(data.get('account_name') or 'подключён') if connected else '❌ не подключён'}\n"
        f"MTProto ключи: {'есть' if account.is_configured() else 'нет (TG_API_ID/TG_API_HASH)'}\n"
        f"Этап: {data.get('stage')}\n"
        f"Ниша: {profile.get('domain_ru') or profile.get('domain') or '—'}\n"
        f"Идея: {(profile.get('idea') or '—')[:100]}\n"
        f"Бренд: {brand.get('brand_name') or '—'}\n"
        f"Канал: {data.get('channel_title') or data.get('channel_id') or 'нет'}\n"
        f"AI: {ai.backend_label()}"
    )
    await _target(update).reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard(connected))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Update error: %s", context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("Сбой на моей стороне. Попробуй ещё раз или /start")
        except Exception:
            pass
