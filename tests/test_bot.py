from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path

import pytest

from bot import config, mailer
from bot.storage import UserStore, is_valid_email


def test_load_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("GMAIL_ADDRESS", "oficcialbrandeu@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret")
    monkeypatch.setenv("ADMIN_IDS", "1,2")
    settings = config.load_settings()
    assert settings.gmail_address == "oficcialbrandeu@gmail.com"
    assert settings.admin_ids == frozenset({1, 2})


def test_load_settings_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="Missing env vars"):
        config.load_settings()


def test_send_to_client_email(monkeypatch: pytest.MonkeyPatch) -> None:
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
            sent["body"] = message.get_body(preferencelist=("plain",)).get_content()

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    settings = config.Settings(
        telegram_bot_token="t",
        gmail_address="oficcialbrandeu@gmail.com",
        gmail_password="secret",
        email_subject="OFFICIALBRAND",
        admin_ids=frozenset(),
    )
    mailer.send_text_email(
        settings, "привет друг", to_email="client@example.com", from_user="@user"
    )
    assert "oficcialbrandeu@gmail.com" in sent["from"]
    assert "OFFICIALBRAND" in sent["from"]
    assert sent["to"] == "client@example.com"
    assert sent["subject"] == "привет друг"
    assert "привет друг" in sent["body"]
    assert "Telegram" not in sent["body"]


def test_user_email_once(tmp_path: Path) -> None:
    store = UserStore(tmp_path / "users.json")
    assert store.get_email(10) is None
    assert store.set_email(10, "Client@Gmail.com") == "client@gmail.com"
    with pytest.raises(PermissionError):
        store.set_email(10, "other@gmail.com")
    assert store.set_email(10, "other@gmail.com", force=True) == "other@gmail.com"
    assert not is_valid_email("not-an-email")
