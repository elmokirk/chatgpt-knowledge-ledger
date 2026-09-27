from __future__ import annotations

import json
import re
from pathlib import Path


HARD_MAX_CHARS = 3000
DEFAULTS = {
    "model": "gpt-6-luna",
    "reasoning_effort": "low",
    "chat_max_chars": 1000,
    "chat_max_sentences": 10,
    "moc_max_chars": 400,
    "moc_max_sentences": 3,
}


def policy(vault: Path) -> dict:
    path = vault / "09 - System" / "State" / "scheduler.config.json"
    configured = json.loads(path.read_text(encoding="utf-8")).get("summarization", {}) if path.is_file() else {}
    result = {**DEFAULTS, **configured}
    for key in ("chat_max_chars", "moc_max_chars"):
        value = result[key]
        if not isinstance(value, int) or not 1 <= value <= HARD_MAX_CHARS:
            raise ValueError(f"summarization.{key} must be between 1 and {HARD_MAX_CHARS}")
    for key in ("chat_max_sentences", "moc_max_sentences"):
        value = result[key]
        if not isinstance(value, int) or not 1 <= value <= 10:
            raise ValueError(f"summarization.{key} must be between 1 and 10")
    if result["moc_max_chars"] > result["chat_max_chars"]:
        raise ValueError("summarization.moc_max_chars cannot exceed chat_max_chars")
    return result


def compact(value: str | None, *, fallback: str, max_chars: int, max_sentences: int) -> str:
    text = value or fallback
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r":chatgpt-content-reference\{[^}]*\}", "", text)
    text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_#>|~]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ0-9])", text)
    result = " ".join(sentences[:max_sentences]).strip() or fallback
    if len(result) > max_chars:
        result = result[: max_chars - 1].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"
    return result
