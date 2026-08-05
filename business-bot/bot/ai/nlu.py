"""Разбор бизнес-идеи: город, возраст аудитории, продукт, модель, бюджет.

Нужен, чтобы бот не переспрашивал то, что человек уже написал.
"""

from __future__ import annotations

import re

CITIES = {
    "киев": "Киев", "київ": "Киев", "киеве": "Киев", "києві": "Киев", "kyiv": "Киев", "kiev": "Киев",
    "харьков": "Харьков", "харків": "Харьков", "харькове": "Харьков",
    "одесса": "Одесса", "одеса": "Одесса", "одессе": "Одесса",
    "львов": "Львов", "львів": "Львов", "львове": "Львов",
    "днепр": "Днепр", "дніпро": "Днепр", "днепре": "Днепр",
    "запорожье": "Запорожье", "винница": "Винница", "полтава": "Полтава",
    "москва": "Москва", "москве": "Москва", "спб": "Санкт-Петербург",
    "петербург": "Санкт-Петербург", "питер": "Санкт-Петербург",
    "минск": "Минск", "минске": "Минск", "алматы": "Алматы", "астана": "Астана",
    "варшава": "Варшава", "варшаве": "Варшава", "краков": "Краков", "берлин": "Берлин",
}

COUNTRIES = {
    "украина": "Украина", "україна": "Украина", "украине": "Украина", "україні": "Украина",
    "россия": "Россия", "россии": "Россия", "беларусь": "Беларусь", "казахстан": "Казахстан",
    "польша": "Польша", "польше": "Польша", "германия": "Германия",
}

ONLINE_WORDS = ["онлайн", "online", "интернет", "по всему миру", "удаленно", "віддалено"]

# Предложный падеж для корректных фраз «в Киеве», «во Львове»
LOCATIVE = {
    "Киев": "в Киеве", "Харьков": "в Харькове", "Одесса": "в Одессе", "Львов": "во Львове",
    "Днепр": "в Днепре", "Запорожье": "в Запорожье", "Винница": "в Виннице", "Полтава": "в Полтаве",
    "Москва": "в Москве", "Санкт-Петербург": "в Санкт-Петербурге", "Минск": "в Минске",
    "Алматы": "в Алматы", "Астана": "в Астане", "Варшава": "в Варшаве", "Краков": "в Кракове",
    "Берлин": "в Берлине", "Украина": "в Украине", "Россия": "в России", "Беларусь": "в Беларуси",
    "Казахстан": "в Казахстане", "Польша": "в Польше", "Германия": "в Германии",
    "онлайн": "онлайн",
}


def locative(geo: str | None) -> str:
    """«Киев» → «в Киеве». Для незнакомых мест — «в X»."""
    if not geo:
        return ""
    if geo in LOCATIVE:
        return LOCATIVE[geo]
    return f"в {geo}"

GENDER_WORDS = {
    "женщин": "женщины", "жінок": "женщины", "девушек": "девушки", "дівчат": "девушки",
    "мужчин": "мужчины", "чоловіків": "мужчины", "парней": "парни",
    "мам": "мамы", "родителей": "родители", "школьник": "школьники", "студент": "студенты",
    "подростк": "подростки", "предпринимател": "предприниматели", "бизнес": "предприниматели",
}

MODEL_WORDS = {
    "подписк": "подписка",
    "услуг": "услуга",
    "товар": "товар",
    "курс": "курс",
    "доставк": "доставка",
    "аренд": "аренда",
    "консультац": "консультации",
    "магазин": "розница",
    "опт": "опт",
    "фриланс": "услуга",
}

BUDGET_RE = re.compile(r"(\d[\d\s]{1,7})\s*(?:грн|₴|руб|₽|\$|usd|тыс|к\b|k\b)?", re.IGNORECASE)
AGE_RANGE_RE = re.compile(r"(\d{2})\s*[-–—до]{1,3}\s*(\d{2})")
AGE_PLUS_RE = re.compile(r"(\d{2})\s*\+")

