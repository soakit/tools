"""Load curated example sentences for vocabulary PDF generation."""

from __future__ import annotations

import json
import re
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "assets"
DEFAULT_PATH = ASSETS / "examples.json"
FALLBACK_PATH = ASSETS / "examples-top500.json"

_examples: dict[str, dict] | None = None


def normalize_key(word: str) -> str:
    w = word.strip().lower()
    w = re.sub(r"\s*\([^)]*\)", "", w)
    w = re.sub(r"\s*=.*$", "", w)
    w = re.sub(r"\s+modal\s*$", "", w, flags=re.I)
    return w.strip().rstrip(".")


def load_examples(path: Path = DEFAULT_PATH, *, force: bool = False) -> dict[str, dict]:
    global _examples
    if _examples is not None and not force:
        return _examples

    _examples = {}
    for p in (path, FALLBACK_PATH):
        if p.exists():
            raw = json.loads(p.read_text(encoding="utf-8"))
            _examples.update(raw.get("examples", raw))
    return _examples


def lookup_example(word: str, path: Path = DEFAULT_PATH) -> tuple[str, str] | None:
    bank = load_examples(path)
    key = normalize_key(word)
    entry = bank.get(key)
    if not entry:
        return None
    en = entry.get("en", "").strip()
    zh = entry.get("zh", "").strip()
    if en and zh:
        return en, zh
    return None
