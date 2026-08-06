from __future__ import annotations

import html
import re
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from bot.config import Settings

BRAND_NAME = "OFFICIALBRAND"


def _subject_from_body(body: str, fallback: str) -> str:
    clean = re.sub(r"\s+", " ", body).strip()
    if not clean:
        return fallback
    if len(clean) <= 60:
        return clean
    return clean[:57].rstrip() + "…"


def send_text_email(
    settings: Settings,
    body: str,
    *,
    to_email: str,
    from_user: str = "",
) -> None:
    plain = body.strip() + "\n"
    safe = html.escape(plain).replace("\n", "<br>\n")
    html_body = f"""<!DOCTYPE html>
<html>
  <body style="margin:0;padding:24px;font-family:Arial,Helvetica,sans-serif;color:#111;background:#fff;">
    <div style="max-width:560px;margin:0 auto;line-height:1.5;font-size:16px;">
      <p style="margin:0 0 16px 0;">{safe}</p>
      <p style="margin:24px 0 0 0;font-size:12px;color:#888;">{html.escape(BRAND_NAME)}</p>
    </div>
  </body>
</html>
"""

    message = EmailMessage()
    message["Subject"] = _subject_from_body(body, settings.email_subject)
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
