from __future__ import annotations

import json
import re
import threading
from pathlib import Path

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value.strip()))


class UserStore:
    """Хранит почту клиента. Один раз поставил — сам не меняет."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict:
        with self.path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, data: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

    def get_email(self, user_id: int) -> str | None:
        with self._lock:
            data = self._read()
            user = data.get(str(user_id))
            if not user:
                return None
            return user.get("email")

    def set_email(self, user_id: int, email: str, *, force: bool = False) -> str:
        email = email.strip().lower()
        if not is_valid_email(email):
            raise ValueError("Некорректный email")

        with self._lock:
            data = self._read()
            key = str(user_id)
            existing = data.get(key, {}).get("email")
            if existing and not force:
                raise PermissionError(
                    "Почта уже сохранена. Сменить можно только через поддержку."
                )
            data[key] = {"email": email}
            self._write(data)
            return email
