"""Реальное подключение Telegram-аккаунта через MTProto (Telethon).

Бот входит в аккаунт пользователя по номеру и коду, после чего может:
- создать канал
- поставить аватарку и описание
- опубликовать посты
- добавить себя (бота) администратором канала

Требуются TG_API_ID и TG_API_HASH с https://my.telegram.org (раздел API development tools).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
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


async def start_login(phone: str) -> LoginStarted:
    """Отправляет код подтверждения на номер."""
    client = _client()
    await client.connect()
    try:
        sent = await client.send_code_request(phone)
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
    return LoginStarted(phone_code_hash=sent.phone_code_hash, session_string=session_string)


def _human_wait(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} сек"
    if seconds < 3600:
        return f"{seconds // 60} мин"
    return f"{seconds // 3600} ч"


async def resend_code(phone: str, phone_code_hash: str, session_string: str) -> LoginStarted:
    """Просит Telegram прислать код заново (например, звонком/SMS)."""
    client = _client(session_string)
    await client.connect()
    try:
        sent = await client(
            functions.auth.ResendCodeRequest(phone_number=phone, phone_code_hash=phone_code_hash)
        )
        return LoginStarted(
            phone_code_hash=sent.phone_code_hash, session_string=client.session.save()
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
    """Завершает вход. Возвращает (session_string, имя аккаунта, нужен_ли_пароль)."""
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
            raise AccountError("Код неверный. Проверь цифры и пришли снова.") from exc
        except PhoneCodeExpiredError as exc:
            raise AccountError("EXPIRED") from exc
        except PasswordHashInvalidError as exc:
            raise AccountError("Пароль не подошёл. Попробуй ещё раз.") from exc
        except FloodWaitError as exc:
            raise AccountError(f"Слишком много попыток. Подожди {_human_wait(exc.seconds)}.") from exc
        me = await client.get_me()
        title = me.username and f"@{me.username}" or (me.first_name or "аккаунт")
        return client.session.save(), title, False
    finally:
        await client.disconnect()


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
