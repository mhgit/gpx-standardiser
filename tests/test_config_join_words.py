"""Bundled join_words.yaml loading and validation."""

import importlib.resources

import pytest

from gpx_standardiser import config as app_config


def test_load_join_words_returns_bundled_defaults() -> None:
    words = app_config.load_join_words()
    assert "to" in words
    assert "from" in words
    assert "occ" in words
    assert len(words) == 16


def test_missing_join_words_file_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_config, "_cached_join_words", None)

    class _NoFile:
        def is_file(self) -> bool:
            return False

    class _Root:
        def joinpath(self, _name: str) -> _NoFile:
            return _NoFile()

    monkeypatch.setattr(importlib.resources, "files", lambda _pkg: _Root())

    with pytest.raises(FileNotFoundError, match="Required application config is missing"):
        app_config.load_join_words()


@pytest.mark.parametrize(
    ("raw", "expect_substr"),
    [
        (None, "null/no document"),
        ({}, "YAML list"),
        ([], "at least one"),
        (["ok", 1], "must be a string"),
        (["  "], "empty or whitespace"),
        (["a", "b", "a"], None),  # deduped, still 2
    ],
)
def test_parse_join_words_errors(raw: object, expect_substr: str | None) -> None:
    if expect_substr is None:
        assert app_config._parse_join_words_yaml(raw) == frozenset({"a", "b"})
        return
    with pytest.raises(ValueError, match=expect_substr):
        app_config._parse_join_words_yaml(raw)
