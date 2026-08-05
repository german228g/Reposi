"""Генерация постов под конкретную нишу и бренд-пакета."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .ai import nlu
from .ai.engine import BusinessAI


def _launch_post(brand: dict[str, Any]) -> str:
    geo = brand.get("geo")
    where = f" {nlu.locative(geo)}" if geo else ""
    return (
        f"🚀 {brand['brand_name']} открывается\n\n"
        f"{brand.get('tagline')}\n\n"
        f"Что делаем: {brand.get('offer')}{where}.\n"
        f"Для кого: {brand.get('audience')}\n\n"
        "Первым клиентам — лучшие условия. Напиши в личку, расскажу детали."
    )


def _offer_post(brand: dict[str, Any]) -> str:
    return (
        f"🔥 Открыт приём заказов\n\n"
        f"{brand.get('offer').capitalize()}. Аудитория: {brand.get('audience')}\n\n"
        "Как заказать:\n"
        "1. Напиши, что нужно\n"
        "2. Согласуем детали и срок\n"
        "3. Подтверждаешь — делаем\n\n"
        f"Пиши «ХОЧУ» — забронирую место в очереди {brand['brand_name']}."
    )


def _value_post(brand: dict[str, Any], tip: str) -> str:
    return (
        f"💡 Полезное про {brand.get('domain_ru')}\n\n"
        f"{tip}\n\n"
        "Сохрани, чтобы не потерять. А если нужна помощь — мы рядом.\n"
        f"— {brand['brand_name']}"
    )


def _story_post(brand: dict[str, Any]) -> str:
    return (
        f"Почему появился {brand['brand_name']}\n\n"
        f"{brand.get('story')}\n\n"
        "Здесь будем показывать работу без прикрас: процесс, результаты, честные цены."
    )


def _faq_post(brand: dict[str, Any]) -> str:
    tips = brand.get("tips") or []
    body = "\n".join(f"— {t}" for t in tips[:3]) or "— Пиши в личку, ответим на всё"
    return (
        f"❓ Частые вопросы про {brand.get('offer')}\n\n"
        f"{body}\n\n"
        "Остались вопросы? Задай в комментариях."
    )


def _plan_post(brand: dict[str, Any]) -> str:
    topics = brand.get("channel_topics") or ["польза", "кейсы", "офферы"]
    week = (topics * 3)[:7]
    return (
        f"📅 О чём будет канал {brand['brand_name']}\n\n"
        + "\n".join(f"{i+1}. {t.capitalize()}" for i, t in enumerate(week))
        + "\n\nПодписывайся, чтобы не пропустить запуск."
    )


def generate_posts(brand: dict[str, Any], ai: BusinessAI | None = None) -> list[dict[str, str]]:
    ai = ai or BusinessAI()
    tips = list(brand.get("tips") or [])
    random.shuffle(tips)
    tip1 = tips[0] if tips else "Начни с одного продукта и проверь спрос."
    tip2 = tips[1] if len(tips) > 1 else "Собирай отзывы с первого клиента."
    return [
        {"title": "Пост запуска", "text": _launch_post(brand)},
        {"title": "Оффер", "text": _offer_post(brand)},
        {"title": "Польза", "text": _value_post(brand, tip1)},
        {"title": "История бренда", "text": _story_post(brand)},
        {"title": "Частые вопросы", "text": _faq_post(brand)},
        {"title": "Польза #2", "text": _value_post(brand, tip2)},
        {"title": "О канале", "text": _plan_post(brand)},
    ]


def write_brand_package(brand: dict[str, Any], posts: list[dict[str, str]], folder: Path) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    plan = "\n".join(f"{i+1}. {s}" for i, s in enumerate(brand.get("launch_plan", [])))
    guide = f"""# {brand['brand_name']} — бренд-пакет

## Позиционирование
{brand.get('positioning')}

## Слоган
{brand.get('tagline')}

## Ниша
{brand.get('domain_ru')}

## Аудитория
{brand.get('audience')}

## Гео
{brand.get('geo') or 'не указано'}

## Оффер
{brand.get('offer')}

## Стиль
{brand.get('style')}

## Палитра
{', '.join(brand.get('palette', []))}

## Варианты названий
{', '.join(brand.get('name_options', []))}

## Описание канала
{brand.get('channel_description')}

## План запуска на 7 дней
{plan}

## Экспертные советы по нише
{chr(10).join('- ' + t for t in brand.get('tips', []))}

## Темы канала
{', '.join(brand.get('channel_topics', []))}
"""
    (folder / "BRAND.md").write_text(guide, encoding="utf-8")
    (folder / "posts.json").write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "brand.json").write_text(json.dumps(brand, ensure_ascii=False, indent=2), encoding="utf-8")
    posts_txt = "\n\n---\n\n".join(f"## {p['title']}\n\n{p['text']}" for p in posts)
    (folder / "POSTS.md").write_text(posts_txt, encoding="utf-8")
    return folder
