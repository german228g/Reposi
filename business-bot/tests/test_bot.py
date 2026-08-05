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
