"""Application YAML: join words and description hints (`ADR-0004`, `ADR-0007`)."""

from __future__ import annotations

import importlib.resources
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

_CONFIG_SUBPATH = Path("config") / "config.yaml"
_BUNDLED_NAME = "bundled_config.yaml"
_CONFIG_LABEL = "config.yaml"

_CacheKey = Path | Literal["bundled"]


@dataclass(frozen=True)
class AppConfigView:
    """Validated contents of the application ``config.yaml`` document."""

    join_words: frozenset[str]
    description_filter: frozenset[str]


# Memo: one parsed view per resolved source path (or ``"bundled"`` for wheel fallback).
_app_config_cache: dict[_CacheKey, AppConfigView] = {}


def reset_app_config_cache() -> None:
    """Clear parsed config memo (primarily for tests)."""

    _app_config_cache.clear()


def _parse_string_list(section: str, raw: object) -> frozenset[str]:
    if raw is None:
        raise ValueError(
            f"{_CONFIG_LABEL}: key {section!r}: expected non-empty YAML list, got null/no value.",
        )

    if not isinstance(raw, list):
        raise ValueError(f"{_CONFIG_LABEL}: key {section!r} must be a YAML list of strings.")

    out: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, str):
            raise ValueError(
                f"{_CONFIG_LABEL}: {section}[{i}] must be a string, not {type(item).__name__}.",
            )

        w = item.strip().lower()
        if not w:
            raise ValueError(
                f"{_CONFIG_LABEL}: {section}[{i}] must not be empty or whitespace-only.",
            )

        out.add(w)

    if not out:
        raise ValueError(f"{_CONFIG_LABEL}: key {section!r} must contain at least one entry.")

    return frozenset(out)


def parse_app_config_document(raw: object) -> AppConfigView:
    """
    Validate a YAML-parsed mapping (used by loaders and focused tests).

    Root must contain ``join_words`` and ``description_filter`` lists.
    """
    if raw is None:
        raise ValueError(f"{_CONFIG_LABEL}: expected a YAML mapping, got null/no document.")

    if not isinstance(raw, dict):
        raise ValueError(
            f"{_CONFIG_LABEL}: root must be a mapping with keys "
            '"join_words" and "description_filter".',
        )

    missing = [k for k in ("join_words", "description_filter") if k not in raw]
    if missing:
        raise ValueError(
            f"{_CONFIG_LABEL}: missing required key(s): {', '.join(repr(k) for k in missing)}.",
        )

    return AppConfigView(
        join_words=_parse_string_list("join_words", raw["join_words"]),
        description_filter=_parse_string_list("description_filter", raw["description_filter"]),
    )


def _path_from_package_source_tree() -> Path | None:
    """If running from a checkout, find ``config/config.yaml`` next to ``pyproject.toml``."""

    here = Path(__file__).resolve()
    for parent in here.parents:
        project = parent / "pyproject.toml"
        candidate = parent / _CONFIG_SUBPATH
        if project.is_file() and candidate.is_file():
            return candidate
    return None


def _path_from_cwd_walk() -> Path | None:
    """Walk parents of the current working directory for ``config/config.yaml``."""

    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / _CONFIG_SUBPATH
        if candidate.is_file():
            return candidate
    return None


def _bundled_yaml_text_or_none() -> str | None:
    """YAML text from wheels that ship ``bundled_config.yaml`` beside the package."""

    root = importlib.resources.files("gpx_standardiser")
    blob = root.joinpath(_BUNDLED_NAME)
    if not blob.is_file():
        return None
    text = blob.read_text(encoding="utf-8")
    return text.strip() if text.strip() else None


def _resolve_config_source(config_file: Path | None = None) -> _CacheKey:
    """Return cache key for discovery: resolved path or ``"bundled"``."""

    if config_file is not None:
        p = Path(config_file).expanduser().resolve()
        if p.is_file():
            return p
        raise FileNotFoundError(f"No such config file: {p}")

    for resolver in (_path_from_package_source_tree, _path_from_cwd_walk):
        resolved = resolver()
        if resolved is not None:
            return resolved

    bundled_text = _bundled_yaml_text_or_none()
    if bundled_text is not None:
        return "bundled"

    sub = "/".join(_CONFIG_SUBPATH.parts)
    hint = (
        f"Missing {_CONFIG_LABEL}: create {sub} at your checkout root,"
        " install from a wheel with bundled defaults, or pass -c/--config PATH."
    )
    raise FileNotFoundError(hint)


def load_config_yaml_raw(config_file: Path | None = None) -> str:
    """Read UTF-8 text for ``config.yaml`` (`ADR-0007`). Raises if missing."""

    source = _resolve_config_source(config_file)
    if source == "bundled":
        bundled_text = _bundled_yaml_text_or_none()
        assert bundled_text is not None
        return bundled_text
    return source.read_text(encoding="utf-8")


def load_app_config(*, config_file: Path | None = None) -> AppConfigView:
    """Load from disk / bundle (first call per distinct ``config_file`` key) or cache."""

    cache_key = _resolve_config_source(config_file)
    hit = _app_config_cache.get(cache_key)
    if hit is not None:
        return hit

    text = load_config_yaml_raw(config_file=config_file)
    try:
        raw: Any = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"{_CONFIG_LABEL}: invalid YAML ({exc})") from exc

    parsed = parse_app_config_document(raw)
    _app_config_cache[cache_key] = parsed
    return parsed


def load_join_words(*, config_file: Path | None = None) -> frozenset[str]:
    """Subset: tokens dropped as English-style join words (ADR-0004)."""

    return load_app_config(config_file=config_file).join_words


def load_description_filter(*, config_file: Path | None = None) -> frozenset[str]:
    """Subset: unit/meta tokens dropped from basename hints."""

    return load_app_config(config_file=config_file).description_filter
