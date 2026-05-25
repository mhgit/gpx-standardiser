"""Application config resolution and YAML schema — not tied to bundled `config/config.yaml` lines."""

from __future__ import annotations

import textwrap

import pytest

from gpx_standardiser import config as app_config


@pytest.fixture(autouse=True)
def clear_config_cache() -> None:
    """Each test sees a fresh `load_app_config` cache (order-independent)."""
    app_config.reset_app_config_cache()
    yield
    app_config.reset_app_config_cache()


def test_missing_config_raises_when_no_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_config, "_path_from_package_source_tree", lambda: None)
    monkeypatch.setattr(app_config, "_path_from_cwd_walk", lambda: None)
    monkeypatch.setattr(app_config, "_bundled_yaml_text_or_none", lambda: None)

    with pytest.raises(FileNotFoundError, match="Missing config\\.yaml"):
        app_config.load_config_yaml_raw()


def test_explicit_config_path_must_exist(tmp_path) -> None:
    missing = tmp_path / "nofile.yaml"
    with pytest.raises(FileNotFoundError, match="No such config file"):
        app_config.load_config_yaml_raw(missing)


def test_well_formed_yaml_file_loads_expected_sets(tmp_path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            join_words:
              - "alice"
              - "bob"
            description_filter:
              - "km"
              - "mile"
            """
        ),
        encoding="utf-8",
    )

    assert app_config.load_join_words(config_file=cfg) == frozenset({"alice", "bob"})
    assert app_config.load_description_filter(config_file=cfg) == frozenset({"km", "mile"})


def test_invalid_yaml_syntax_raises(tmp_path) -> None:
    cfg = tmp_path / "broken.yaml"
    cfg.write_text("join_words: [\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid YAML"):
        app_config.load_app_config(config_file=cfg)


def test_valid_yaml_missing_required_section_raises(tmp_path) -> None:
    cfg = tmp_path / "incomplete.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            join_words:
              - "only"
            """
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing required key"):
        app_config.load_app_config(config_file=cfg)


def test_load_app_config_caches_each_resolved_path_independently(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ADR-0007: memo per resolved path — loading B must not evict cache for A."""

    cfg_a = tmp_path / "one.yaml"
    cfg_b = tmp_path / "two.yaml"
    cfg_a.write_text(
        textwrap.dedent(
            """\
            join_words:
              - "alice"
            description_filter:
              - "z"
            """
        ),
        encoding="utf-8",
    )
    cfg_b.write_text(
        textwrap.dedent(
            """\
            join_words:
              - "bob"
            description_filter:
              - "z"
            """
        ),
        encoding="utf-8",
    )

    reads = 0
    orig_raw = app_config.load_config_yaml_raw

    def counting_raw(*, config_file=None):
        nonlocal reads
        reads += 1
        return orig_raw(config_file=config_file)

    monkeypatch.setattr(app_config, "load_config_yaml_raw", counting_raw)

    first_a = app_config.load_app_config(config_file=cfg_a)
    assert reads == 1
    assert first_a.join_words == frozenset({"alice"})

    first_b = app_config.load_app_config(config_file=cfg_b)
    assert reads == 2
    assert first_b.join_words == frozenset({"bob"})

    second_a = app_config.load_app_config(config_file=cfg_a)
    assert reads == 2
    assert second_a is first_a


def test_load_app_config_caches_by_resolved_discovery_path(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ADR-0007: auto-discovery cache key follows resolved path, not a single \"auto\" slot."""

    cfg_a = tmp_path / "alpha" / "config" / "config.yaml"
    cfg_b = tmp_path / "beta" / "config" / "config.yaml"
    cfg_a.parent.mkdir(parents=True)
    cfg_b.parent.mkdir(parents=True)
    cfg_a.write_text(
        textwrap.dedent(
            """\
            join_words:
              - "alpha"
            description_filter:
              - "z"
            """
        ),
        encoding="utf-8",
    )
    cfg_b.write_text(
        textwrap.dedent(
            """\
            join_words:
              - "beta"
            description_filter:
              - "z"
            """
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(app_config, "_path_from_package_source_tree", lambda: None)
    monkeypatch.setattr(app_config, "_bundled_yaml_text_or_none", lambda: None)

    monkeypatch.setattr(app_config, "_path_from_cwd_walk", lambda: cfg_a)
    first_alpha = app_config.load_app_config()
    assert first_alpha.join_words == frozenset({"alpha"})

    monkeypatch.setattr(app_config, "_path_from_cwd_walk", lambda: cfg_b)
    beta = app_config.load_app_config()
    assert beta.join_words == frozenset({"beta"})
    assert beta is not first_alpha

    monkeypatch.setattr(app_config, "_path_from_cwd_walk", lambda: cfg_a)
    second_alpha = app_config.load_app_config()
    assert second_alpha is first_alpha


@pytest.mark.parametrize(
    ("raw", "expect_substr"),
    [
        (None, "null/no document"),
        ({}, "missing required key"),
        ({"join_words": [], "description_filter": ["x"]}, "join_words.*at least one"),
        ({"description_filter": ["x"], "join_words": ["ok", 1]}, "must be a string"),
        (
            {"join_words": ["ok"], "description_filter": []},
            "description_filter.*at least one",
        ),
        ({"join_words": ["a"], "description_filter": ["b"]}, None),
    ],
)
def test_parse_app_config_document_errors(raw: object, expect_substr: str | None) -> None:
    if expect_substr is None:
        got = app_config.parse_app_config_document(raw)
        assert got.join_words == frozenset({"a"})
        assert got.description_filter == frozenset({"b"})
        return
    with pytest.raises(ValueError, match=expect_substr):
        app_config.parse_app_config_document(raw)


@pytest.mark.parametrize(
    ("raw", "expect_substr"),
    [
        (None, "null/no value"),
        ([], "at least one"),
        (["ok", 1], "must be a string"),
        (["  "], "empty or whitespace"),
        (["a", "b", "a"], None),
    ],
)
def test_parse_string_list_join_words_branch(raw: object, expect_substr: str | None) -> None:
    if expect_substr is None:
        cfg = {"join_words": raw, "description_filter": ["z"]}
        assert app_config.parse_app_config_document(cfg).join_words == frozenset({"a", "b"})
        return
    with pytest.raises(ValueError, match=expect_substr):
        cfg = {"join_words": raw, "description_filter": ["z"]}
        app_config.parse_app_config_document(cfg)
