"""Тесты: точность модели, NLU, флоу диалога, MTProto-логика."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot.ai import nlu  # noqa: E402
from bot.ai.classifier import NaiveBayesClassifier, evaluate  # noqa: E402
from bot.ai.corpus import build_corpus, split  # noqa: E402
from bot.ai.engine import BusinessAI  # noqa: E402
from bot.posts_generator import generate_posts  # noqa: E402

REAL_IDEAS = [
    ("Продавать цветы в Украине для 14-22 киев", "flowers"),
    ("хочу торты на заказ во львове", "food"),
    ("делаю ботов для бизнеса онлайн", "digital"),
    ("маникюр на дому в Харькове", "beauty"),
    ("репетитор по математике для школьников", "edu"),
    ("хочу продавать чехлы для телефонов", "shop"),
    ("бренд одежды худи и футболки", "clothing"),
    ("организую туры в горы", "travel"),
    ("выгул собак и груминг", "pets"),
    ("клининг квартир после ремонта", "cleaning"),
]


@pytest.fixture(scope="module")
def ai() -> BusinessAI:
    engine = BusinessAI()
    assert engine.model is not None, "Модель не обучена: запусти scripts/train_ai.py"
    return engine


def test_model_holdout_accuracy():
    rows = build_corpus(per_keyword=6)
    train, test = split(rows)
    model = NaiveBayesClassifier()
    model.fit(train)
    metrics = evaluate(model, test)
    assert metrics["accuracy"] >= 0.85, metrics


@pytest.mark.parametrize("text,expected", REAL_IDEAS)
def test_real_ideas_detected(ai: BusinessAI, text: str, expected: str):
    assert ai.detect_domain(text) == expected


def test_nlu_extracts_geo_age_budget():
    facts = nlu.parse_idea("Продавать цветы в Украине для 14-22 киев бюджет 5000")
    assert facts["geo"] == "Киев"
    assert facts["age"] == "14–22 лет"
    assert facts["budget"] == "5000"


def test_locative_declension():
    assert nlu.locative("Киев") == "в Киеве"
    assert nlu.locative("Львов") == "во Львове"
    assert nlu.locative("онлайн") == "онлайн"


def test_no_repeat_questions_for_known_facts(ai: BusinessAI):
    """Если в идее есть возраст и город — про аудиторию не спрашиваем."""
    profile = ai.enrich_profile({"idea": "Продавать цветы в Украине для 14-22 киев"})
    question = ai.next_question(profile)
    assert question["key"] == "offer", question


def test_brand_uses_user_facts(ai: BusinessAI):
    profile = ai.enrich_profile({"idea": "Продавать цветы в Украине для 14-22 киев"})
    profile.update(offer="букеты", budget="5000", style="минимализм", name_pref="придумай")
    brand = ai.brand_strategy(profile)
    assert brand["domain"] == "flowers"
    assert "в Киеве" in brand["positioning"]
    assert "14–22" in brand["positioning"]
    assert brand["offer"] == "букеты"
    posts = generate_posts(brand, ai)
    assert len(posts) >= 5
    assert "в Киеве" in posts[0]["text"]


def test_custom_name_respected(ai: BusinessAI):
    names = ai.suggest_names("цветы", "минимализм", "Квіточка", "flowers")
    assert names[0] == "Квіточка"


def test_mtproto_channel_creation_sequence(tmp_path):
    os.environ["TG_API_ID"] = "123456"
    os.environ["TG_API_HASH"] = "abcdef"
    import importlib

    import bot.telegram_account as account

    importlib.reload(account)
    assert account.is_configured()

    account.save_session(424242, "FAKE")
    logo = tmp_path / "logo.png"
    from bot.logo_generator import generate_logo

    generate_logo("Тест", ["#7B2D4E", "#E8A0BF", "#F6E7EE"], "минимализм", logo)

    calls: list[str] = []
    channel = MagicMock()
    channel.id = -1001234567890
    channel.title = "Тест"

    class FakeClient:
        session = MagicMock(save=lambda: "S")

        async def connect(self):
            calls.append("connect")

        async def disconnect(self):
            calls.append("disconnect")

        async def is_user_authorized(self):
            return True

        async def upload_file(self, path):
            calls.append("upload_file")
            return "FILE"

        async def send_file(self, ch, path, caption=None):
            calls.append("send_file")

        async def send_message(self, ch, text):
            calls.append("send_message")

        async def get_entity(self, target):
            return "BOT"

        async def __call__(self, request):
            name = type(request).__name__
            calls.append(name)
            if name == "CreateChannelRequest":
                assert request.broadcast is True
                return MagicMock(chats=[channel])
            if name == "ExportChatInviteRequest":
                return MagicMock(link="https://t.me/+INVITE")
            return MagicMock()

    with patch.object(account, "_client", return_value=FakeClient()):
        result = asyncio.run(
            account.create_channel_with_content(
                user_id=424242,
                title="Тест",
                about="Описание канала",
                logo_path=logo,
                posts=["пост 1", "пост 2"],
                bot_username="@some_bot",
            )
        )

    account.drop_session(424242)
    assert result["posts_published"] == 2
    assert result["logo_set"] and result["bot_admin"]
    assert result["invite_link"] == "https://t.me/+INVITE"
    for expected in ("CreateChannelRequest", "EditPhotoRequest", "EditAdminRequest"):
        assert expected in calls


class _Recorder:
    """Мини-заготовка Telegram-объектов для проверки текстов бота."""

    def __init__(self, text: str = "", user_id: int = 4242):
        self.sent: list[str] = []
        self.photos: list[str] = []
        self.text = text
        self.user_id = user_id

        recorder = self

        class Chat:
            id = 1

            async def send_action(self, *a, **k):
                pass

            async def send_message(self, text, **k):
                recorder.sent.append(text)

        class Message:
            def __init__(self):
                self.text = recorder.text
                self.chat = Chat()
                self.forward_origin = None

            message_id = 10

            async def reply_text(self, text, **k):
                recorder.sent.append(text)

            async def reply_photo(self, photo=None, caption=None, **k):
                recorder.photos.append(caption or "")
                return SimpleNamespace(message_id=11)

            def get_bot(self):
                return SimpleNamespace()

            async def delete(self):
                pass

        self.callback_query = None
        self.message = Message()
        self.effective_chat = self.message.chat
        self.effective_message = self.message
        self.effective_user = SimpleNamespace(
            id=user_id, first_name="T", full_name="T", username="t"
        )

    @property
    def joined(self) -> str:
        return "\n".join(self.sent)


def test_client_never_sees_api_key_instructions(tmp_path, monkeypatch):
    """Обычному пользователю нельзя показывать инструкции про my.telegram.org."""
    import bot.config as config
    import bot.handlers as handlers
    import bot.storage as storage

    monkeypatch.setattr(storage, "USERS", tmp_path / "users")
    monkeypatch.setenv("ADMIN_USER_IDS", "1")  # клиент — не админ
    monkeypatch.delenv("TG_API_ID", raising=False)
    monkeypatch.delenv("TG_API_HASH", raising=False)
    assert not config.is_admin(4242)

    rec = _Recorder(user_id=4242)
    asyncio.run(handlers._start_account_login(rec, rec.effective_user))
    assert "my.telegram.org" not in rec.joined
    assert "api_hash" not in rec.joined.lower()
    assert "недоступно" in rec.joined


def test_admin_sees_setapi_hint(tmp_path, monkeypatch):
    import bot.handlers as handlers
    import bot.storage as storage

    monkeypatch.setattr(storage, "USERS", tmp_path / "users")
    monkeypatch.setenv("ADMIN_USER_IDS", "4242")
    monkeypatch.delenv("TG_API_ID", raising=False)
    monkeypatch.delenv("TG_API_HASH", raising=False)

    rec = _Recorder(user_id=4242)
    asyncio.run(handlers._start_account_login(rec, rec.effective_user))
    assert "/setapi" in rec.joined


def test_setapi_persists_keys_without_restart(tmp_path, monkeypatch):
    """Ключи применяются сразу: перезапуск бота не нужен."""
    import bot.config as config
    import bot.handlers as handlers
    import bot.telegram_account as account

    env_file = tmp_path / ".env"
    monkeypatch.setattr(config, "ENV_PATH", env_file)
    monkeypatch.setenv("ADMIN_USER_IDS", "4242")
    monkeypatch.delenv("TG_API_ID", raising=False)
    monkeypatch.delenv("TG_API_HASH", raising=False)
    assert not account.is_configured()

    async def fake_validate(api_id, api_hash):
        return True

    monkeypatch.setattr(account, "validate_credentials", fake_validate)

    rec = _Recorder(text="/setapi 1234567 abcdef0123456789abcdef0123456789", user_id=4242)
    asyncio.run(handlers.cmd_setapi(rec, SimpleNamespace()))

    assert account.is_configured()
    assert account.credentials() == (1234567, "abcdef0123456789abcdef0123456789")
    assert "TG_API_ID=1234567" in env_file.read_text(encoding="utf-8")
    assert "Ключи приняты" in rec.joined


def test_setapi_rejects_bad_keys(tmp_path, monkeypatch):
    import bot.config as config
    import bot.handlers as handlers
    import bot.telegram_account as account

    monkeypatch.setattr(config, "ENV_PATH", tmp_path / ".env")
    monkeypatch.setenv("ADMIN_USER_IDS", "4242")

    async def fake_validate(api_id, api_hash):
        return False

    monkeypatch.setattr(account, "validate_credentials", fake_validate)
    rec = _Recorder(text="/setapi 999 wrong", user_id=4242)
    asyncio.run(handlers.cmd_setapi(rec, SimpleNamespace()))
    assert "отклонил" in rec.joined


def test_setapi_denied_for_non_admin(tmp_path, monkeypatch):
    import bot.handlers as handlers

    monkeypatch.setenv("ADMIN_USER_IDS", "1")
    rec = _Recorder(text="/setapi 1 x", user_id=4242)
    asyncio.run(handlers.cmd_setapi(rec, SimpleNamespace()))
    assert "только владельцу" in rec.joined


def test_qr_png_is_valid_image():
    """QR рисуется из ссылки tg://login и остаётся читаемым PNG."""
    from io import BytesIO

    from PIL import Image

    import bot.telegram_account as account

    png = account.qr_png("tg://login?token=AQIDBAUGBwgJCg")
    image = Image.open(BytesIO(png))
    assert image.format == "PNG"
    assert image.width >= 200 and image.width == image.height


