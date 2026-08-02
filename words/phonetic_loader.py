"""Supplement phonetics from cache or Free Dictionary API."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from examples_loader import normalize_key

ASSETS = Path(__file__).resolve().parent / "assets"
CACHE_PATH = ASSETS / "phonetics.json"

_phonetics: dict[str, str] | None = None
API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

# Direct IPA for proper nouns, abbreviations, and phrases not in the API.
PHONETIC_OVERRIDES: dict[str, str] = {
    "africa": "ˈæfrɪkə",
    "america": "əˈmerɪkə",
    "asia": "ˈeɪʒə",
    "atlantic": "ətˈlæntɪk",
    "europe": "ˈjʊərəp",
    "oceania": "ˌəʊʃiˈɑːniə",
    "mm": "ˈmɪlimiːtə",
    "millimetre": "ˈmɪlimiːtə",
    "aluminium": "ˌæljəˈmɪniəm",
    "beancurd": "ˌbiːn ˈkɜːd",
    "beddings": "ˈbedɪŋz",
    "centigrade": "ˈsentɪɡreɪd",
    "dustbin": "ˈdʌstbɪn",
    "grandparents": "ˈɡrænpeərənts",
    "hardworking": "ˌhɑːd ˈwɜːkɪŋ",
    "human being": "ˈhjuːmən ˈbiːɪŋ",
    "minibus": "ˈmɪnibʌs",
    "oilfield": "ˈɔɪlfiːld",
    "ought": "ɔːt",
    "passer-by": "ˌpɑːsə ˈbaɪ",
    "ping-pong": "ˈpɪŋ pɒŋ",
    "salesgirl": "ˈseɪlzɡɜːl",
    "seashell": "ˈsiːʃel",
    "semicircle": "ˈsemisɜːkl",
    "sharpener": "ˈʃɑːpənə",
    "sideway": "ˈsaɪdweɪ",
    "sunburnt": "ˈsʌnbɜːnt",
    "table tennis": "ˈteɪbəl ˈtenɪs",
    "videophone": "ˈvɪdiəʊfəʊn",
    "waiting-room": "ˈweɪtɪŋ ruːm",
    "washroom": "ˈwɒʃruːm",
    "b.c.": "ˌbiː ˈsiː",
    "b.c": "ˌbiː ˈsiː",
    "bc": "ˌbiː ˈsiː",
    "apro": "ˌæprəˈpəʊ",
    "forgetful": "fəˈɡetfʊl",
    "cd": "ˌsiː ˈdiː",
    "dvd": "ˌdiː viː ˈdiː",
    "p.c.": "ˌpiː ˈsiː",
    "pc": "ˌpiː ˈsiː",
    "p.e.": "ˌpiː ˈiː",
    "pe": "ˌpiː ˈiː",
    "pm": "ˌpiː ˈem",
    "p.m.": "ˌpiː ˈem",
    "vcd": "ˌviː siː ˈdiː",
    "e-mail": "ˈiːmeɪl",
    "email": "ˈiːmeɪl",
}

# Map to alternate dictionary lookup forms.
PHONETIC_ALIASES: dict[str, str] = {
    "offence": "offense",
    "woollen": "woolen",
    "yoghurt": "yogurt",
    "questionaire": "questionnaire",
    "relevent": "relevant",
    "apro": "apropos",
}


def load_phonetics(*, force: bool = False) -> dict[str, str]:
    global _phonetics
    if _phonetics is not None and not force:
        return _phonetics
    if CACHE_PATH.exists():
        raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        _phonetics = raw.get("phonetics", raw)
    else:
        _phonetics = {}
    return _phonetics


def lookup_keys(word: str) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        for part in re.split(r"[/=]", raw):
            part = re.sub(r"\s*\([^)]*\)", "", part)
            part = re.sub(r"\s+modal\s*$", "", part, flags=re.I)
            part = re.sub(r"\s+v&?\s*$", "", part, flags=re.I)
            part = re.sub(r"\s+n\s.*$", "", part, flags=re.I)
            part = re.sub(r"[^a-zA-Z\s\-'.]", " ", part).strip()
            if not part:
                continue
            key = normalize_key(part)
            if key and key not in seen:
                seen.add(key)
                keys.append(key)
            first = re.match(r"^([a-zA-Z\-']+)", part)
            if first:
                fk = normalize_key(first.group(1))
                if fk and fk not in seen:
                    seen.add(fk)
                    keys.append(fk)

    add(word.strip())
    base = re.match(r"^([^(=/]+)", word.strip())
    if base:
        add(base.group(1))
    return keys


def _clean_ipa(text: str) -> str:
    text = text.strip().strip("/[]")
    return text


def fetch_from_api(word: str) -> str:
    url = API_URL.format(word=urllib.request.quote(word.lower()))
    req = urllib.request.Request(url, headers={"User-Agent": "words-tool/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return ""

    if not isinstance(data, list) or not data:
        return ""

    for item in data:
        for ph in item.get("phonetics", []):
            text = ph.get("text", "").strip()
            if text:
                return _clean_ipa(text)
    return ""


def lookup_phonetic(word: str, *, fetch: bool = False) -> str:
    bank = load_phonetics()
    for key in lookup_keys(word):
        if key in bank and bank[key]:
            return bank[key]
        if key in PHONETIC_OVERRIDES:
            return PHONETIC_OVERRIDES[key]
        alias = PHONETIC_ALIASES.get(key)
        if alias:
            if alias in bank and bank[alias]:
                return bank[alias]
            if alias in PHONETIC_OVERRIDES:
                return PHONETIC_OVERRIDES[alias]
            if fetch:
                ipa = fetch_from_api(alias)
                if ipa:
                    bank[key] = ipa
                    return ipa
    if not fetch:
        return ""
    for key in lookup_keys(word):
        ipa = fetch_from_api(key)
        if ipa:
            bank[key] = ipa
            return ipa
    return ""


def save_phonetics(bank: dict[str, str]) -> None:
    payload = {"meta": {"total": len(bank)}, "phonetics": bank}
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    global _phonetics
    _phonetics = bank