STOPWORDS = {
    "хочу", "хотел", "хотела", "делать", "сделать", "бизнес", "бізнес", "для", "это", "буду",
    "будет", "свой", "свою", "своё", "продавать", "продаю", "канал", "телеграм", "очень",
    "просто", "типа", "чтобы", "который", "которая", "начать", "открыть", "заниматься",
    "планирую", "думаю", "мечтаю", "идея", "проект", "нужно", "нужен", "нужна", "есть",
    "можно", "также", "тоже", "года", "лет", "около", "примерно", "может", "быть", "самое",
}


def _clean_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Zа-яА-ЯёЁіїєґІЇЄҐ]{3,}", (text or "").lower())


def extract_geo(text: str) -> str | None:
    low = (text or "").lower()
    for word in _clean_words(low):
        if word in CITIES:
            return CITIES[word]
    for word in _clean_words(low):
        if word in COUNTRIES:
            return COUNTRIES[word]
    for w in ONLINE_WORDS:
        if w in low:
            return "онлайн"
    return None


def extract_age(text: str) -> str | None:
    low = (text or "").lower()
    m = AGE_RANGE_RE.search(low)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if 8 <= a <= 90 and a < b <= 95:
            return f"{a}–{b} лет"
    m = AGE_PLUS_RE.search(low)
    if m:
        a = int(m.group(1))
        if 10 <= a <= 80:
            return f"{a}+ лет"
    return None


def extract_gender_group(text: str) -> str | None:
    low = (text or "").lower()
    for stem, label in GENDER_WORDS.items():
        if stem in low:
            return label
    return None


def extract_model(text: str) -> str | None:
    low = (text or "").lower()
    for stem, label in MODEL_WORDS.items():
        if stem in low:
            return label
    return None


def extract_budget(text: str) -> str | None:
    low = (text or "").lower()
    if any(w in low for w in ["без вложений", "без бюджета", "нет денег", "ноль", "0 грн", "бесплатно"]):
        return "0"
    m = BUDGET_RE.search(low)
    if m:
        raw = m.group(1).replace(" ", "")
        if raw.isdigit() and 100 <= int(raw) <= 10_000_000:
            return raw
    return None


def extract_product(text: str, domain_products: list[str] | None = None) -> str | None:
    """Ключевая сущность идеи: то, что человек продаёт."""
    words = [w for w in _clean_words(text) if w not in STOPWORDS]
    if not words:
        return None
    # берём первое содержательное слово-существительное и соседнее уточнение
    head = words[0]
    tail = words[1] if len(words) > 1 and words[1] not in CITIES and words[1] not in COUNTRIES else ""
    phrase = f"{head} {tail}".strip()
    return phrase


def parse_idea(text: str) -> dict[str, str | None]:
    """Достаёт всё, что можно понять из свободного текста идеи."""
    audience_bits = []
    group = extract_gender_group(text)
    age = extract_age(text)
    geo = extract_geo(text)
    if group:
        audience_bits.append(group)
    if age:
        audience_bits.append(age)
    # Гео в аудиторию не дублируем: оно хранится отдельным полем
    return {
        "geo": geo,
        "age": age,
        "group": group,
        "audience": ", ".join(audience_bits) if audience_bits else None,
        "model": extract_model(text),
        "budget": extract_budget(text),
        "product": extract_product(text),
    }


def missing_fields(profile: dict) -> list[str]:
    """Какие данные реально ещё нужны — остальное не спрашиваем."""
    need = []
    if not profile.get("idea"):
        need.append("idea")
    if not profile.get("audience"):
        need.append("audience")
    if not profile.get("offer"):
        need.append("offer")
    if not profile.get("budget"):
        need.append("budget")
    if not profile.get("style"):
        need.append("style")
    return need
