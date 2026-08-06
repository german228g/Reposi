from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path

import pytest

from bot import config, mailer
from bot.form_steps import is_valid_date, is_valid_email, validate_step
from bot.receipt_template import email_subject, format_preview, generate_order_number, render_html
from bot.storage import UserStore


def test_load_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    settings = config.load_settings()
    assert settings.gmail_address == config.SENDER_GMAIL


def test_form_validation() -> None:
    assert is_valid_email("a@b.com")
    assert not is_valid_email("bad")
    assert is_valid_date("2024-01-15")
    assert validate_step("order_date", "bad") is not None
    assert validate_step("product_image_url", "https://x.com/a.png") is None


def test_preview_matches_template_style() -> None:
    data = {
        "name": "John",
        "surname": "Doe",
        "product_name": "Iphone 13",
        "order_number": "W30514310",
        "product_price": "$800",
        "order_date": "1999-12-12",
        "street": "STREET 113",
        "city": "CITY",
        "state": "KIEV",
        "zip_code": "9000",
        "phone": "+380 333333333",
        "product_image_url": "https://example.com/p.png",
    }
    preview = format_preview(data)
    html_body = render_html(data)
    assert "🍎 Apple Receipt Preview" in preview
    assert "Send Receipt" in preview
    assert email_subject(data) == "Your Apple Order Receipt - W30514310"
    assert "Thank you for your order." in html_body
    assert "Items to be" in html_body
    assert "EXPRESS SHIPPING" in html_body
    assert "Billing and" in html_body
    assert "bgcolor=\"#f5f5f7\"" in html_body
    assert 'align="center"' in html_body
    assert "DEMO / NOT A REAL RECEIPT" in html_body


def test_send_receipt_email(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict = {}

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, user, password):
            sent["login"] = (user, password)

        def send_message(self, message: EmailMessage):
            sent["to"] = message["To"]
            sent["subject"] = message["Subject"]
            sent["body"] = message.get_body(preferencelist=("plain",)).get_content()

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    settings = config.Settings(
        telegram_bot_token="t",
        gmail_address="oficcialbrandeu@gmail.com",
        gmail_password="secret",
        email_subject="OFFICIALBRAND",
        admin_ids=frozenset(),
    )
    data = {
        "name": "A",
        "surname": "B",
        "product_name": "Item",
        "order_number": generate_order_number(),
        "product_price": "$50",
        "order_date": "2024-02-02",
        "street": "S",
        "city": "C",
        "state": "K",
        "zip_code": "1",
        "phone": "+380",
        "product_image_url": "https://example.com/i.png",
    }
    mailer.send_receipt_email(settings, data, to_email="client@example.com")
    assert sent["to"] == "client@example.com"
    assert sent["subject"] == email_subject(data)
    assert "DEMO / NOT A REAL RECEIPT" in sent["body"]


def test_user_email_once(tmp_path: Path) -> None:
    store = UserStore(tmp_path / "users.json")
    assert store.set_email(10, "Client@Gmail.com") == "client@gmail.com"
    with pytest.raises(PermissionError):
        store.set_email(10, "other@gmail.com")
