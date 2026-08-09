"""Настройки сервиса: ключи приложения и админы.

api_id / api_hash принадлежат нашему приложению, а не пользователям:
их достаточно указать один раз, после чего любой человек подключает
свой аккаунт номером и кодом.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_USER_IDS", "")
    ids: set[int] = set()
    for part in re.split(r"[,\s]+", raw):
        if part.strip().isdigit():
            ids.add(int(part.strip()))
    return ids


def is_admin(user_id: int) -> bool:
    ids = admin_ids()
    # Пока админы не заданы, первый, кто настраивает ключи, становится админом
    return not ids or user_id in ids


def set_env(values: dict[str, str], persist: bool = True) -> None:
    """Обновляет переменные окружения процесса и (опционально) .env."""
    for key, value in values.items():
        os.environ[key] = value
    if not persist:
        return

    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    for key, value in values.items():
        replaced = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                replaced = True
                break
        if not replaced:
            lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        ENV_PATH.chmod(0o600)
    except OSError:
        pass
