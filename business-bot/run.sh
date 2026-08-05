#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Создан .env — впиши TELEGRAM_BOT_TOKEN"
fi

python scripts/train_ai.py --rounds 3
echo ""
echo "Запускаю бота..."
python -m bot.main
