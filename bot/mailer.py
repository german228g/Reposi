from __future__ import annotations

import smtplib
from email.message import EmailMessage

from bot.config import Settings


def send_text_email(settings: Settings, body: str, *, from_user: str) -> None:
    message = EmailMessage()
    message["Subject"] = settings.email_subject
    message["From"] = settings.gmail_address
    message["To"] = settings.recipient_email
    message.set_content(
        f"Сообщение из Telegram от {from_user}:\n\n{body}\n"
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(settings.gmail_address, settings.gmail_password)
        smtp.send_message(message)
