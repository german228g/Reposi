"""Генератор обучающего корпуса бизнес-идей (RU/UA) для классификатора ниш."""

from __future__ import annotations

import random

from .domains import DOMAINS

TEMPLATES = [
    "хочу {kw}",
    "хочу заниматься {kw}",
    "планирую делать {kw}",
    "думаю открыть {kw}",
    "мечтаю про {kw}",
    "начинаю бизнес {kw}",
    "мой бизнес это {kw}",
    "буду продавать {kw}",
    "хочу зарабатывать на {kw}",
    "идея простая: {kw}",
    "{kw} на заказ",
    "{kw} в моем городе",
    "{kw} с доставкой",
    "{kw} онлайн",
    "{kw} для людей",
    "делаю {kw} уже год, хочу масштабировать",
    "у меня есть опыт в {kw}, хочу свой проект",
    "хочу открыть свое дело: {kw}",
    "маленький бизнес на {kw}",
    "запускаю проект про {kw}",
    "хочу канал про {kw}",
    "продаю {kw}, нужны клиенты",
    "хочу {kw} для подростков",
    "{kw} премиум сегмент",
    "{kw} недорого для студентов",
    "хочу {kw} без вложений",
]

GEO_SUFFIX = [
    "", " в Киеве", " в Москве", " в Одессе", " во Львове", " в Харькове",
    " в Украине", " в Минске", " в Алматы", " по всей стране", " онлайн",
    " в своем городе", " в Днепре", " в Варшаве",
]

AUDIENCE_SUFFIX = [
    "", " для 14-22", " для женщин 25-40", " для мужчин", " для мам",
    " для школьников", " для студентов", " для подростков 13-18",
    " для взрослых 30+", " для всех",
]

NOISE = [
    "", " бюджет минимальный", " бюджет 5000", " хочу быстро запуститься",
    " не знаю с чего начать", " нужна помощь с брендом", " хочу телеграм канал",
    " опыта нет", " опыт есть", " нужно название и лого",
]


def build_corpus(seed: int = 42, per_keyword: int = 6, per_class: int | None = None) -> list[tuple[str, str]]:
    """Сбалансированный корпус: одинаковое число примеров на каждую нишу.

    Ниша `general` в обучение не входит: её слова («бизнес», «идея») встречаются
    во всех формулировках и размывают модель. Она используется как fallback
    при низкой уверенности классификатора.
    """
    rnd = random.Random(seed)
    trainable = {k: v for k, v in DOMAINS.items() if k != "general"}

    if per_class is None:
        largest = max(
            len(v.get("keywords", [])) + len(v.get("products", [])) for v in trainable.values()
        )
        per_class = largest * per_keyword

    rows: list[tuple[str, str]] = []
    for domain, info in trainable.items():
        pool = list(info.get("keywords", [])) + list(info.get("products", []))
        if not pool:
            continue
        seen: set[str] = set()
        attempts = 0
        while len(seen) < per_class and attempts < per_class * 12:
            attempts += 1
            if rnd.random() < 0.75:
                kw = rnd.choice(pool)
                text = rnd.choice(TEMPLATES).format(kw=kw)
            else:
                a, b = rnd.sample(pool, 2) if len(pool) > 1 else (pool[0], pool[0])
                text = f"{a} и {b}"
            text += rnd.choice(GEO_SUFFIX)
            text += rnd.choice(AUDIENCE_SUFFIX)
            text += rnd.choice(NOISE)
            text = text.strip()
            if text in seen:
                continue
            seen.add(text)
            rows.append((text, domain))
    rnd.shuffle(rows)
    return rows


def split(rows: list[tuple[str, str]], test_ratio: float = 0.2, seed: int = 7):
    rnd = random.Random(seed)
    data = list(rows)
    rnd.shuffle(data)
    cut = int(len(data) * (1 - test_ratio))
    return data[:cut], data[cut:]
