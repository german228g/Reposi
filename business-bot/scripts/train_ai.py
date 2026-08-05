#!/usr/bin/env python3
"""Обучение AI: классификатор ниш + экспертные примеры.

Что реально происходит:
1. Генерируется корпус бизнес-идей на RU/UA по всем нишам (десятки тысяч примеров)
2. Обучается Multinomial Naive Bayes на словах, биграммах и символьных триграммах
3. Считается точность на отложенной выборке (train/test split) + по каждой нише
4. Проверяются ручные контрольные фразы (реальные формулировки людей)
5. Модель сохраняется в knowledge/model.json, примеры — в trained.json

Запуск:
  python scripts/train_ai.py
  python scripts/train_ai.py --rounds 5 --per-keyword 10
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot.ai.classifier import NaiveBayesClassifier, evaluate  # noqa: E402
from bot.ai.corpus import build_corpus, split  # noqa: E402
from bot.ai.domains import DOMAINS  # noqa: E402
from bot.ai.engine import BusinessAI  # noqa: E402

KNOWLEDGE = ROOT / "bot" / "ai" / "knowledge"
TRAINED = KNOWLEDGE / "trained.json"
DATASET = KNOWLEDGE / "finetune_dataset.jsonl"
REPORT = KNOWLEDGE / "train_report.json"

# Контрольные фразы: как реально пишут люди (проверка после обучения)
SANITY = [
    ("Продавать цветы в Украине", "flowers"),
    ("хочу букеты для 14-22 киев", "flowers"),
    ("доставка цветов по Одессе", "flowers"),
    ("хочу открыть кофейню", "food"),
    ("торты на заказ для дней рождения", "food"),
    ("делаю маникюр на дому", "beauty"),
    ("наращивание ресниц в Харькове", "beauty"),
    ("репетитор по математике онлайн", "edu"),
    ("хочу курсы английского для школьников", "edu"),
    ("делаю телеграм ботов для бизнеса", "digital"),
    ("делаю ботов для бизнеса онлайн", "digital"),
    ("разработка сайтов и лендингов", "digital"),
    ("хочу продавать букеты в киеве", "flowers"),
    ("хочу шить одежду на заказ", "clothing"),
    ("делаю сайты для малого бизнеса", "digital"),
    ("продаю кофе с собой", "food"),
    ("хочу учить детей рисованию", "edu"),
    ("сдаю квартиры туристам", "travel"),
    ("продаю зоотовары для кошек", "pets"),
    ("хочу продавать чехлы для телефонов", "shop"),
    ("бренд одежды худи и футболки", "clothing"),
    ("вяжу игрушки своими руками", "handmade"),
    ("свечи ручной работы на подарок", "handmade"),
    ("настраиваю рекламу и веду соцсети", "smm"),
    ("онлайн тренировки для похудения", "fitness"),
    ("хочу канал с мемами и обзорами", "content"),
    ("свадебный фотограф в Киеве", "photo"),
    ("ремонт телефонов и замена экрана", "repair"),
    ("автомойка и детейлинг", "auto"),
    ("выгул собак и груминг", "pets"),
    ("оформление шарами на день рождения", "events"),
    ("организую туры в горы", "travel"),
    ("клининг квартир после ремонта", "cleaning"),
    ("прокачка аккаунтов в играх", "gaming"),
    ("бухгалтерия для фоп", "finance"),
]

EXPERT_EXAMPLES = [
    {
        "domain": "flowers",
        "input": "Хочу продавать цветы, бюджет маленький",
        "output": "Не арендуй точку сразу: работай на предзаказ из дома. Закупай у оптовика 2 раза в неделю малыми партиями, собери 3 пакета (мини/классика/премиум) и договорись с курьером на доставку за 2 часа. Первые заказы бери в чатах района и у знакомых под праздники.",
        "tip": "В цветах решает свежесть и скорость доставки, а не ассортимент",
    },
    {
        "domain": "flowers",
        "input": "Как продавать букеты подросткам и молодёжи 14-22",
        "output": "Молодёжь покупает цветы под поводы: свидание, извинение, выпускной, 8 марта. Сделай дешёвый мини-букет до 300₴, красивую упаковку и оплату по ссылке без звонков. Заходи в TikTok с видео сборки — там твоя аудитория.",
        "tip": "Для молодёжи важнее цена, упаковка и заказ без звонка",
    },
    {
        "domain": "food",
        "input": "Хочу печь торты дома и продавать",
        "output": "Стартуй с 3 вкусов и фиксированных размеров, считай себестоимость до грамма. Возьми предзаказ на выходные, чтобы не выбрасывать продукты. Фото разреза торта продаёт лучше внешнего вида.",
        "tip": "В кондитерке фото разреза важнее фото украшения",
    },
    {
        "domain": "beauty",
        "input": "Маникюр на дому, нет клиентов",
        "output": "Собери 10 работ в портфолио, поставь 3 пакета вместо прайса по услугам и запусти акцию «первый визит -30% за отзыв». Раздай визитки в соседних домах и попроси клиенток отмечать тебя в сторис.",
        "tip": "Первые клиенты в бьюти приходят из соседних домов и сарафана",
    },
    {
        "domain": "edu",
        "input": "Хочу учить английскому онлайн",
        "output": "Продавай результат: «заговоришь на бытовые темы за 8 недель». Сделай бесплатный вводный урок 20 минут, собери 5 учеников по цене ниже рынка и запиши их результаты в кейсы. Дальше поднимай цену и веди группы.",
        "tip": "В обучении цена растёт от кейсов, а не от стажа",
    },
    {
        "domain": "digital",
        "input": "Делаю ботов, где брать заказы",
        "output": "Сделай 2 демо-бота под конкретные нишы (запись в салон, приём заявок) и покажи 30-секундное видео. Пиши в чаты предпринимателей с готовым решением их задачи, а не с «делаю ботов». Первые 3 проекта — по низкой цене ради кейсов.",
        "tip": "Digital продаётся через демо, а не через список технологий",
    },
    {
        "domain": "clothing",
        "input": "Хочу свой бренд одежды",
        "output": "Начни с одной модели в 3 цветах и работай по предзаказу. Найди небольшой цех на 30–50 единиц, сделай реальную размерную сетку с замерами и сними фото на живых людях. Дроп с дедлайном продаёт лучше постоянной витрины.",
        "tip": "Один товар в трёх цветах вместо коллекции на старте",
    },
    {
        "domain": "handmade",
        "input": "Вяжу игрушки, как продавать дороже",
        "output": "Продавай повод, а не изделие: набор «подарок новорождённому» дороже одной игрушки. Считай стоимость часа работы и добавляй её в цену. Видео процесса вязания собирает охваты и приводит заказы.",
        "tip": "В хендмейде наборы дороже одиночных изделий",
    },
    {
        "domain": "smm",
        "input": "Хочу вести соцсети клиентам",
        "output": "Выбери одну нишу (например салоны или стоматологии) и упакуй пакет с понятными цифрами: столько постов, столько заявок ожидаемо. Возьми 2 проекта на результат ради кейсов и веди свой канал как витрину.",
        "tip": "Нишевый SMM дороже общего в 2–3 раза",
    },
    {
        "domain": "fitness",
        "input": "Онлайн тренировки, как удержать людей",
        "output": "Запусти 21-дневный челлендж с ежедневными чек-инами в чате — удержание выше, чем у разовых тренировок. Собирай фото прогресса с первого дня, они станут основным доказательством. Групповой формат даёт больше денег за твой час.",
        "tip": "Челлендж с чек-инами держит людей лучше персональных занятий",
    },
    {
        "domain": "shop",
        "input": "Хочу продавать товары без вложений",
        "output": "Работай по предзаказу или дропшиппингу: выкладывай 1–3 позиции, собирай оплату, потом закупай. Проси у первых покупателей фото — это твой контент. Понятные условия доставки и возврата снимают возражения.",
        "tip": "Предзаказ убирает риск закупки на старте",
    },
    {
        "domain": "services",
        "input": "Фриланс услуги, мало заказов",
        "output": "Упакуй три пакета вместо почасовки и добавь кейсы с цифрами результата. Делай один бесплатный аудит в неделю — из него получаются и кейсы, и клиенты. Всегда предоплата 50% и короткий договор.",
        "tip": "Пакеты и предоплата стабилизируют доход фрилансера",
    },
    {
        "domain": "events",
        "input": "Оформление праздников шарами",
        "output": "Продавай готовые сценарии-пакеты с фото, а не «сделаем что хотите». Видео с прошлых праздников — главный аргумент. Бронируй дату только с депозитом 30%, иначе календарь развалится.",
        "tip": "Готовые пакеты оформления продаются быстрее индивидуальных",
    },
    {
        "domain": "repair",
        "input": "Ремонт телефонов, как получить клиентов",
        "output": "Выложи прозрачный прайс на частые работы (экран, батарея, разъём) и дай гарантию 3 месяца. Фото до/после и гео-реклама в радиусе 5 км дают самые дешёвые заявки. Считай нормо-часы, чтобы не работать в убыток.",
        "tip": "Прозрачный прайс и гарантия важнее рекламы в ремонте",
    },
    {
        "domain": "general",
        "input": "Не знаю какой бизнес начать",
        "output": "Выпиши три списка: твои навыки, люди рядом с тобой, что у тебя уже просят. На пересечении — идея. Проверь её 20 разговорами и выбери ту, где первый клиент реален за 7 дней.",
        "tip": "Идея без первого клиента за неделю — слишком ранняя",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=3, help="Проходов усиления знаний")
    parser.add_argument("--per-keyword", type=int, default=8, help="Примеров на ключевое слово")
    args = parser.parse_args()

    print("1/5 Генерирую корпус бизнес-идей…")
    rows = build_corpus(per_keyword=args.per_keyword)
    train_rows, test_rows = split(rows)
    print(f"    всего {len(rows)}, train {len(train_rows)}, test {len(test_rows)}, ниш {len(DOMAINS)}")

    print("2/5 Обучаю классификатор ниш (Naive Bayes, слова + биграммы + триграммы)…")
    model = NaiveBayesClassifier()
    model.fit(train_rows)

    print("3/5 Считаю метрики на отложенной выборке…")
    metrics = evaluate(model, test_rows)
    print(f"    accuracy = {metrics['accuracy']:.4f} на {metrics['samples']} примерах")
    weak = {c: a for c, a in metrics["per_class"].items() if a < 0.8}
    if weak:
        print(f"    слабые ниши: {weak}")

    print("4/5 Проверяю контрольные фразы (как в боте: модель + фразы)…")
    # Сохраняем модель до проверки, чтобы движок использовал свежие веса
    model.save()
    engine = BusinessAI()
    sanity_results = []
    sanity_ok = 0
    for text, expected in SANITY:
        pred, conf, _ = engine.detect_domain_detailed(text)
        ok = pred == expected
        sanity_ok += int(ok)
        sanity_results.append(
            {"text": text, "expected": expected, "predicted": pred, "confidence": round(conf, 3), "ok": ok}
        )
        mark = "✓" if ok else "✗"
        print(f"    {mark} {text[:44]:44s} → {pred} ({conf:.2f})")
    sanity_acc = sanity_ok / len(SANITY)
    print(f"    контрольная точность: {sanity_acc:.1%} ({sanity_ok}/{len(SANITY)})")

    model.meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "accuracy": metrics["accuracy"],
        "sanity_accuracy": round(sanity_acc, 4),
        "train_size": len(train_rows),
        "test_size": len(test_rows),
        "classes": len(DOMAINS),
        "vocab_size": model.vocab_size,
    }
    model_path = model.save()

    print("5/5 Сохраняю экспертные знания…")
    examples: list[dict] = []
    tips_extra: dict[str, list[str]] = {}
    for _ in range(max(1, args.rounds)):
        for case in EXPERT_EXAMPLES:
            examples.append(
                {"domain": case["domain"], "input": case["input"], "output": case["output"]}
            )
            tips_extra.setdefault(case["domain"], [])
            if case["tip"] not in tips_extra[case["domain"]]:
                tips_extra[case["domain"]].append(case["tip"])

    uniq = {ex["input"]: ex for ex in examples}
    examples = list(uniq.values())

    trained = {
        "version": "2.0",
        "trained_at": model.meta["trained_at"],
        "rounds": args.rounds,
        "examples_count": len(examples),
        "examples": examples,
        "tips_extra": tips_extra,
    }
    TRAINED.write_text(json.dumps(trained, ensure_ascii=False, indent=2), encoding="utf-8")

    system = (KNOWLEDGE / "system_prompt.txt").read_text(encoding="utf-8")
    with DATASET.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(
                json.dumps(
                    {
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": ex["input"]},
                            {"role": "assistant", "content": ex["output"]},
                        ]
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    REPORT.write_text(
        json.dumps(
            {
                "meta": model.meta,
                "metrics": metrics,
                "sanity": sanity_results,
                "examples_count": len(examples),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("Готово.")
    print(f"  модель:  {model_path}  ({len(DOMAINS)} ниш, vocab {model.vocab_size})")
    print(f"  accuracy: {metrics['accuracy']:.1%} (holdout), контрольные: {sanity_acc:.1%}")
    print(f"  примеры: {TRAINED}")
    print(f"  отчёт:   {REPORT}")

    if sanity_acc < 0.85:
        print("\n⚠️ Контрольная точность ниже 85% — стоит добавить ключевых слов в domains.py")
        sys.exit(2)


if __name__ == "__main__":
    main()
