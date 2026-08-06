from __future__ import annotations

from email.message import EmailMessage

import pytest

from bot import config, mailer


def test_load_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("GMAIL_ADDRESS", "oficcialbrandeu@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    monkeypatch.setenv("DEFAULT_EMAIL_SUBJECT", "Test")

    settings = config.load_settings()
    assert settings.recipient_email == config.FIXED_RECIPIENT
    assert settings.recipient_email == "oficcialbrandeu@gmail.com"


def test_recipient_cannot_be_overridden_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    monkeypatch.setenv("RECIPIENT_EMAIL", "hacker@example.com")
    settings = config.load_settings()
    assert settings.recipient_email == "oficcialbrandeu@gmail.com"


def test_load_settings_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="Missing env vars"):
        config.load_settings()


def test_send_text_email(monkeypatch: pytest.MonkeyPatch) -> None:
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
            sent["from"] = message["From"]
            sent["subject"] = message["Subject"]
            sent["body"] = message.get_content()

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)

    settings = config.Settings(
        telegram_bot_token="t",
        gmail_address="oficcialbrandeu@gmail.com",
        gmail_password="secret",
        recipient_email="oficcialbrandeu@gmail.com",
        email_subject="Сообщение из Telegram",
    )
    mailer.send_text_email(settings, "привет", from_user="@user")

    assert sent["to"] == "oficcialbrandeu@gmail.com"
    assert sent["from"] == "oficcialbrandeu@gmail.com"
    assert "привет" in sent["body"]
    assert "@user" in sent["body"]
