#!/usr/bin/env python3
"""Export collocations_manual.py to assets/collocations-top500.json."""

from __future__ import annotations

import json
from pathlib import Path

from collocations_manual import COLLOCATIONS, load_top500_base_words, verify_coverage

ASSETS = Path(__file__).resolve().parent / "assets"
OUTPUT = ASSETS / "collocations-top500.json"


def main() -> None:
    verify_coverage()
    words = load_top500_base_words()
    collocations = {
        w: {"items": [{"en": en, "zh": zh} for en, zh in COLLOCATIONS.get(w, [])]}
        for w in words
    }
    payload = {
        "meta": {
            "total": len(collocations),
            "phrases": sum(len(v["items"]) for v in collocations.values()),
            "source": "collocations_manual.py",
        },
        "collocations": collocations,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT}")
    print(f"  words: {payload['meta']['total']}, phrases: {payload['meta']['phrases']}")


if __name__ == "__main__":
    main()
