"""Heuristic description hints from legacy filenames (ADR-0004)."""

from __future__ import annotations

import re
from pathlib import Path

from gpx_standardiser.config import load_description_filter, load_join_words

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


def _drop_join_word_tokens(tokens: list[str], join_words: frozenset[str]) -> list[str]:
    """Remove tokens whose lowercase form appears in ``join_words``."""

    return [t for t in tokens if t.lower() not in join_words]


def _keep_token(tok: str, noise: frozenset[str]) -> bool:
    t = tok.strip()
    if not t:
        return False
    if _TIER.match(t):
        return False
    if t.lower() in noise:
        return False
    if re.fullmatch(r"\d+", t):
        return False
    if _NUMBER_UNIT.match(t):
        return False
    if not re.search(r"[A-Za-z]", t):
        return False
    return True


def _hint_from_plain_suffix(
    fragment: str,
    *,
    join_words: frozenset[str],
    noise: frozenset[str],
) -> str | None:
    cand = [_t for _t in _split_tokens(fragment.strip()) if _keep_token(_t, noise)]
    cand = _drop_join_word_tokens(cand, join_words)
    return "-".join(cand) if cand else None


def description_hint_from_original(filename: str, *, config_file: Path | None = None) -> str:
    """
    Produce a hyphen-joined starter string from basename (with or without `.gpx`).

    Loads ``join_words`` / ``description_filter`` via ``ADR-0007``
    (``config_file`` when given, otherwise auto-resolve ``config/config.yaml``).

    Priority:
      1. Text after the final `@` (canonical exported names).
      2. Else text after the final `^` (legacy uploads / historical experiment).
      3. Else tokenise what remains once numbers/units/noise stripped.
    """
    join_words = load_join_words(config_file=config_file)
    noise = load_description_filter(config_file=config_file)

    stem = filename.removesuffix(".gpx")
    remainder = stem

    if "@" in stem:
        before_at, _, after_at = stem.rpartition("@")
        hint = _hint_from_plain_suffix(after_at, join_words=join_words, noise=noise)
        if hint:
            return hint
        remainder = before_at

    if "^" in remainder:
        before_hat, _, after_hat = remainder.rpartition("^")
        hint = _hint_from_plain_suffix(after_hat, join_words=join_words, noise=noise)
        if hint:
            return hint
        remainder = before_hat

    filtered = [_t for _t in _split_tokens(remainder) if _keep_token(_t, noise)]
    if not filtered:
        return ""

    deduped: list[str] = []
    for t in filtered:
        norm = "-".join(chunk for chunk in re.split(r"\s+", t.replace("_", " ").strip()) if chunk)
        compare = norm.lower()
        if not deduped or deduped[-1].lower() != compare:
            deduped.append(norm)
    deduped = _drop_join_word_tokens(deduped, join_words)
    return "-".join(deduped)