def test_qr_login_shows_code_and_waits(tmp_path, monkeypatch):
    """Подключение показывает QR и не просит вводить код цифрами."""
    import bot.handlers as handlers
    import bot.storage as storage
    import bot.telegram_account as account

    monkeypatch.setattr(storage, "USERS", tmp_path / "users")
    monkeypatch.setenv("TG_API_ID", "1234567")
    monkeypatch.setenv("TG_API_HASH", "abcdef")

    async def fake_start_qr(user_id):
        return account.qr_png("tg://login?token=TEST")

    monkeypatch.setattr(account, "start_qr_login", fake_start_qr)
    monkeypatch.setattr(handlers.asyncio, "create_task", lambda coro: coro.close())

    rec = _Recorder(user_id=4242)
    asyncio.run(handlers._start_qr_login(rec, rec.effective_user))

    assert rec.photos, "QR-код не отправлен"
    caption = rec.photos[0]
    assert "Устройства" in caption and "QR" in caption
    assert "цифр" not in caption.split("Ввод кода")[0].lower()
    assert storage.load_user(4242)["stage"] == "await_qr"


def test_typed_code_is_rejected_with_explanation(tmp_path, monkeypatch):
    """Если человек всё же прислал цифры — объясняем, а не пытаемся войти."""
    import bot.handlers as handlers
    import bot.storage as storage

    monkeypatch.setattr(storage, "USERS", tmp_path / "users")
    storage.save_user(4242, {"user_id": 4242, "stage": "await_qr", "profile": {}})

    rec = _Recorder(text="29218", user_id=4242)
    asyncio.run(handlers.on_message(rec, SimpleNamespace(bot=SimpleNamespace())))
    assert "аннулирует" in rec.joined
    assert storage.load_user(4242)["stage"] == "await_qr"


