"""Load curated collocations for vocabulary PDF generation."""

from __future__ import annotations

import json
from pathlib import Path

from examples_loader import normalize_key

ASSETS = Path(__file__).resolve().parent / "assets"
DEFAULT_PATH = ASSETS / "collocations.json"
FALLBACK_PATH = ASSETS / "collocations-top500.json"

_collocations: dict[str, list[tuple[str, str]]] | None = None


def load_collocations(path: Path = DEFAULT_PATH, *, force: bool = False) -> dict[str, list[tuple[str, str]]]:
    global _collocations
    if _collocations is not None and not force:
        return _collocations

    merged: dict[str, list[tuple[str, str]]] = {}
    for p in (path, FALLBACK_PATH):
        if not p.exists():
            continue
        raw = json.loads(p.read_text(encoding="utf-8"))
        items = raw.get("collocations", raw)
        for k, v in items.items():
            if k in merged:
                continue
            if isinstance(v, dict):
                merged[k] = [(p["en"], p["zh"]) for p in v.get("items", [])]
            else:
                merged[k] = v
    _collocations = merged
    return _collocations


def lookup_collocations(word: str, path: Path = DEFAULT_PATH, *, limit: int = 3) -> list[tuple[str, str]]:
    bank = load_collocations(path)
    key = normalize_key(word)
    return bank.get(key, [])[:limit]
