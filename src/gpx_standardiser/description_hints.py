"""Heuristic description hints from legacy filenames (ADR-0004)."""

from __future__ import annotations

import re

from gpx_standardiser.config import load_join_words

# Tokens listed in config/join_words.yaml are dropped wherever they appear as whole
# tokens after splitting (case-insensitive).
_JOINING_STOPWORDS = load_join_words()

# Lowercase tokens treated as units / meta (not place names).
_NOISE_TOKENS = frozenset(
    {
        "km",
        "k",
        "kms",
        "ml",
        "mls",
        "miles",
        "mile",
        "mi",
        "m",
        "mtrs",
        "mtr",
        "ft",
        "ccw",
        "cw",
        "clockwise",
        "climbing",
    }
)

# Pattern: ability tier T1–T6 (case-insensitive).
_TIER = re.compile(r"^T\d+$", re.IGNORECASE)

# Leading number + common unit suffix (48m, 100k, 82km, 115km, ...).
_NUMBER_UNIT = re.compile(
    r"^\d+(?:km|[kKmM]|mls|ml|miles|mile|mi|mtrs|mtr|ft|climbing|mph|m)$",
    re.IGNORECASE,
)


def _split_tokens(text: str) -> list[str]:
    """Split on runs of separators without dropping internal apostrophes."""
    parts = re.split(r"[_\s\-]+", text)
    return [p for p in parts if p]


def _drop_join_word_tokens(tokens: list[str]) -> list[str]:
    """Remove any token whose lowercase form is in the join-word list (not case-sensitive)."""

    return [t for t in tokens if t.lower() not in _JOINING_STOPWORDS]


def _keep_token(tok: str) -> bool:
    t = tok.strip()
    if not t:
        return False
    if _TIER.match(t):
        return False
    if t.lower() in _NOISE_TOKENS:
        return False
    if re.fullmatch(r"\d+", t):
        return False
    if _NUMBER_UNIT.match(t):
        return False
    # Need at least one letter for “word-like” hints.
    if not re.search(r"[A-Za-z]", t):
        return False
    return True


def _hint_from_plain_suffix(fragment: str) -> str | None:
    cand = [_t for _t in _split_tokens(fragment.strip()) if _keep_token(_t)]
    cand = _drop_join_word_tokens(cand)
    return "-".join(cand) if cand else None


def description_hint_from_original(filename: str) -> str:
    """
    Produce a hyphen-joined starter string from basename (with or without `.gpx`).

    Priority:
      1. Text after the final `@` (canonical exported names).
      2. Else text after the final `^` (legacy uploads / historical experiment).
      3. Else tokenise what remains once numbers/units/noise stripped.
    """
    stem = filename.removesuffix(".gpx")
    remainder = stem

    if "@" in stem:
        before_at, _, after_at = stem.rpartition("@")
        hint = _hint_from_plain_suffix(after_at)
        if hint:
            return hint
        remainder = before_at

    if "^" in remainder:
        before_hat, _, after_hat = remainder.rpartition("^")
        hint = _hint_from_plain_suffix(after_hat)
        if hint:
            return hint
        remainder = before_hat

    filtered = [_t for _t in _split_tokens(remainder) if _keep_token(_t)]
    if not filtered:
        return ""

    deduped: list[str] = []
    for t in filtered:
        norm = "-".join(chunk for chunk in re.split(r"\s+", t.replace("_", " ").strip()) if chunk)
        compare = norm.lower()
        if not deduped or deduped[-1].lower() != compare:
            deduped.append(norm)
    deduped = _drop_join_word_tokens(deduped)
    return "-".join(deduped)
