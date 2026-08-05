# Business Launch AI — Telegram-бот для запуска бизнеса

Помогает людям 13–50 лет: уточняет идею, собирает бренд, рисует лого, пишет посты и помогает подключить канал.

## Что умеет

- Диалог-анкета по бизнес-идее
- AI-советы (локальный Business Pro engine; опционально Groq/Ollama)
- Название, слоган, позиционирование
- Логотип PNG + SVG и палитра
- Пакет постов и контент-план
- Инструкция по созданию канала + публикация после добавления бота админом

## Быстрый старт

```bash
cd business-bot
cp .env.example .env
# Впиши токен от @BotFather в TELEGRAM_BOT_TOKEN
chmod +x run.sh
./run.sh
```

Или вручную:

```bash
cd business-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/train_ai.py --rounds 5
python -m bot.main
```

## Токен

1. Открой [@BotFather](https://t.me/BotFather)
2. `/newbot` или возьми токен существующего
3. Вставь в `business-bot/.env`:

```
TELEGRAM_BOT_TOKEN=123456:ABC...
```

⚠️ Не публикуй токен в чатах и git. Если уже светился — перевыпусти через `/revoke` в BotFather.

## «Обучение» AI

Полноценно обучить модель «до уровня GPT» на домашнем ПК нельзя без огромного железа.
Скрипт `scripts/train_ai.py` делает практичное автоусиление:

- расширяет knowledge-базу кейсами по нишам
- копит few-shot примеры
- готовит `finetune_dataset.jsonl` под будущий LoRA (Ollama / Unsloth)

```bash
python scripts/train_ai.py --rounds 10
```

Опционально усилить ответы бесплатным API:

1. Ключ [Groq](https://console.groq.com) → `GROQ_API_KEY` в `.env`
2. Или локальный [Ollama](https://ollama.com) → `OLLAMA_BASE_URL=http://localhost:11434`

## Сценарий пользователя

1. `/start` → «Запустить бизнес»
2. Ответить на вопросы
3. Получить лого, палитру, BRAND.md, POSTS.md
4. Создать канал в Telegram, поставить лого, добавить бота админом
5. Переслать пост из канала боту
6. `/publish` — пост запуска уходит в канал

## Структура

```
business-bot/
  bot/
    main.py           # запуск
    handlers.py       # логика Telegram
    ai/engine.py      # AI-движок
    ai/knowledge/     # база знаний + trained.json
    logo_generator.py
    posts_generator.py
  scripts/train_ai.py
  data/               # профили пользователей и бренд-пакеты
  run.sh
```

## Важно про каналы

Telegram Bot API **не умеет создавать каналы** от имени пользователя. Бот готовит всё до стержня и публикует, когда вы добавите его админом.
