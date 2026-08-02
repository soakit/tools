#!/usr/bin/env python3
"""Fetch missing phonetics and save to assets/phonetics.json."""

from __future__ import annotations

import time
from pathlib import Path

from coca_loader import load_index
from generate_pdf import ASSETS, WordEntry, enrich_with_coca, load_words
from phonetic_loader import fetch_from_api, load_phonetics, lookup_keys, save_phonetics

SENIOR = ASSETS / "senior.json"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Supplement missing phonetics")
    parser.add_argument("--delay", type=float, default=0.15)
    args = parser.parse_args()

    coca = load_index()
    entries = load_words(SENIOR, coca)
    bank = load_phonetics(force=True)
    missing = [e for e in entries if not e.phonetic]

    print(f"missing phonetics: {len(missing)}")
    added = 0
    for i, entry in enumerate(missing, 1):
        found = ""
        for key in lookup_keys(entry.word):
            if key in bank and bank[key]:
                found = bank[key]
                break
            ipa = fetch_from_api(key)
            if ipa:
                bank[key] = ipa
                found = ipa
                added += 1
                break
            if args.delay:
                time.sleep(args.delay)

        if found:
            entry.phonetic = found
        print(f"[{i}/{len(missing)}] {entry.base_word:20s} -> {found or '(none)'}")

    save_phonetics(bank)
    still = sum(1 for e in entries if not (e.phonetic or any(bank.get(k) for k in lookup_keys(e.word))))
    print(f"\nSaved {len(bank)} entries to assets/phonetics.json (+{added} new)")
    print(f"Still missing after supplement: {still}")


if __name__ == "__main__":
    main()
