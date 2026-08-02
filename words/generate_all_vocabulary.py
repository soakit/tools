#!/usr/bin/env python3
"""Generate examples and collocations for all senior.json words (merge top500 + Tatoeba)."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from coca_loader import load_index
from generate_examples import (
    MANUAL,
    base_word,
    fetch_tatoeba,
    score_sentence,
)

ASSETS = Path(__file__).resolve().parent / "assets"
SENIOR_PATH = ASSETS / "senior.json"
EXAMPLES_PATH = ASSETS / "examples.json"
COLLOCATIONS_PATH = ASSETS / "collocations.json"
EXAMPLES_TOP500 = ASSETS / "examples-top500.json"
COLLOCATIONS_TOP500 = ASSETS / "collocations-top500.json"
CACHE_PATH = ASSETS / "_tatoeba_cache.json"

TATOEBA_URL = (
    "https://tatoeba.org/en/api_v0/search?from=eng&to=cmn&orphans=no&sort=relevance&limit=15&query="
)
EMPTY_PRONOUNS = frozenset({"him", "their", "them", "its", "her", "his", "my", "your", "our"})


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_examples(examples: dict, stats: dict) -> None:
    payload = {
        "meta": {"total": len(examples), "stats": stats},
        "examples": examples,
    }
    EXAMPLES_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_collocations(collocations: dict, stats: dict) -> None:
    payload = {
        "meta": {"total": len(collocations), "phrases": sum(len(v["items"]) for v in collocations.values()), "stats": stats},
        "collocations": collocations,
    }
    COLLOCATIONS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_senior_words() -> list[dict]:
    coca = load_index()
    data = json.loads(SENIOR_PATH.read_text(encoding="utf-8"))
    words: list[dict] = []
    seen: set[str] = set()
    for section in data["words_by_letter"]:
        for item in section["words"]:
            base = base_word(item["word"])
            if base in seen:
                continue
            seen.add(base)
            entry = coca.lookup(item["word"])
            words.append({
                "word": item["word"],
                "definition": item["definition"],
                "rank": entry.rank if entry else 999999,
                "coca_paraphrase": entry.paraphrase if entry else "",
                "coca_meanings": entry.meanings if entry else [],
            })
    words.sort(key=lambda w: (w["rank"], base_word(w["word"])))
    return words


def merge_top500(examples: dict, collocations: dict) -> None:
    if EXAMPLES_TOP500.exists():
        for k, v in load_json(EXAMPLES_TOP500).get("examples", {}).items():
            examples.setdefault(k, v)
    if COLLOCATIONS_TOP500.exists():
        for k, v in load_json(COLLOCATIONS_TOP500).get("collocations", {}).items():
            collocations.setdefault(k, v)


def load_cache() -> dict[str, list[tuple[str, str]]]:
    if not CACHE_PATH.exists():
        return {}
    raw = load_json(CACHE_PATH)
    return {k: [(a, b) for a, b in v] for k, v in raw.items()}


def save_cache(cache: dict[str, list[tuple[str, str]]]) -> None:
    CACHE_PATH.write_text(
        json.dumps({k: v for k, v in sorted(cache.items())}, ensure_ascii=False),
        encoding="utf-8",
    )


def fetch_tatoeba_cached(base: str, cache: dict[str, list[tuple[str, str]]]) -> list[tuple[str, str]]:
    if base in cache:
        return cache[base]
    try:
        result = fetch_tatoeba(base)
    except Exception:
        result = []
    cache[base] = result
    return result


def pick_example(base: str, item: dict, candidates: list[tuple[str, str]]) -> tuple[str, str, str]:
    if base in MANUAL:
        return *MANUAL[base], "manual"
    for en, zh in candidates:
        if score_sentence(en, base) > 0:
            return en, zh, "tatoeba"
    return "", "", "skipped"


def extract_collocations(
    base: str, candidates: list[tuple[str, str]], example_en: str, max_items: int = 3
) -> list[tuple[str, str]]:
    if base in EMPTY_PRONOUNS:
        return []

    seen: set[str] = set()
    items: list[tuple[str, str]] = []
    example_key = example_en.strip().lower()

    def add(en: str, zh: str) -> None:
        en = en.strip()
        zh = zh.strip()
        if not en or not zh:
            return
        key = en.lower()
        if key in seen or key == example_key:
            return
        if not re.search(rf"\b{re.escape(base)}\b", en, re.I):
            return
        wcount = len(en.split())
        if wcount < 2 or wcount > 10:
            return
        seen.add(key)
        items.append((en, zh))

    # Prefer short phrase-like Tatoeba hits (skip the main example sentence).
    for en, zh in candidates:
        add(en, zh)
        if len(items) >= max_items:
            return items[:max_items]

    # Extract "word + tail" / "head + word" from longer sentences.
    for en, zh in candidates:
        for m in re.finditer(rf"\b(\w+(?:\s+\w+){{0,2}}\s+{re.escape(base)}|\b{re.escape(base)}\s+\w+(?:\s+\w+){{0,2}})\b", en, re.I):
            add(m.group(1), zh)
            if len(items) >= max_items:
                return items[:max_items]

    return items[:max_items]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate examples + collocations for all senior words")
    parser.add_argument("--delay", type=float, default=0.12, help="Delay between Tatoeba requests (seconds)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true", help="Skip words already in output files")
    args = parser.parse_args()

    words = load_senior_words()
    if args.limit:
        words = words[: args.limit]

    examples: dict = {}
    collocations: dict = {}
    merge_top500(examples, collocations)

    if args.resume and EXAMPLES_PATH.exists():
        examples.update(load_json(EXAMPLES_PATH).get("examples", {}))
    if args.resume and COLLOCATIONS_PATH.exists():
        collocations.update(load_json(COLLOCATIONS_PATH).get("collocations", {}))

    cache = load_cache()
    ex_stats = {"manual": 0, "tatoeba": 0, "skipped": 0}
    col_stats = {"curated": 0, "tatoeba": 0, "empty": 0, "skipped": 0}

    todo = [
        w for w in words
        if base_word(w["word"]) not in examples
        or (
            base_word(w["word"]) not in collocations
            or (
                not collocations.get(base_word(w["word"]), {}).get("items")
                and base_word(w["word"]) not in EMPTY_PRONOUNS
            )
        )
    ]
    print(f"Total unique words: {len(words)}, to process: {len(todo)}")

    for i, item in enumerate(todo, 1):
        base = base_word(item["word"])

        need_ex = base not in examples
        has_col = base in collocations and collocations[base].get("items")
        need_col = not has_col and base not in EMPTY_PRONOUNS

        if not need_ex and not need_col:
            ex_stats["skipped"] += 1
            col_stats["skipped"] += 1
            continue

        candidates: list[tuple[str, str]] = []
        if need_ex or (need_col and base not in EMPTY_PRONOUNS):
            candidates = fetch_tatoeba_cached(base, cache)
            if args.delay:
                time.sleep(args.delay)

        if need_ex:
            en, zh, src = pick_example(base, item, candidates)
            if src != "skipped":
                examples[base] = {
                    "en": en, "zh": zh, "rank": item["rank"], "word": item["word"], "source": src,
                }
                ex_stats[src] += 1
            else:
                ex_stats["skipped"] += 1
                en = ""
        else:
            en = examples[base]["en"]

        if need_col:
            if base in EMPTY_PRONOUNS:
                collocations[base] = {"items": []}
                col_stats["empty"] += 1
            else:
                phrases = extract_collocations(base, candidates, en)
                collocations[base] = {"items": [{"en": a, "zh": b} for a, b in phrases]}
                col_stats["tatoeba" if phrases else "empty"] += 1

        if i % 25 == 0:
            save_cache(cache)
            save_examples(examples, ex_stats)
            save_collocations(collocations, col_stats)
            print(f"[{i}/{len(todo)}] saved checkpoint ({base})")

        if i % 5 == 0 or i == len(todo):
            ex_src = examples.get(base, {}).get("source", "skipped")
            print(f"[{i}/{len(todo)}] {base:22s} ex={ex_src:8s} col={len(collocations.get(base, {}).get('items', []))}")

    save_cache(cache)
    save_examples(examples, ex_stats)
    save_collocations(collocations, col_stats)
    print(f"\nDone.")
    print(f"  examples: {EXAMPLES_PATH} ({len(examples)} words) stats={ex_stats}")
    print(f"  collocations: {COLLOCATIONS_PATH} stats={col_stats}")


if __name__ == "__main__":
    main()
