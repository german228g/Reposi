from __future__ import annotations

import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value.strip()))


def is_valid_url(value: str) -> bool:
    return bool(URL_RE.match(value.strip()))


def is_valid_date(value: str) -> bool:
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


RECEIPT_STEPS: list[tuple[str, str]] = [
    ("name", "Name — введи имя:"),
    ("surname", "Surname — введи фамилию:"),
    ("product_name", "Product Name — название товара:"),
    ("order_date", "Order Date — дата заказа (YYYY-MM-DD):"),
    ("product_image_url", "Product Image URL — ссылка на фото товара:"),
    ("product_price", "Product Price — цена с валютой (например $800):"),
    ("street", "Street — улица:"),
    ("city", "City — город:"),
    ("zip_code", "ZIP Code — индекс:"),
    ("phone", "Phone Number — телефон:"),
    ("state", "State — регион/штат:"),
]


def validate_step(field: str, value: str) -> str | None:
    value = value.strip()
    if not value:
        return "Поле не может быть пустым."
    if field == "order_date" and not is_valid_date(value):
        return "Дата должна быть в формате YYYY-MM-DD."
    if field == "product_image_url" and not is_valid_url(value):
        return "Нужна ссылка, начинающаяся с http:// или https://"
    return None
