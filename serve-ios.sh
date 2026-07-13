#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8080}"
DIR="$(cd "$(dirname "$0")" && pwd)"

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$IP" ]; then
  IP=$(ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1")
fi

URL="http://${IP}:${PORT}"

echo ""
echo "  🎱 8 Ball Pool — сервер запущен"
echo ""
echo "  На iPhone (тот же Wi‑Fi) откройте Safari:"
echo ""
echo "    ${URL}"
echo ""
echo "  Затем: Поделиться → «На экран Домой» — запуск в один тап!"
echo ""
echo "  Ctrl+C чтобы остановить"
echo ""

cd "$DIR"
python3 -m http.server "$PORT" --bind 0.0.0.0