def test_qr_wait_refresh_and_success(monkeypatch, tmp_path):
    """Устаревший QR пересоздаётся, успешный вход сохраняет сессию."""
    import bot.telegram_account as account

    monkeypatch.setattr(account, "SESSIONS", tmp_path / "sessions")
    calls: list[str] = []

    class FakeQr:
        url = "tg://login?token=A"

        def __init__(self):
            self.waits = 0

        async def wait(self, timeout=None):
            self.waits += 1
            if self.waits == 1:
                raise asyncio.TimeoutError
            return SimpleNamespace(username="client", first_name="C")

        async def recreate(self):
            calls.append("recreate")
            self.url = "tg://login?token=B"

    class FakeClient:
        session = SimpleNamespace(save=lambda: "SESSION_STRING")

        async def disconnect(self):
            calls.append("disconnect")

    account._QR[4242] = account.QrSession(client=FakeClient(), qr=FakeQr())

    status, png = asyncio.run(account.wait_qr_login(4242, timeout=0.01))
    assert status == "refresh" and png and "recreate" in calls

    status, _ = asyncio.run(account.wait_qr_login(4242, timeout=0.01))
    assert status == "ok"
    assert account.load_session(4242) == "SESSION_STRING"
    assert not account.qr_login_active(4242)
    account.drop_session(4242)


