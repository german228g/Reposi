from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Фиксированная почта. Менять только через поддержку (этот файл / .env отправителя).
FIXED_RECIPIENT = "oficcialbrandeu@gmail.com"


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    gmail_address: str
    gmail_password: str
    recipient_email: str
    email_subject: str


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    gmail = os.getenv("GMAIL_ADDRESS", FIXED_RECIPIENT).strip() or FIXED_RECIPIENT
    password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    subject = os.getenv("DEFAULT_EMAIL_SUBJECT", "Сообщение из Telegram").strip()

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
        recipient_email=FIXED_RECIPIENT,
        email_subject=subject,
    )
