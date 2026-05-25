"""Bundled configuration (package data)."""

from __future__ import annotations

import importlib.resources
from typing import Any

import yaml

_CONFIG_PKG = "gpx_standardiser.config"
_JOIN_FILENAME = "join_words.yaml"

_cached_join_words: frozenset[str] | None = None


def _parse_join_words_yaml(raw: object) -> frozenset[str]:
    if raw is None:
        raise ValueError("join_words.yaml: expected a non-empty YAML list, got null/no document.")

    if not isinstance(raw, list):
        raise ValueError(
            "join_words.yaml: root must be a YAML list of strings (one join word per line).",
        )

    out: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, str):
            raise ValueError(
                f"join_words.yaml: entry {i} must be a string, not {type(item).__name__}."
            )

        w = item.strip().lower()
        if not w:
            raise ValueError(f"join_words.yaml: entry {i} must not be empty or whitespace-only.")

        out.add(w)

    if not out:
        raise ValueError("join_words.yaml: list must contain at least one join word.")

    return frozenset(out)


def load_join_words() -> frozenset[str]:
    """Load join words from bundled ``join_words.yaml``. Raises if the file is missing or invalid."""

    global _cached_join_words

    if _cached_join_words is not None:
        return _cached_join_words

    root = importlib.resources.files(_CONFIG_PKG)
    path = root.joinpath(_JOIN_FILENAME)
    if not path.is_file():
        msg = (
            f"Required application config is missing: {_JOIN_FILENAME!r} is not bundled "
            f"under package {_CONFIG_PKG!r}."
        )
        raise FileNotFoundError(msg)

    text = path.read_text(encoding="utf-8")
    try:
        raw: Any = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"join_words.yaml: invalid YAML ({exc})") from exc

    _cached_join_words = _parse_join_words_yaml(raw)
    return _cached_join_words
