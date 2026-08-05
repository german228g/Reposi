"""AI-движок: обученный классификатор ниш + NLU + генерация бренда и советов."""

from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path
from typing import Any

import httpx

from . import nlu
from .classifier import MODEL_PATH, NaiveBayesClassifier
from .domains import DOMAINS, get_domain

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
TRAINED_PATH = KNOWLEDGE_DIR / "trained.json"
PROMPT_PATH = KNOWLEDGE_DIR / "system_prompt.txt"

STYLE_OPTIONS = ["минимализм", "яркий", "премиум", "дерзкий", "тёплый", "техно"]


class BusinessAI:
    def __init__(self) -> None:
        self.model = NaiveBayesClassifier.load(MODEL_PATH)
        self.trained = self._load_trained()
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "").strip().rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    @staticmethod
    def _load_trained() -> dict[str, Any]:
        if TRAINED_PATH.exists():
            try:
                return json.loads(TRAINED_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"examples": [], "tips_extra": {}}

    # ---------- понимание ----------

    def detect_domain(self, text: str) -> str:
        label, _, _ = self.detect_domain_detailed(text)
        return label

    def detect_domain_detailed(self, text: str) -> tuple[str, float, list[tuple[str, float]]]:
        """Гибрид: обученная модель + точные фразовые совпадения.

        Модель хорошо обобщает, но многословные фразы («туры в горы»,
        «чехлы для телефонов») однозначны — им доверяем больше.
        """
        phrase_hits = self._phrase_hits(text)
        if not self.model:
            fallback = max(phrase_hits, key=phrase_hits.get) if phrase_hits else self._keyword_fallback(text)
            return fallback, 1.0 if phrase_hits else 0.0, []

        label, confidence = self.model.predict(text or "")
        top = self.model.top_k(text or "", 3)
        if phrase_hits:
            best_phrase = max(phrase_hits, key=phrase_hits.get)
            # фразовое совпадение перебивает модель, если та не уверена
            # или если фраза длиннее и совпала точно
            if best_phrase != label and (confidence < 0.9 or phrase_hits[best_phrase] >= 2):
                return best_phrase, max(confidence, 0.9), top
        return label, confidence, top

    @staticmethod
    def _phrase_hits(text: str) -> dict[str, int]:
        """Считает точные совпадения многословных ключевых фраз по нишам."""
        low = f" {(text or '').lower()} "
        hits: dict[str, int] = {}
        for key, info in DOMAINS.items():
            if key == "general":
                continue
            count = 0
            for kw in info.get("keywords", []) + info.get("products", []):
                if " " not in kw or len(kw) < 8:
                    continue
                if kw.lower() in low:
                    count += 1
            if count:
                hits[key] = count
        return hits

    @staticmethod
    def _keyword_fallback(text: str) -> str:
        low = (text or "").lower()
        best, best_score = "general", 0
        for key, info in DOMAINS.items():
            score = sum(1 for kw in info.get("keywords", []) if kw in low)
            if score > best_score:
                best, best_score = key, score
        return best

    def get_domain_info(self, domain: str) -> dict[str, Any]:
        info = dict(get_domain(domain))
        extra = (self.trained.get("tips_extra") or {}).get(domain, [])
        if extra:
            info["tips"] = list(info.get("tips", [])) + list(extra)
        return info

    def analyze(self, idea: str) -> dict[str, Any]:
        """Полный разбор идеи: ниша + вытащенные факты."""
        domain, confidence, top = self.detect_domain_detailed(idea)
        facts = nlu.parse_idea(idea)
        info = self.get_domain_info(domain)
        return {
            "domain": domain,
            "domain_ru": info.get("ru", domain),
            "confidence": round(confidence, 3),
            "alternatives": [d for d, _ in top[1:3]],
            **facts,
        }

    # ---------- адаптивные вопросы ----------

    def next_question(self, profile: dict[str, Any]) -> dict[str, Any] | None:
        """Спрашиваем только то, чего реально не хватает."""
        if not profile.get("idea"):
            return {
                "key": "idea",
                "text": "Расскажи идею: что продаёшь и кому? Можно одним предложением.",
                "options": [],
            }
        domain = profile.get("domain") or self.detect_domain(profile["idea"])
        info = self.get_domain_info(domain)

        if not profile.get("audience"):
            return {
                "key": "audience",
                "text": (
                    f"Кто твой клиент в нише «{info.get('ru')}»?\n"
                    "Напиши возраст и город, либо выбери вариант."
                ),
                "options": ["Женщины 25–40", "Молодёжь 14–22", "Родители", "Все, онлайн"],
            }
        if not profile.get("offer"):
            products = info.get("products", [])
            opts = [p.capitalize() for p in products[:3]]
            return {
                "key": "offer",
                "text": "Что продаёшь на старте? Один главный продукт.",
                "options": opts,
            }
        if not profile.get("budget"):
            return {
                "key": "budget",
                "text": "Бюджет на запуск?",
                "options": ["0", "до 5000", "5000–20000", "20000+"],
            }
        if not profile.get("style"):
            return {
                "key": "style",
                "text": "Стиль бренда?",
                "options": ["минимализм", "яркий", "премиум", "тёплый"],
            }
        return None

    def enrich_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Заполняет то, что можно понять из текста идеи, без вопросов."""
        idea = profile.get("idea") or ""
        if not idea:
            return profile
        analysis = self.analyze(idea)
        profile.setdefault("domain", analysis["domain"])
        profile["domain_ru"] = analysis["domain_ru"]
        if analysis.get("audience") and not profile.get("audience"):
            profile["audience"] = analysis["audience"]
        if analysis.get("geo") and not profile.get("geo"):
            profile["geo"] = analysis["geo"]
        if analysis.get("age") and not profile.get("age"):
            profile["age"] = analysis["age"]
        if analysis.get("budget") and not profile.get("budget"):
            profile["budget"] = analysis["budget"]
        if analysis.get("model") and not profile.get("model"):
            profile["model"] = analysis["model"]
        if analysis.get("product") and not profile.get("product"):
            profile["product"] = analysis["product"]
        return profile

    # ---------- ответы ----------

    async def chat(self, user_message: str, context: dict[str, Any] | None = None) -> str:
        context = context or {}
        domain = context.get("domain") or self.detect_domain(
            f"{user_message} {context.get('idea', '')}"
        )
        info = self.get_domain_info(domain)
        if self.groq_key:
            try:
                return await self._groq(user_message, context, info, domain)
            except Exception:
                pass
        if self.ollama_url:
            try:
                return await self._ollama(user_message, context, info, domain)
            except Exception:
                pass
        return self._local_reply(user_message, context, info, domain)

    async def _groq(self, message: str, context: dict, info: dict, domain: str) -> str:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": self._build_prompt(message, context, info, domain)},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 900,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

    async def _ollama(self, message: str, context: dict, info: dict, domain: str) -> str:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": self._build_prompt(message, context, info, domain)},
                    ],
                },
            )
            r.raise_for_status()
            return r.json()["message"]["content"].strip()

    def _build_prompt(self, message: str, context: dict, info: dict, domain: str) -> str:
        tips = "\n".join(f"- {t}" for t in info.get("tips", [])[:8])
        examples = [
            e for e in (self.trained.get("examples") or []) if e.get("domain") == domain
        ][:3]
        shots = "\n".join(f"Вопрос: {e['input']}\nОтвет: {e['output']}" for e in examples)
        return (
            f"Ниша: {domain} ({info.get('ru', '')})\n"
            f"Данные о бизнесе: {json.dumps(context, ensure_ascii=False)}\n"
            f"Экспертные правила:\n{tips}\n\n"
            f"Примеры хороших ответов:\n{shots}\n\n"
            f"Вопрос пользователя: {message}"
        )

    def _local_reply(self, message: str, context: dict, info: dict, domain: str) -> str:
        """Ответ на основе того, что человек уже рассказал."""
        examples = [
            e for e in (self.trained.get("examples") or [])
            if e.get("domain") == domain
        ]
        matched = self._best_example(message, examples)
        tips = info.get("tips", [])
        product = context.get("offer") or context.get("product") or "твой продукт"
        geo = context.get("geo")
        audience = context.get("audience") or "твоя аудитория"
        name = context.get("brand_name") or "твой бренд"

        head = f"Ниша: {info.get('ru')}."
        if geo:
            head += f" Гео: {geo}."
        lines = [head]
        if matched:
            lines.append(matched["output"])
        chosen = random.sample(tips, k=min(2, len(tips))) if tips else []
        for tip in chosen:
            lines.append(f"• {tip}")
        lines.append(
            f"Ближайший шаг для {name}: продай {product} первым 10 клиентам "
            f"({audience}) и собери отзывы."
        )
        return "\n".join(lines)

    @staticmethod
    def _best_example(message: str, examples: list[dict]) -> dict | None:
        if not examples:
            return None
        tokens = set(re.findall(r"[a-zа-яёіїєґ]{3,}", (message or "").lower()))
        best, best_score = None, 0
        for ex in examples:
            ex_tokens = set(re.findall(r"[a-zа-яёіїєґ]{3,}", ex.get("input", "").lower()))
            score = len(tokens & ex_tokens)
            if score > best_score:
                best, best_score = ex, score
        return best if best_score >= 2 else None

    # ---------- бренд ----------

    def suggest_names(self, idea: str, style: str, pref: str, domain: str) -> list[str]:
        if pref and pref.lower().strip() not in {"придумай", "нет", "-", "не знаю", "хз", "ні", "нема"}:
            clean = re.sub(r"[^\w\s\-А-Яа-яЁёІіЇїЄєҒґ]", "", pref).strip()
            if clean:
                return [clean, f"{clean} Studio", f"{clean} Club"]

        info = self.get_domain_info(domain)
        ru_words = list(info.get("name_ru", [])) or ["Старт"]
        en_words = list(info.get("name_en", [])) or ["Base"]
        suffixes = ["Studio", "Club", "Lab", "House", "Co", "Shop", "Room", "Point"]
        style_low = (style or "").lower()

        names: list[str] = []
        product = nlu.extract_product(idea) or ""
        seed = (product.split() or [""])[0].capitalize()

        if "премиум" in style_low:
            names.append(f"{random.choice(en_words)} {random.choice(['Atelier', 'Maison', 'Prive'])}")
        if "дерзк" in style_low or "ярк" in style_low:
            names.append(f"{random.choice(en_words).upper()}!")

        names.append(random.choice(ru_words))
        names.append(f"{random.choice(en_words)}{random.choice(suffixes)}")
        names.append(f"{random.choice(ru_words)} {random.choice(['&Co', 'Дом', 'Место'])}")
        if seed and len(seed) > 3 and seed.lower() not in {"хочу", "буду"}:
            names.append(f"{seed}{random.choice(suffixes)}")
        names.append(random.choice(en_words))

        uniq: list[str] = []
        for n in names:
            n = n.strip()
            if n and n not in uniq:
                uniq.append(n)
        return uniq[:5]

    def brand_strategy(self, profile: dict[str, Any]) -> dict[str, Any]:
        profile = self.enrich_profile(dict(profile))
        idea = profile.get("idea", "")
        domain = profile.get("domain") or self.detect_domain(idea)
        info = self.get_domain_info(domain)
        style = profile.get("style") or "минимализм"
        names = self.suggest_names(idea, style, profile.get("name_pref", ""), domain)
        brand_name = names[0]

        offer = profile.get("offer") or (info.get("products", ["первый продукт"])[0])
        audience = profile.get("audience") or "клиенты в твоём городе"
        geo = profile.get("geo")
        geo_part = f" {nlu.locative(geo)}" if geo else ""

        tagline = self._tagline(brand_name, offer, style, info)
        # Формулировка без склонений: «Аудитория: X» вместо «для X»
        positioning = (
            f"{brand_name} — {offer}{geo_part}.\n"
            f"Аудитория: {audience}.\n"
            f"Ниша: {info.get('ru')}. Стиль: {style}."
        )
        plan = self._launch_plan(info, offer, audience, geo)
        return {
            "domain": domain,
            "domain_ru": info.get("ru", domain),
            "brand_name": brand_name,
            "name_options": names,
            "tagline": tagline,
            "positioning": positioning,
            "palette": info.get("palette", ["#264653", "#2A9D8F", "#E9C46A", "#F4A261"]),
            "tips": info.get("tips", [])[:5],
            "channel_topics": info.get("channels", []),
            "audience": audience,
            "offer": offer,
            "geo": geo,
            "style": style,
            "budget": profile.get("budget", "0"),
            "story": self._origin_story(brand_name, offer, audience, geo),
            "launch_plan": plan,
            "channel_description": f"{tagline}. {offer.capitalize()}{geo_part}. Аудитория: {audience}.",
        }

    def _tagline(self, name: str, offer: str, style: str, info: dict) -> str:
        style_low = (style or "").lower()
        if "премиум" in style_low:
            return f"{offer.capitalize()} с характером"
        if "дерзк" in style_low:
            return f"{name}. Без скучных решений."
        if "тёпл" in style_low or "тепл" in style_low:
            return f"{offer.capitalize()} с заботой о деталях"
        if "техно" in style_low:
            return f"{offer.capitalize()} — точно и быстро"
        return f"{offer.capitalize()} без лишнего"

    def _origin_story(self, name: str, offer: str, audience: str, geo: str | None) -> str:
        where = f" {nlu.locative(geo)}" if geo and geo != "онлайн" else ""
        return (
            f"{name} появился просто. Аудитория: {audience}{where}. "
            f"Найти нормальный вариант — «{offer}» — без переплат и ожидания сложно. "
            "Мы решили сделать это по-человечески."
        )

    def _launch_plan(self, info: dict, offer: str, audience: str, geo: str | None) -> list[str]:
        where = f" {nlu.locative(geo)}" if geo else ""
        return [
            f"День 1–2: определи 3 пакета «{offer}» с ценами и посчитай себестоимость",
            "День 3: создай канал, поставь лого и описание, выложи пост запуска",
            f"День 4–5: напиши 20 людям из целевой ({audience}) лично, без рассылки",
            f"День 6: собери первые 3 заказа{where}, даже со скидкой ради отзывов",
            "День 7: выложи отзывы и запусти оффер с дедлайном",
            info.get("tips", ["Считай метрики: заявки, конверсия, повторные покупки"])[0],
        ]

    def backend_label(self) -> str:
        meta = (self.model.meta if self.model else {}) or {}
        acc = meta.get("accuracy")
        classes = len(self.model.class_counts) if self.model else 0
        parts = []
        if acc is not None:
            parts.append(f"классификатор {classes} ниш, точность {round(float(acc) * 100)}%")
        examples = len(self.trained.get("examples") or [])
        if examples:
            parts.append(f"{examples} экспертных примеров")
        if self.groq_key:
            parts.append("Groq LLM")
        elif self.ollama_url:
            parts.append(f"Ollama {self.ollama_model}")
        return "; ".join(parts) or "локальный движок"
