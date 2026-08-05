"""Простое файловое хранилище пользователей."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
USERS = DATA / "users"
BRANDS = DATA / "brands"


def _ensure() -> None:
    USERS.mkdir(parents=True, exist_ok=True)
    BRANDS.mkdir(parents=True, exist_ok=True)


def user_path(user_id: int) -> Path:
    _ensure()
    return USERS / f"{user_id}.json"


def load_user(user_id: int) -> dict[str, Any]:
    path = user_path(user_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "user_id": user_id,
        "stage": "idle",
        "q_index": 0,
        "profile": {},
        "brand": None,
        "channel_id": None,
        "channel_username": None,
    }


def save_user(user_id: int, data: dict[str, Any]) -> None:
    path = user_path(user_id)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def brand_dir(user_id: int, brand_name: str) -> Path:
    _ensure()
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in brand_name)[:40] or "brand"
    folder = BRANDS / f"{user_id}_{safe}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder
