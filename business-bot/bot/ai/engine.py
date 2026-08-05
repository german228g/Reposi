"""Гибридный AI: локальная knowledge-база + опционально Groq/Ollama."""

from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path
from typing import Any

import httpx

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
BASE_PATH = KNOWLEDGE_DIR / "base.json"
TRAINED_PATH = KNOWLEDGE_DIR / "trained.json"
PROMPT_PATH = KNOWLEDGE_DIR / "system_prompt.txt"


class BusinessAI:
    def __init__(self) -> None:
        self.base = self._load_json(BASE_PATH)
        self.trained = self._load_json(TRAINED_PATH) if TRAINED_PATH.exists() else {"examples": [], "tips_extra": {}}
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "").strip().rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def detect_domain(self, text: str) -> str:
        t = text.lower()
        rules = [
            ("food", ["еда", "кафе", "кофе", "бургер", "пицц", "доставк", "выпечк", "торты", "кухн", "ресторан", "фуд"]),
            ("beauty", ["красот", "бьюти", "ногт", "ресниц", "макияж", "парикмах", "барбер", "косметолог", "уход"]),
            ("edu", ["обучен", "курс", "репетитор", "урок", "школ", "егэ", "английск", "матема", "наставник"]),
            ("digital", ["бот", "сайт", "приложен", "софт", "ai", "ии", "saas", "дизайн", "разработ", "скрипт", "телеграм"]),
            ("shop", ["магазин", "мерч", "товар", "продаж", "одежд", "украшен", "дропшип", "wildberries", "wb"]),
            ("fitness", ["фитнес", "спорт", "тренир", "зож", "похуд", "качал", "йога"]),
            ("content", ["блог", "контент", "канал", "медиа", "тикток", "youtube", "сообществ", "комьюнити"]),
            ("services", ["услуг", "фриланс", "агентств", "смм", "маркетинг", "фотограф", "видеограф", "юрист", "ремонт"]),
        ]
        scores = {k: 0 for k, _ in rules}
        for key, words in rules:
            for w in words:
                if w in t:
                    scores[key] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"

    def get_domain_info(self, domain: str) -> dict[str, Any]:
        domains = self.base.get("domains", {})
        info = dict(domains.get(domain) or domains["general"])
        extra = self.trained.get("tips_extra", {}).get(domain, [])
        if extra:
            info["tips"] = list(info.get("tips", [])) + list(extra)
        return info

    def questions(self) -> list[dict[str, str]]:
        return list(self.base.get("questions", []))

    async def chat(self, user_message: str, context: dict[str, Any] | None = None) -> str:
        context = context or {}
        domain = context.get("domain") or self.detect_domain(user_message + " " + str(context.get("idea", "")))
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
        prompt = self._build_prompt(message, context, info, domain)
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 900,
                },
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _ollama(self, message: str, context: dict, info: dict, domain: str) -> str:
        prompt = self._build_prompt(message, context, info, domain)
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            r.raise_for_status()
            return r.json()["message"]["content"].strip()

    def _build_prompt(self, message: str, context: dict, info: dict, domain: str) -> str:
        tips = "\n".join(f"- {t}" for t in info.get("tips", [])[:8])
        return (
            f"Домен: {domain} ({info.get('ru', '')})\n"
            f"Контекст анкеты: {json.dumps(context, ensure_ascii=False)}\n"
            f"Экспертные советы:\n{tips}\n\n"
            f"Сообщение пользователя: {message}"
        )

    def _local_reply(self, message: str, context: dict, info: dict, domain: str) -> str:
        tip = random.choice(info.get("tips", ["Начни с малого и проверь спрос."]))
        name = context.get("brand_name") or context.get("name_pref") or "твой бренд"
        if not context.get("idea"):
            return (
                "Огонь, давай соберём бизнес с нуля.\n\n"
                "Напиши идею: чем хочешь заниматься и для кого?\n"
                "Можно коротко — я задам уточняющие вопросы."
            )
        if context.get("stage") == "advice":
            return (
                f"По нише «{info.get('ru', domain)}» вот рабочий ход:\n\n"
                f"• {tip}\n"
                f"• Сделай 1 оффер и 1 канал продаж на 14 дней\n"
                f"• Измерь: сколько людей написали / купили\n\n"
                f"Команда /brand — соберу название, лого, посты и дизайн для {name}."
            )
        return (
            f"Понял направление: {info.get('ru', domain)}.\n\n"
            f"Ключевой совет: {tip}\n\n"
            "Продолжай отвечать на вопросы — после анкеты соберу полный пакет запуска."
        )

    def suggest_names(self, idea: str, style: str, pref: str) -> list[str]:
        if pref and pref.lower() not in {"придумай", "нет", "-", "не знаю", "хз"}:
            clean = re.sub(r"[^\w\s\-А-Яа-яЁё]", "", pref).strip()
            if clean:
                return [clean, f"{clean} Lab", f"{clean} Co"]

        domain = self.detect_domain(idea)
        particles = self.base.get("name_particles", {})
        prefixes = particles.get("prefixes", ["Nova"])
        suffixes = particles.get("suffixes", ["Hub"])
        ru_words = particles.get("ru_words", ["Старт"])

        style = (style or "").lower()
        if "премиум" in style:
            prefixes = ["Aura", "Pure", "Bold", "Nova"] + prefixes
        elif "дерзк" in style or "ярк" in style:
            prefixes = ["Spark", "Pulse", "Bold", "Flux"] + prefixes
        elif "техно" in style or "tech" in style:
            prefixes = ["Neo", "Core", "Flux", "Peak"] + prefixes

        names = set()
        seed_word = self._seed_from_idea(idea)
        for _ in range(20):
            if random.random() < 0.45 and seed_word:
                names.add(f"{seed_word}{random.choice(suffixes)}")
            elif random.random() < 0.5:
                names.add(f"{random.choice(prefixes)}{random.choice(suffixes)}")
            else:
                names.add(random.choice(ru_words))
            if len(names) >= 5:
                break
        result = list(names)[:5]
        if domain == "food" and "Bite" not in result:
            result.append(f"{random.choice(prefixes)}Bite")
        return result[:5]

    def _seed_from_idea(self, idea: str) -> str:
        stop = {
            "хочу", "сделать", "бизнес", "для", "это", "будет", "свой", "свою", "продать",
            "продавать", "канал", "телеграм", "очень", "просто", "типа", "чтобы", "который",
        }
        words = re.findall(r"[A-Za-zА-Яа-яЁё]{4,}", idea or "")
        candidates = [w.capitalize() for w in words if w.lower() not in stop]
        return candidates[0] if candidates else ""

    def brand_strategy(self, profile: dict[str, Any]) -> dict[str, Any]:
        idea = profile.get("idea", "")
        domain = self.detect_domain(idea + " " + profile.get("offer", ""))
        info = self.get_domain_info(domain)
        style = profile.get("style", "минимализм")
        names = self.suggest_names(idea, style, profile.get("name_pref", ""))
        brand_name = names[0]
        audience = profile.get("audience") or "людям, которым нужна твоя экспертиза"
        offer = profile.get("offer") or "твой первый продукт"
        tagline = self._tagline(brand_name, offer, audience, style)
        positioning = (
            f"{brand_name} — это {offer} для {audience}. "
            f"Стиль: {style}. Ниша: {info.get('ru', domain)}."
        )
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
            "style": style,
            "budget": profile.get("budget", "0"),
            "story": self._origin_story(brand_name, idea, audience),
        }

    def _tagline(self, name: str, offer: str, audience: str, style: str) -> str:
        templates = [
            f"{name}: {offer} без лишнего шума",
            f"Для {audience} — просто и по делу",
            f"{offer}. Красиво. Честно. Быстро.",
            f"Запуск без воды — только результат",
        ]
        if "премиум" in (style or "").lower():
            return f"{name} — тихая сила и точный вкус"
        if "дерзк" in (style or "").lower():
            return f"{name}. Громче, чем сомнения."
        return random.choice(templates)

    def _origin_story(self, name: str, idea: str, audience: str) -> str:
        short = (idea or "идею помочь людям").strip()
        if len(short) > 180:
            short = short[:177] + "..."
        return (
            f"Мы заметили, что {audience} часто остаются без простого решения. "
            f"Так родился {name}: {short}"
        )

    def backend_label(self) -> str:
        if self.groq_key:
            return "Groq Llama 3.3 (бесплатный API)"
        if self.ollama_url:
            return f"Ollama ({self.ollama_model})"
        trained_n = len(self.trained.get("examples", []))
        return f"Локальный Business Pro engine (+{trained_n} обученных примеров)"
