#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Создан .env — впиши TELEGRAM_BOT_TOKEN (и TG_API_ID/TG_API_HASH для авто-канала)"
  exit 1
fi

python scripts/train_ai.py --rounds 3 --per-keyword 10

echo ""
echo "Запускаю бота..."
python -m bot.main
