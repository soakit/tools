"""Load COCA word frequency, phonetics and paraphrases from coca-vocabulary-20000."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

VENDOR = Path(__file__).resolve().parent / "vendor" / "coca-vocabulary-20000"
VOCAB_DIR = VENDOR / "vocabulary"
CACHE = Path(__file__).resolve().parent / "assets" / "coca-index.json"


@dataclass
class CocaEntry:
    rank: int
    word: str
    phonetic_us: str = ""
    phonetic_uk: str = ""
    paraphrase: str = ""
    meanings: list[str] = field(default_factory=list)


@dataclass
class CocaIndex:
    by_rank: dict[int, CocaEntry]
    by_word: dict[str, CocaEntry]
    meta: dict[str, int | str] = field(default_factory=dict)

    def lookup(self, word: str) -> CocaEntry | None:
        return lookup(self.by_word, word)

    def get_rank(self, rank: int) -> CocaEntry | None:
        return self.by_rank.get(rank)


def _parse_phonetic_line(line: str) -> tuple[str, str]:
    parts = re.findall(r"\[([^\]]+)\]", line)
    if not parts:
        return "", ""
    us = parts[0].strip()
    uk = parts[1].strip() if len(parts) > 1 else us
    return us, uk


def _extract_meanings(paraphrase: str) -> list[str]:
    meanings: list[str] = []
    pattern = re.compile(r"((?:[a-z]+(?:\.&?\s*)?)+)\[([^\]]*)\]", re.I)
    for m in pattern.finditer(paraphrase):
        pos = re.sub(r"\s+", "", m.group(1))
        items = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
        for item in items:
            item = item.replace('\\"', '"').strip()
            if item:
                meanings.append(f"{pos} {item}")
    if not meanings:
        text = re.sub(r'\["([^"]+)"(?:,"([^"]+)")*\]', r"\1", paraphrase)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            meanings.append(text)
    return meanings


def _format_paraphrase(raw: str) -> str:
    parts: list[str] = []
    pattern = re.compile(r"((?:[a-z]+(?:\.&?\s*)?)+)\[([^\]]*)\]", re.I)
    for m in pattern.finditer(raw):
        pos = re.sub(r"\s+", "", m.group(1))
        items = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
        zh = "；".join(item.replace('\\"', '"').strip() for item in items if item.strip())
        if zh:
            parts.append(f"{pos} {zh}")
    if parts:
        return "  ".join(parts)
    return raw.strip()


def normalize_key(word: str) -> str:
    w = word.strip().lower().rstrip(".")
    w = re.sub(r"\s*\([^)]*\)\s*", "", w).strip()
    return w


def parse_vocabulary_dir(vocab_dir: Path = VOCAB_DIR) -> CocaIndex:
    by_rank: dict[int, CocaEntry] = {}
    by_word: dict[str, CocaEntry] = {}

    for md_file in sorted(vocab_dir.glob("part*.md")):
        lines = md_file.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            m = re.match(r"^(\d+)\s+(.+?)\s*$", lines[i])
            if not m:
                i += 1
                continue

            rank = int(m.group(1))
            word = m.group(2).strip()
            phonetic_us = phonetic_uk = ""
            paraphrase = ""

            if i + 1 < len(lines) and lines[i + 1].startswith("- ["):
                phonetic_us, phonetic_uk = _parse_phonetic_line(lines[i + 1])
                i += 1
            if i + 1 < len(lines) and lines[i + 1].startswith("- ") and not lines[i + 1].startswith("- ["):
                paraphrase = lines[i + 1][2:].strip()
                i += 1

            entry = CocaEntry(
                rank=rank,
                word=word,
                phonetic_us=phonetic_us,
                phonetic_uk=phonetic_uk,
                paraphrase=_format_paraphrase(paraphrase),
                meanings=_extract_meanings(paraphrase),
            )
            by_rank[rank] = entry

            key = normalize_key(word)
            if key not in by_word or rank < by_word[key].rank:
                by_word[key] = entry

            i += 1

    meta = {
        "total": len(by_rank),
        "unique_words": len(by_word),
        "source": "coca-vocabulary-20000/vocabulary",
    }
    return CocaIndex(by_rank=by_rank, by_word=by_word, meta=meta)


def lookup(by_word: dict[str, CocaEntry], word: str) -> CocaEntry | None:
    keys = {normalize_key(word)}
    base = re.match(r"^([^(=/]+)", word.strip())
    if base:
        keys.add(normalize_key(base.group(1)))
    m = re.match(r"^(.+?)\s*\(([^)]+)\)", word.strip())
    if m:
        keys.add(normalize_key(m.group(1)))
        for part in re.split(r"[,;/]+", m.group(2)):
            keys.add(normalize_key(part))

    best: CocaEntry | None = None
    for key in keys:
        if key in by_word:
            if best is None or by_word[key].rank < best.rank:
                best = by_word[key]
    return best


def _serialize_index(index: CocaIndex) -> dict:
    return {
        "meta": index.meta,
        "by_rank": {str(k): v.__dict__ for k, v in sorted(index.by_rank.items())},
        "by_word": {k: v.__dict__ for k, v in sorted(index.by_word.items())},
    }


def _deserialize_index(raw: dict) -> CocaIndex:
    if "by_rank" in raw:
        by_rank = {int(k): CocaEntry(**v) for k, v in raw["by_rank"].items()}
        by_word = {k: CocaEntry(**v) for k, v in raw["by_word"].items()}
        return CocaIndex(by_rank=by_rank, by_word=by_word, meta=raw.get("meta", {}))

    # legacy: flat word-keyed dict
    by_word = {k: CocaEntry(**v) for k, v in raw.items()}
    by_rank = {e.rank: e for e in by_word.values()}
    return CocaIndex(
        by_rank=by_rank,
        by_word=by_word,
        meta={"total": len(by_rank), "unique_words": len(by_word), "legacy": True},
    )


def load_index(force_rebuild: bool = False) -> CocaIndex:
    if CACHE.exists() and not force_rebuild:
        raw = json.loads(CACHE.read_text(encoding="utf-8"))
        return _deserialize_index(raw)

    index = parse_vocabulary_dir()
    CACHE.write_text(
        json.dumps(_serialize_index(index), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return index


if __name__ == "__main__":
    idx = load_index(force_rebuild=True)
    print(f"COCA by_rank: {len(idx.by_rank)}")
    print(f"COCA by_word: {len(idx.by_word)}")
    print(f"meta: {idx.meta}")
    for w in ("abandon", "arise", "to"):
        e = idx.lookup(w)
        print(f"lookup {w!r} -> rank {e.rank if e else None}")
    e7 = idx.get_rank(7)
    e9 = idx.get_rank(9)
    print(f"rank 7: {e7.word if e7 else None}, rank 9: {e9.word if e9 else None}")
