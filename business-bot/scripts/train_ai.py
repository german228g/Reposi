#!/usr/bin/env python3
"""Автообучение локального Business Pro engine.

Не обучает нейросеть с нуля (это требует GPU-кластер), а:
1) расширяет knowledge-базу экспертными кейсами
2) добавляет tips по нишам
3) сохраняет few-shot примеры для RAG/промптов
4) опционально готовит JSONL под LoRA (если позже подключишь Ollama/Unsloth)

Запуск:
  python scripts/train_ai.py
  python scripts/train_ai.py --rounds 5
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "bot" / "ai" / "knowledge"
BASE = KNOWLEDGE / "base.json"
TRAINED = KNOWLEDGE / "trained.json"
DATASET = KNOWLEDGE / "finetune_dataset.jsonl"

SYNTHETIC_CASES = [
    {
        "domain": "food",
        "input": "Хочу печь капкейки и продавать в школе",
        "output": "Стартуй с 3 вкусов и pre-order в классных чатах. Себестоимость ×3. Фото до/после выпечки каждый день. Первый KPI: 20 заказов за 7 дней.",
        "tip": "Школьные/универские чаты — бесплатный канал дистрибуции для еды",
    },
    {
        "domain": "edu",
        "input": "Хочу вести курсы по Python для новичков",
        "output": "Сделай бесплатный мини-урок 20 минут + платный пакет на 2 недели. Кейс: «напишешь своего Telegram-бота». Цена старта ниже рынка, цель — 5 отзывов.",
        "tip": "Продавай результат проекта, а не количество часов",
    },
    {
        "domain": "digital",
        "input": "Хочу AI-бота для малого бизнеса",
        "output": "MVP: один сценарий (ответы на FAQ + сбор заявок). Возьми 3 бизнесов из знакомых бесплатно ради кейсов, потом пакет Старт/Про. Дистрибуция — чаты предпринимателей.",
        "tip": "Кейсы важнее фич на старте SaaS/бота",
    },
    {
        "domain": "beauty",
        "input": "Делаю маникюр на дому",
        "output": "Портфолио из 10 работ, прайс пакетами, запись через форму. Контент: процесс + результат + уход. Бартер с микроблогерами района.",
        "tip": "До/после — главный актив бьюти-бизнеса",
    },
    {
        "domain": "shop",
        "input": "Хочу магазин мерча",
        "output": "1–2 дизайна, pre-order без склада, канал с lookbook. Первый дроп — лимитированная серия 30 штук с дедлайном.",
        "tip": "Лимитированный дроп создаёт срочность лучше вечной витрины",
    },
    {
        "domain": "services",
        "input": "Хочу SMM-услуги",
        "output": "Упакуй 3 пакета. Сделай 1 бесплатный аудит в неделю ради кейса. В постах показывай прирост охватов цифрами.",
        "tip": "Пакеты и цифры результатов продают услуги лучше «я умею SMM»",
    },
    {
        "domain": "fitness",
        "input": "Онлайн-тренировки для новичков",
        "output": "21-дневный челлендж + ежедневные чек-ины в Telegram. Витрина трансформаций. Старт с низкой цены и сильным комьюнити.",
        "tip": "Челлендж с чек-инами даёт удержание лучше разовых тренировок",
    },
    {
        "domain": "content",
        "input": "Хочу Telegram-канал про стартапы",
        "output": "Выбери узкий угол (например стартапы до 18 / без инвестиций). Контент-план 14 дней. Монетизация после 1–2к: свои гайды и платный чат.",
        "tip": "Узкая точка зрения растёт быстрее общего блога",
    },
    {
        "domain": "general",
        "input": "Не знаю какой бизнес начать",
        "output": "Выпиши навыки + аудиторию рядом с тобой + что люди уже просят. Проверь спрос 20 разговорами. Выбери идею, где первый клиент возможен за 7 дней.",
        "tip": "Идея без пути к первому клиенту за неделю — слишком ранняя",
    },
    {
        "domain": "digital",
        "input": "Сделать приложение для привычек",
        "output": "Не начинай с app store. Сначала Telegram-бот + таблица прогресса. Собери 50 waitlist. Плати только когда 10 человек готовы платить.",
        "tip": "Валидируй digital-продукт в Telegram до дорогой разработки",
    },
]


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def train(rounds: int = 3) -> None:
    base = load_json(BASE)
    trained = load_json(TRAINED) or {"examples": [], "tips_extra": {}, "rounds": 0}

    examples = list(trained.get("examples", []))
    tips_extra = dict(trained.get("tips_extra", {}))

    for r in range(rounds):
        batch = SYNTHETIC_CASES.copy()
        random.shuffle(batch)
        for case in batch:
            examples.append(
                {
                    "domain": case["domain"],
                    "input": case["input"],
                    "output": case["output"],
                    "trained_round": trained.get("rounds", 0) + r + 1,
                }
            )
            tips_extra.setdefault(case["domain"], [])
            if case["tip"] not in tips_extra[case["domain"]]:
                tips_extra[case["domain"]].append(case["tip"])

        # distill tips from base domains into reinforced set
        for domain, info in base.get("domains", {}).items():
            tips_extra.setdefault(domain, [])
            for tip in info.get("tips", []):
                reinforced = f"[pro] {tip}"
                if reinforced not in tips_extra[domain] and random.random() < 0.35:
                    tips_extra[domain].append(reinforced)

    # dedupe examples by input
    uniq = {}
    for ex in examples:
        uniq[ex["input"]] = ex
    examples = list(uniq.values())

    trained = {
        "version": "1.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "rounds": int(trained.get("rounds", 0)) + rounds,
        "examples_count": len(examples),
        "examples": examples,
        "tips_extra": tips_extra,
        "note": "Локальное усиление knowledge/RAG. Для настоящей LoRA используй finetune_dataset.jsonl",
    }
    TRAINED.write_text(json.dumps(trained, ensure_ascii=False, indent=2), encoding="utf-8")

    # JSONL for optional LoRA later
    with DATASET.open("w", encoding="utf-8") as f:
        system = (KNOWLEDGE / "system_prompt.txt").read_text(encoding="utf-8")
        for ex in examples:
            row = {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": ex["input"]},
                    {"role": "assistant", "content": ex["output"]},
                ]
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # update base trained_at marker
    base["trained_at"] = trained["trained_at"]
    base["examples_count"] = trained["examples_count"]
    BASE.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Обучение завершено: {trained['examples_count']} примеров, раундов всего {trained['rounds']}")
    print(f"   → {TRAINED}")
    print(f"   → {DATASET}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=3, help="Сколько проходов автообучения")
    args = parser.parse_args()
    train(rounds=args.rounds)


if __name__ == "__main__":
    main()
