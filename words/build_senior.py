#!/usr/bin/env python3
"""Build assets/senior.json from 3500.docx, excluding 三年级 vocabulary."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from docx import Document

ASSETS = Path(__file__).resolve().parent / "assets"
DOCX_PATH = ASSETS / "3500.docx"
GRADE3_PATH = ASSETS / "三年级.json"
OUTPUT_PATH = ASSETS / "senior.json"

POS = r"(?:art|n|v|adj|adv|prep|conj|pron|num|int|abbr|aux|vi|vt|modal)"
POS_RE = re.compile(rf"\s({POS})\.?\b", re.I)
POS_INLINE_RE = re.compile(rf"\b({POS})\.?\s", re.I)
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
FOOTER_RE = re.compile(r"^山东高考")
LETTER_RE = re.compile(r"^[A-Z]$")


def normalize_key(word: str) -> str:
    w = word.strip().lower()
    w = re.sub(r"\s*\([^)]*\)", "", w)
    w = re.sub(r"\s*=.*$", "", w)
    w = re.sub(r"\s+modal\s*$", "", w, flags=re.I)
    return w.strip().rstrip(".")


def clean_word(word: str) -> str:
    word = word.strip()
    word = re.sub(r"\s+modal\s*$", "", word, flags=re.I)
    word = re.sub(r"(?<=[a-zA-Z])\d+", "", word)
    word = re.sub(r"\s+", " ", word).strip()
    return word


def preprocess_line(line: str) -> str:
    line = re.sub(rf"(\d)({POS})\.", r"\1 \2.", line, flags=re.I)
    line = re.sub(rf"([）)])({POS})\.", r"\1 \2.", line, flags=re.I)
    return line


def split_at_chinese(line: str) -> tuple[str, str]:
    depth = 0
    for i, ch in enumerate(line):
        if ch == "（":
            depth += 1
        elif ch == "）" and depth:
            depth -= 1
        elif CHINESE_RE.match(ch) and depth == 0:
            return line[:i].strip(), line[i:].strip()
    return line.strip(), ""


def normalize_definition(definition: str) -> str:
    definition = definition.strip()
    definition = re.sub(r"^modal\s+", "", definition, flags=re.I)
    return definition


def parse_entry(line: str) -> tuple[str, str] | None:
    line = preprocess_line(line.strip())
    if not line or FOOTER_RE.search(line):
        return None

    m = POS_RE.search(line)
    if not m:
        m = POS_INLINE_RE.search(line)
    if m:
        word = clean_word(line[: m.start()].strip())
        definition = normalize_definition(line[m.start() :].strip())
        if word and definition:
            return word, definition

    if "=" in line and line.split("=", 1)[0].strip().isascii():
        left, rest = line.split("=", 1)
        pos = POS_RE.search(rest) or POS_INLINE_RE.search(rest)
        if pos:
            word = clean_word(left.strip())
            definition = normalize_definition(rest[pos.start() :].strip())
            if word and definition:
                return word, definition

    word, definition = split_at_chinese(line)
    word = clean_word(word.rstrip(".,;"))
    if word and definition:
        return word, definition
    return None


def should_exclude(word: str, grade3_keys: set[str]) -> bool:
    key = normalize_key(word)
    if key not in grade3_keys:
        return False
    if "(" in word or "modal" in word.lower() or "=" in word:
        return False
    bare = re.sub(r"\s*\([^)]*\).*", "", word.strip().lower())
    bare = re.sub(r"\s*=.*", "", bare).strip()
    return bare == key


def load_grade3_keys(path: Path = GRADE3_PATH) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    keys: set[str] = set()
    for semester in ("上", "下"):
        for unit in data[semester]:
            for item in unit["words"]:
                keys.add(normalize_key(item["word"]))
    return keys


def parse_docx(path: Path = DOCX_PATH) -> tuple[list[dict], int]:
    doc = Document(path)
    entries: list[dict] = []
    letter = "?"
    unknown = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if LETTER_RE.fullmatch(text):
            letter = text
            continue

        parsed = parse_entry(text)
        if not parsed:
            unknown += 1
            continue

        word, definition = parsed
        entries.append({"letter": letter, "word": word, "definition": definition})

    return entries, unknown


def build_senior(*, exclude_grade3: bool = True) -> dict:
    grade3_keys = load_grade3_keys() if exclude_grade3 else set()
    raw_entries, unknown = parse_docx()

    kept: list[dict] = []
    removed = 0
    for item in raw_entries:
        if exclude_grade3 and should_exclude(item["word"], grade3_keys):
            removed += 1
            continue
        kept.append(item)

    by_letter: dict[str, list[dict]] = defaultdict(list)
    for item in kept:
        by_letter[item["letter"]].append({"word": item["word"], "definition": item["definition"]})

    words_by_letter = [
        {"letter": letter, "words": by_letter[letter]}
        for letter in sorted(by_letter)
    ]

    return {
        "source": DOCX_PATH.name,
        "excluded_from": GRADE3_PATH.name if exclude_grade3 else "",
        "stats": {
            "source_words": len(raw_entries),
            "removed": removed,
            "remaining": len(kept),
            "letters": len(words_by_letter),
            "unknown_lines": unknown,
        },
        "words_by_letter": words_by_letter,
    }


def main() -> None:
    payload = build_senior()
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    stats = payload["stats"]
    print(f"Saved {OUTPUT_PATH}")
    print(
        f"  source={stats['source_words']} removed={stats['removed']} "
        f"remaining={stats['remaining']} unknown={stats['unknown_lines']}"
    )


if __name__ == "__main__":
    main()