def test_qr_2fa_password_completes_login(monkeypatch, tmp_path):
    import bot.telegram_account as account

    monkeypatch.setattr(account, "SESSIONS", tmp_path / "sessions")

    class FakeClient:
        session = SimpleNamespace(save=lambda: "SESSION_2FA")

        async def sign_in(self, password=None):
            assert password == "secret"
            return SimpleNamespace(username=None, first_name="Клиент")

        async def disconnect(self):
            pass

    account._QR[777] = account.QrSession(client=FakeClient(), qr=SimpleNamespace())
    name = asyncio.run(account.finish_qr_with_password(777, "secret"))
    assert name == "Клиент"
    assert account.load_session(777) == "SESSION_2FA"
    account.drop_session(777)


def test_dialog_flow_reaches_brand(tmp_path, monkeypatch):
    """Полный диалог: идея → 3 ответа → готовый бренд с постами."""
    import bot.handlers as handlers
    import bot.storage as storage

    monkeypatch.setattr(storage, "USERS", tmp_path / "users")
    monkeypatch.setattr(storage, "BRANDS", tmp_path / "brands")

    class FakeChat:
        id = 1

        async def send_action(self, *a, **k):
            pass

        async def send_message(self, *a, **k):
            pass

    class FakeMessage:
        def __init__(self, text):
            self.text = text
            self.chat = FakeChat()
            self.forward_origin = None

        async def reply_text(self, *a, **k):
            pass

        async def reply_photo(self, *a, **k):
            pass

    class FakeUpdate:
        callback_query = None

        def __init__(self, text):
            self.message = FakeMessage(text)
            self.effective_user = SimpleNamespace(id=31337, first_name="T", full_name="T", username="t")
            self.effective_chat = self.message.chat

    ctx = SimpleNamespace(
        bot=SimpleNamespace(
            send_chat_action=lambda *a, **k: asyncio.sleep(0),
            get_me=lambda: asyncio.sleep(0),
        )
    )

    async def run():
        for text in ["Продавать цветы в Украине для 14-22 киев", "букеты", "5000", "минимализм"]:
            await handlers.on_message(FakeUpdate(text), ctx)

    asyncio.run(run())
    data = storage.load_user(31337)
    assert data["stage"] == "branded"
    assert data["brand"]["domain"] == "flowers"
    assert len(data["posts"]) >= 5
    folder = Path(data["brand_folder"])
    assert (folder / "logo.png").exists()
    assert (folder / "BRAND.md").exists()
