from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from typing import Any

from bot.config import Settings
from bot.receipt_template import render_html, render_plain

BRAND_NAME = "OFFICIALBRAND"


def send_receipt_email(settings: Settings, data: dict[str, Any], *, to_email: str) -> None:
    order_no = data["order_number"]
    plain = render_plain(data)
    html_body = render_html(data)

    message = EmailMessage()
    message["Subject"] = (
        f"Your OFFICIALBRAND Order Receipt - {order_no} [DEMO]"
    )
    message["From"] = formataddr((BRAND_NAME, settings.gmail_address))
    message["To"] = to_email
    message["Reply-To"] = settings.gmail_address
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain="gmail.com")
    message.set_content(plain)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(settings.gmail_address, settings.gmail_password)
        smtp.send_message(message)
