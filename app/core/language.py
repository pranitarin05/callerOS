"""Language detection for Hindi / English / Hinglish conversations."""

import re
from typing import Optional

SUPPORTED_LANGUAGES = {"en", "hi", "hinglish", "auto"}

DEVANAGARI = re.compile(r"[\u0900-\u097F]")

ROMANIZED_HINDI = {
    "namaste", "aap", "aapka", "aapki", "aapko", "kya", "hai", "hain", "ho",
    "nahi", "nahin", "chahte", "chahie", "chahiye", "kar", "karna", "karte",
    "kal", "abhi", "jaldi", "shuru", "surat", "dhanyavaad", "dhanyabad",
    "theek", "achha", "accha", "bataiye", "bataiye", "milna", "chahte hain",
    "karna hai", "bahut", "thoda", "farq", "samajh", "samajh gaya", "kyun",
    "kyon", "kaise", "kahan", "kitna", "paise", "rupaye", "rupees",
}

ENGLISH_MARKERS = {
    "hello", "yes", "no", "please", "demo", "interested", "follow", "up",
    "call", "schedule", "need", "we", "our", "team", "product", "price",
}


def detect_language(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return "en"
    if DEVANAGARI.search(raw):
        return "hi"

    lower = raw.lower()
    words = set(re.findall(r"[a-z]+", lower))
    hindi_hits = len(words & ROMANIZED_HINDI)
    for phrase in ("chahte hain", "karna hai", "samajh gaya"):
        if phrase in lower:
            hindi_hits += 1
    english_hits = len(words & ENGLISH_MARKERS)

    if hindi_hits >= 2:
        return "hinglish" if english_hits >= 1 else "hi"
    return "en"


def resolve_language(text: str, preferred: Optional[str] = None) -> str:
    detected = detect_language(text)
    pref = (preferred or "auto").strip().lower()
    if pref not in SUPPORTED_LANGUAGES or pref == "auto":
        return detected
    if detected != "en":
        return detected
    if not DEVANAGARI.search(text or "") and len(re.findall(r"[a-z]+", (text or "").lower())) < 8:
        return pref
    return detected


def language_label(code: Optional[str]) -> str:
    return {
        "en": "English",
        "hi": "Hindi",
        "hinglish": "Hinglish",
        "auto": "Auto-detect",
    }.get((code or "auto").strip().lower(), "English")
