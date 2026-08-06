from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# С этой почты уходят письма клиентам.
SENDER_GMAIL = "oficcialbrandeu@gmail.com"


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    gmail_address: str
    gmail_password: str
    email_subject: str
    admin_ids: frozenset[int]


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    gmail = os.getenv("GMAIL_ADDRESS", SENDER_GMAIL).strip() or SENDER_GMAIL
    password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    subject = os.getenv("DEFAULT_EMAIL_SUBJECT", "Сообщение из Telegram").strip()
    admin_raw = os.getenv("ADMIN_IDS", "").strip()
    admin_ids = frozenset(
        int(x) for x in admin_raw.split(",") if x.strip().isdigit()
    )

    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", token),
            ("GMAIL_APP_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    return Settings(
        telegram_bot_token=token,
        gmail_address=gmail,
        gmail_password=password,
        email_subject=subject,
        admin_ids=admin_ids,
    )
