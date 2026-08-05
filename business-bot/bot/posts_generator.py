"""Генерация постов и дизайн-гайда."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .ai.engine import BusinessAI


def generate_posts(brand: dict[str, Any], ai: BusinessAI | None = None) -> list[dict[str, str]]:
    ai = ai or BusinessAI()
    templates = ai.base.get("post_templates", {})
    tip = random.choice(brand.get("tips") or ["Начни с малого и проверь спрос."])
    ctx = {
        "name": brand["brand_name"],
        "tagline": brand.get("tagline", ""),
        "offer": brand.get("offer", ""),
        "audience": brand.get("audience", ""),
        "tip": tip,
        "story": brand.get("story", ""),
    }
    posts: list[dict[str, str]] = []
    order = [("launch", "Запуск"), ("value", "Польза"), ("offer", "Оффер"), ("story", "История"), ("value", "Польза #2")]
    for key, title in order:
        opts = templates.get(key, ["{name}: новый пост"])
        text = random.choice(opts).format(**ctx)
        posts.append({"title": title, "text": text})
    # content plan tip
    topics = brand.get("channel_topics") or ["польза", "кейсы", "офферы"]
    posts.append(
        {
            "title": "План на неделю",
            "text": (
                f"Контент-план {brand['brand_name']} (7 дней):\n"
                + "\n".join(f"{i+1}. {t}" for i, t in enumerate((topics * 3)[:7]))
                + "\n\nПубликуй в одно и то же время — алгоритм и люди любят ритм."
            ),
        }
    )
    return posts


def write_brand_package(brand: dict[str, Any], posts: list[dict[str, str]], folder: Path) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    guide = f"""# {brand['brand_name']} — бренд-пакет

## Позиционирование
{brand.get('positioning')}

## Слоган
{brand.get('tagline')}

## Ниша
{brand.get('domain_ru')}

## Аудитория
{brand.get('audience')}

## Оффер
{brand.get('offer')}

## Стиль
{brand.get('style')}

## Палитра
{', '.join(brand.get('palette', []))}

## Варианты названий
{', '.join(brand.get('name_options', []))}

## Советы по запуску
{chr(10).join('- ' + t for t in brand.get('tips', []))}

## Темы канала
{', '.join(brand.get('channel_topics', []))}

## Как создать канал в Telegram
1. Telegram → New Channel → название «{brand['brand_name']}»
2. Описание: {brand.get('tagline')}
3. Поставь аватарку — файл logo.png из этой папки
4. Добавь бота администратором канала (право публиковать сообщения)
5. В боте нажми «Подключить канал» и перешли пост из канала / пришли @username

## Первые действия на 7 дней
1. Опубликовать пост запуска
2. Написать 20 потенциальным клиентам лично
3. Собрать 5 диалогов обратной связи
4. Выложить 3 полезных поста
5. Сделать первый оффер с дедлайном
"""
    (folder / "BRAND.md").write_text(guide, encoding="utf-8")
    (folder / "posts.json").write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "brand.json").write_text(json.dumps(brand, ensure_ascii=False, indent=2), encoding="utf-8")
    posts_txt = "\n\n---\n\n".join(f"## {p['title']}\n\n{p['text']}" for p in posts)
    (folder / "POSTS.md").write_text(posts_txt, encoding="utf-8")
    return folder
