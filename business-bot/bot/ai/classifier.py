"""Multinomial Naive Bayes на словах и символьных n-граммах.

Обучается на корпусе бизнес-идей и сохраняется в knowledge/model.json.
Работает без внешних зависимостей, поэтому бот запускается везде.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "knowledge" / "model.json"

_WORD_RE = re.compile(r"[a-zа-яёіїєґ0-9]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    text = (text or "").lower().replace("ё", "е")
    words = _WORD_RE.findall(text)
    tokens: list[str] = []
    for w in words:
        if len(w) < 2:
            continue
        tokens.append(w)
        # префиксы разной длины заменяют стеммер: «ботов» → «бот», «бото», «ботов»
        for cut in (3, 4, 5, 6):
            if len(w) > cut:
                tokens.append(w[:cut])
        # символьные триграммы дают устойчивость к опечаткам и склонениям
        if len(w) >= 4:
            for i in range(len(w) - 2):
                tokens.append("#" + w[i : i + 3])
    for a, b in zip(words, words[1:]):
        tokens.append(f"{a}_{b}")
    return tokens


class NaiveBayesClassifier:
    def __init__(self) -> None:
        self.class_counts: dict[str, int] = {}
        self.token_counts: dict[str, dict[str, int]] = {}
        self.class_totals: dict[str, int] = {}
        self.vocab_size: int = 0
        self.trained: bool = False
        self.meta: dict = {}

    def fit(self, rows: list[tuple[str, str]]) -> None:
        class_counts: dict[str, int] = defaultdict(int)
        token_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        class_totals: dict[str, int] = defaultdict(int)
        vocab: set[str] = set()

        for text, label in rows:
            class_counts[label] += 1
            # бинаризация: короткие тексты иначе перевешиваются повторами n-грамм
            for tok in set(tokenize(text)):
                token_counts[label][tok] += 1
                class_totals[label] += 1
                vocab.add(tok)

        self.class_counts = dict(class_counts)
        self.token_counts = {c: dict(t) for c, t in token_counts.items()}
        self.class_totals = dict(class_totals)
        self.vocab_size = len(vocab)
        self.trained = True

    def scores(self, text: str) -> dict[str, float]:
        if not self.trained:
            return {}
        tokens = set(tokenize(text))
        n_classes = len(self.class_counts) or 1
        out: dict[str, float] = {}
        for label in self.class_counts:
            # равномерный априор: корпус сбалансирован, частота класса не должна решать
            score = math.log(1 / n_classes)
            counts = self.token_counts.get(label, {})
            denom = self.class_totals.get(label, 0) + self.vocab_size + 1
            for tok in tokens:
                score += math.log((counts.get(tok, 0) + 1) / denom)
            out[label] = score
        return out

    def predict(self, text: str) -> tuple[str, float]:
        scores = self.scores(text)
        if not scores:
            return "general", 0.0
        best = max(scores, key=scores.get)
        # softmax-подобная нормализация уверенности
        top = scores[best]
        exp_sum = sum(math.exp(min(0.0, s - top)) for s in scores.values())
        confidence = 1.0 / exp_sum if exp_sum else 0.0
        return best, confidence

    def top_k(self, text: str, k: int = 3) -> list[tuple[str, float]]:
        scores = self.scores(text)
        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
        return ordered

    def save(self, path: Path = MODEL_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "class_counts": self.class_counts,
            "token_counts": self.token_counts,
            "class_totals": self.class_totals,
            "vocab_size": self.vocab_size,
            "meta": self.meta,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> "NaiveBayesClassifier | None":
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        model = cls()
        model.class_counts = payload.get("class_counts", {})
        model.token_counts = payload.get("token_counts", {})
        model.class_totals = payload.get("class_totals", {})
        model.vocab_size = int(payload.get("vocab_size", 0))
        model.meta = payload.get("meta", {})
        model.trained = bool(model.class_counts)
        return model if model.trained else None


def evaluate(model: NaiveBayesClassifier, rows: list[tuple[str, str]]) -> dict:
    correct = 0
    per_class_total: dict[str, int] = defaultdict(int)
    per_class_correct: dict[str, int] = defaultdict(int)
    for text, label in rows:
        pred, _ = model.predict(text)
        per_class_total[label] += 1
        if pred == label:
            correct += 1
            per_class_correct[label] += 1
    accuracy = correct / len(rows) if rows else 0.0
    per_class = {
        c: round(per_class_correct[c] / per_class_total[c], 3)
        for c in sorted(per_class_total)
        if per_class_total[c]
    }
    return {"accuracy": round(accuracy, 4), "samples": len(rows), "per_class": per_class}
