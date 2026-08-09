"""Реальное подключение Telegram-аккаунта через MTProto (Telethon).

Вход с одного телефона: номер → код.
Telegram аннулирует код, если его прислали в чат «как есть» (29218) —
это антифишинг. Поэтому код принимаем только в «разбитом» виде: 2-9-2-1-8.
Дополнительно просим SMS вместо кода в приложении — так ещё надёжнее.

QR остаётся запасным вариантом для тех, у кого есть второй экран.

Ключи приложения (TG_API_ID / TG_API_HASH) задаются один раз владельцем сервиса.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from telethon import TelegramClient, functions, types
from telethon.errors import (
    ApiIdInvalidError,
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeEmptyError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberBannedError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
)
from telethon.sessions import StringSession

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "data" / "sessions"


class AccountError(Exception):
    """Ошибка, текст которой можно показать пользователю."""


@dataclass
class LoginStarted:
    phone_code_hash: str
    session_string: str
    via: str = "app"  # app | sms


def parse_login_code(text: str) -> str | None:
    """Достаёт код из «безопасного» формата.

    Принимаем только разбитый код — иначе Telegram блокирует вход:
      ✓ 2-9-2-1-8   2 9 2 1 8   2.9.2.1.8   a29218   29218x
      ✗ 29218  (сплошняком — детект антифишинга)
    """
    raw = (text or "").strip()
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 5 or len(digits) > 6:
        return None
    # сплошные 5–6 цифр без разделителей/букв — отказываем заранее
    if re.fullmatch(r"\d{5,6}", raw):
        raise AccountError("BARE_CODE")
    # есть разделители или буквы вокруг — ок
    if re.search(r"[\s\-–—\.·,/|_]", raw) or re.search(r"[A-Za-zА-Яа-яЁё]", raw):
        return digits
    raise AccountError("BARE_CODE")


def format_code_hint(code: str = "29218") -> str:
    return "-".join(code)


def _human_wait(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} сек"
    if seconds < 3600:
        return f"{seconds // 60} мин"
    return f"{seconds // 3600} ч"


async def start_login(phone: str) -> LoginStarted:
    """Отправляет код и сразу пытается переключить доставку на SMS."""
    client = _client()
    await client.connect()
    via = "app"
    try:
        sent = await client.send_code_request(phone)
        phone_code_hash = sent.phone_code_hash
        # Повторная отправка часто уходит SMS — код из SMS можно вводить проще
        try:
            resent = await client(
                functions.auth.ResendCodeRequest(
                    phone_number=phone, phone_code_hash=phone_code_hash
                )
            )
            phone_code_hash = resent.phone_code_hash
            via = "sms"
        except Exception:
            log.info("SMS resend недоступен, остаёмся на коде в приложении")
            via = "app"
    except PhoneNumberInvalidError as exc:
        raise AccountError("Такого номера не существует. Формат: +380971234567") from exc
    except PhoneNumberBannedError as exc:
        raise AccountError("Этот номер заблокирован в Telegram.") from exc
    except FloodWaitError as exc:
        raise AccountError(
            f"Telegram просит подождать {_human_wait(exc.seconds)} перед следующей попыткой."
        ) from exc
    except ApiIdInvalidError as exc:
        raise AccountError("SERVICE_NOT_CONFIGURED") from exc
    finally:
        session_string = client.session.save()
        await client.disconnect()
    return LoginStarted(phone_code_hash=phone_code_hash, session_string=session_string, via=via)


async def resend_code(phone: str, phone_code_hash: str, session_string: str) -> LoginStarted:
    client = _client(session_string)
    await client.connect()
    try:
        sent = await client(
            functions.auth.ResendCodeRequest(
                phone_number=phone, phone_code_hash=phone_code_hash
            )
        )
        return LoginStarted(
            phone_code_hash=sent.phone_code_hash,
            session_string=client.session.save(),
            via="sms",
        )
    except FloodWaitError as exc:
        raise AccountError(f"Подожди {_human_wait(exc.seconds)} — Telegram ограничил попытки.") from exc
    finally:
        await client.disconnect()


async def complete_login(
    phone: str,
    code: str,
    phone_code_hash: str,
    session_string: str,
    password: str | None = None,
) -> tuple[str, str, bool]:
    """Возвращает (session_string, имя, нужен_ли_пароль)."""
    client = _client(session_string)
    await client.connect()
    try:
        try:
            if password:
                await client.sign_in(password=password)
            else:
                await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        except SessionPasswordNeededError:
            return client.session.save(), "", True
        except (PhoneCodeInvalidError, PhoneCodeEmptyError) as exc:
            # Telegram часто маскирует антифишинг-блок под «неверный/истёкший» код
            raise AccountError("CODE_REJECTED") from exc
        except PhoneCodeExpiredError as exc:
            raise AccountError("EXPIRED") from exc
        except PasswordHashInvalidError as exc:
            raise AccountError("Пароль не подошёл. Попробуй ещё раз.") from exc
        except FloodWaitError as exc:
            raise AccountError(f"Слишком много попыток. Подожди {_human_wait(exc.seconds)}.") from exc
        me = await client.get_me()
        return client.session.save(), _title_of(me), False
    finally:
        await client.disconnect()


@dataclass
class QrSession:
    """Живая MTProto-сессия на время ожидания сканирования QR."""

    client: object
    qr: object
    account_title: str = ""
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


# QR-логины держим в памяти: клиент должен оставаться подключённым до сканирования
_QR: dict[int, QrSession] = {}


def qr_png(url: str, size: int = 8) -> bytes:
    """Рисует QR-код из ссылки tg://login."""
    import qrcode

    qr = qrcode.QRCode(border=2, box_size=size, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#0D1B2A", back_color="white").convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


async def start_qr_login(user_id: int) -> bytes:
    """Создаёт QR для входа и возвращает картинку."""
    await cancel_qr_login(user_id)
    client = _client()
    await client.connect()
    try:
        qr = await client.qr_login()
    except ApiIdInvalidError as exc:
        await client.disconnect()
        raise AccountError("SERVICE_NOT_CONFIGURED") from exc
    except Exception:
        await client.disconnect()
        raise
    _QR[user_id] = QrSession(client=client, qr=qr)
    return qr_png(qr.url)


async def wait_qr_login(user_id: int, timeout: float = 25.0) -> tuple[str, bytes | None]:
    """Ждёт сканирование.

    Возвращает статус и, для «refresh», новую картинку QR:
    - ("ok", None)        — вход выполнен, сессия сохранена
    - ("password", None)  — нужен облачный пароль (2FA)
    - ("refresh", png)    — QR устарел, показать новый
    - ("gone", None)      — сессии больше нет (отмена/перезапуск)
    """
    session = _QR.get(user_id)
    if session is None:
        return "gone", None

    async with session.lock:
        try:
            user = await session.qr.wait(timeout=timeout)
        except asyncio.TimeoutError:
            try:
                await session.qr.recreate()
            except Exception:
                log.warning("qr recreate failed", exc_info=True)
                await cancel_qr_login(user_id)
                return "gone", None
            return "refresh", qr_png(session.qr.url)
        except SessionPasswordNeededError:
            return "password", None
        except Exception:
            log.exception("qr wait failed")
            await cancel_qr_login(user_id)
            return "gone", None

    title = _title_of(user)
    save_session(user_id, session.client.session.save())
    session.account_title = title
    await cancel_qr_login(user_id, keep_title=True)
    return "ok", None


async def finish_qr_with_password(user_id: int, password: str) -> str:
    """Завершает QR-вход, если на аккаунте включён облачный пароль."""
    session = _QR.get(user_id)
    if session is None:
        raise AccountError("Сессия входа истекла. Начни заново: /connect")
    try:
        user = await session.client.sign_in(password=password)
    except PasswordHashInvalidError as exc:
        raise AccountError("Пароль не подошёл. Пришли ещё раз.") from exc
    title = _title_of(user)
    save_session(user_id, session.client.session.save())
    await cancel_qr_login(user_id, keep_title=True)
    return title


async def cancel_qr_login(user_id: int, keep_title: bool = False) -> None:
    session = _QR.pop(user_id, None)
    if session is None:
        return
    try:
        await session.client.disconnect()
    except Exception:
        log.debug("qr client disconnect failed", exc_info=True)


def qr_login_active(user_id: int) -> bool:
    return user_id in _QR


def _title_of(user) -> str:
    if user is None:
        return "аккаунт"
    username = getattr(user, "username", None)
    if username:
        return f"@{username}"
    return getattr(user, "first_name", None) or "аккаунт"


def credentials() -> tuple[int, str] | None:
    api_id = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    if not api_id or not api_hash or not api_id.isdigit():
        return None
    return int(api_id), api_hash


def is_configured() -> bool:
    return credentials() is not None


def session_path(user_id: int) -> Path:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    return SESSIONS / f"{user_id}.session"


def has_session(user_id: int) -> bool:
    path = session_path(user_id)
    return path.exists() and bool(path.read_text(encoding="utf-8").strip())


def save_session(user_id: int, session_string: str) -> None:
    path = session_path(user_id)
    path.write_text(session_string, encoding="utf-8")
    path.chmod(0o600)


def load_session(user_id: int) -> str | None:
    if not has_session(user_id):
        return None
    return session_path(user_id).read_text(encoding="utf-8").strip()


def drop_session(user_id: int) -> None:
    path = session_path(user_id)
    if path.exists():
        path.unlink()


def _client(session_string: str | None = None) -> TelegramClient:
    creds = credentials()
    if creds is None:
        raise AccountError("SERVICE_NOT_CONFIGURED")
    api_id, api_hash = creds
    return TelegramClient(
        StringSession(session_string or None),
        api_id,
        api_hash,
        device_model="Business Launch AI",
        system_version="1.0",
        app_version="1.0",
    )


async def validate_credentials(api_id: int, api_hash: str) -> bool:
    """Проверяет, что ключи приложения рабочие (без входа в аккаунт)."""
    client = TelegramClient(StringSession(), api_id, api_hash)
    try:
        await client.connect()
        # Любой безобидный запрос к API: неверные ключи отдадут ApiIdInvalidError
        await client(functions.help.GetNearestDcRequest())
        return True
    except ApiIdInvalidError:
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def account_name(user_id: int) -> str | None:
    session_string = load_session(user_id)
    if not session_string:
        return None
    client = _client(session_string)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            return None
        me = await client.get_me()
        return me.username and f"@{me.username}" or (me.first_name or "аккаунт")
    finally:
        await client.disconnect()


async def create_channel_with_content(
    user_id: int,
    title: str,
    about: str,
    logo_path: Path | None,
    posts: list[str],
    bot_username: str | None = None,
) -> dict:
    """Создаёт канал от имени пользователя, ставит аватар/описание и публикует посты."""
    session_string = load_session(user_id)
    if not session_string:
        raise AccountError("Аккаунт не подключён. Нажми «Подключить аккаунт».")

    client = _client(session_string)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            drop_session(user_id)
            raise AccountError("Сессия истекла. Подключи аккаунт заново: /connect")

        result = await client(
            functions.channels.CreateChannelRequest(
                title=title[:128],
                about=about[:255],
                megagroup=False,
                broadcast=True,
            )
        )
        channel = result.chats[0]

        if logo_path and Path(logo_path).exists():
            uploaded = await client.upload_file(str(logo_path))
            await client(
                functions.channels.EditPhotoRequest(
                    channel=channel,
                    photo=types.InputChatUploadedPhoto(file=uploaded),
                )
            )

        posted = 0
        for text in posts:
            if not text:
                continue
            if posted == 0 and logo_path and Path(logo_path).exists():
                await client.send_file(channel, str(logo_path), caption=text[:1024])
            else:
                await client.send_message(channel, text[:4000])
            posted += 1

        admin_added = False
        if bot_username:
            try:
                bot_entity = await client.get_entity(bot_username)
                await client(
                    functions.channels.EditAdminRequest(
                        channel=channel,
                        user_id=bot_entity,
                        admin_rights=types.ChatAdminRights(
                            post_messages=True,
                            edit_messages=True,
                            delete_messages=True,
                            change_info=True,
                            invite_users=True,
                        ),
                        rank="bot",
                    )
                )
                admin_added = True
            except Exception:
                log.warning("Не удалось добавить бота админом", exc_info=True)

        invite = None
        try:
            exported = await client(
                functions.messages.ExportChatInviteRequest(peer=channel)
            )
            invite = getattr(exported, "link", None)
        except Exception:
            log.warning("Не удалось получить ссылку-приглашение", exc_info=True)

        return {
            "channel_id": channel.id,
            "title": channel.title,
            "invite_link": invite,
            "posts_published": posted,
            "bot_admin": admin_added,
            "logo_set": bool(logo_path and Path(logo_path).exists()),
        }
    finally:
        await client.disconnect()


async def publish_to_channel(user_id: int, channel_id: int, text: str, photo: Path | None = None) -> None:
    session_string = load_session(user_id)
    if not session_string:
        raise AccountError("Аккаунт не подключён.")
    client = _client(session_string)
    await client.connect()
    try:
        entity = await client.get_entity(types.PeerChannel(channel_id))
        if photo and Path(photo).exists():
            await client.send_file(entity, str(photo), caption=text[:1024])
        else:
            await client.send_message(entity, text[:4000])
    finally:
        await client.disconnect()
