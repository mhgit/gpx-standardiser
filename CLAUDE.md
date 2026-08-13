# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                          # or `uv sync --all-groups --frozen` as CI does
uv run gpx-standardiser plan --route-files ./inbound-files/
uv run gpx-standardiser rename --route-files ./inbound-files/ -o ./outbound-files/

uv run ruff check .              # the three CI gates, in order
uv run ruff format --check .
uv run pytest

uv run pytest tests/test_naming.py::test_format_stem_happy_path   # single test
uv run pytest -k naming --no-cov                              # skip the coverage gate while iterating
```

**uv only** — ADR-0001 forbids pip/poetry in docs and CI. Python is pinned to 3.14 in
`.python-version`; `requires-python` is `>=3.12` and Ruff targets `py312`, so don't use 3.13+ syntax.

`pytest` fails under 80% coverage (`cli.py` omitted). `pythonpath = ["tests"]` in `pyproject.toml`
is what makes `from fixtures.gpx_build import track_xml_simple` work — build GPX fixtures with that
helper rather than hand-written XML.

Ruff 0.16 lints and formats Python code fences inside Markdown, so `ruff check .` / `ruff format
--check .` cover the docs too. Today every fence in `README.md`, `CONTRIBUTING.md`, and `docs/` is
`bash`/`text`/`mermaid`; adding a ```python fence puts it under the formatter.

## Architecture

A Typer CLI with two commands over a set of pure, typed helpers. `cli.py` is routing and I/O only —
new logic belongs in a module with a mirrored `tests/test_<module>.py`.

Pipeline: `gpx_stats` (metrics from geometry) → `description_hints` (slug guess from the old
basename, needs config) → `naming` (canonical stem + collision suffixes) → `units` (metric maths
converted at the display/filename boundary) → either stdout (`plan`, `plan_report`) or a copy
(`rename`).

Load-bearing invariants, each backed by an ADR in `docs/adr/`:

- **`rename` copies; sources are never modified** (ADR-0005). `write_renamed_copy` reads the source
  text, rewrites `<name>`, and writes to the destination.
- **Metrics come from the first `<trk>` only** (ADR-0003). Extra tracks and any `<rte>` produce
  non-fatal `TrackMetrics.warnings`; missing tracks or fewer than two elevation points raise
  `GpxAnalysisError`, which callers turn into a per-file skip, not an abort.
- **Ascent is summed over an 11-sample centred moving average**, not raw `<ele>` deltas — that's the
  whole point of `smooth_elevation_moving_average`, and changing the window changes every filename.
- **All internal maths is metric**; `units.convert_for_output` converts once, at the edge. Default
  output is **imperial** (`053mls-1234ft@Desc.gpx`); `--units metric` gives `085km-376m@Desc.gpx`
  (ADR-0002). Distance is zero-padded to at least three digits for lexicographic sorting.
- **GPX `<name>` is the description only** (ADR-0004), never the metric-prefixed filename.
- **Config is mandatory and fails at startup** (ADR-0007). `config/config.yaml` supplies
  `join_words` and `description_filter`; discovery is checkout layout (`pyproject.toml` sibling) →
  walk up from cwd → `bundled_config.yaml` in a wheel, overridable with `-c/--config`. Parsed views
  are memoised per resolved path — call `reset_app_config_cache()` in tests that write their own
  YAML. If you move `config/config.yaml`, keep both
  `tool.hatch.build.targets.{sdist,wheel}.force-include` in `pyproject.toml` coherent.
- **`allocate_unique_gpx_basename` returns `None` to mean "skip this file"** — the destination
  basename exists on disk and `--force` wasn't given. A returned name is already reserved in the
  caller's `occupied` set. `plan -i` passes `check_destination_files=False`, so its preview shows
  intra-run `-2`/`-3` numbering but ignores files already in any output folder.
- **`inbound-files/` / `outbound-files/` are gitignored and must never be hardcoded** — callers pass
  paths (ADR-0005).

Scope is deliberately narrow: local files, no upload/host API integration. Behaviour changes should
land alongside the relevant ADR; `docs/design.md` carries the backlog and what was rejected.

## Branches

`develop` is the working branch — CI runs on `main` and `develop`, and Dependabot version updates
target `develop`, which is then promoted to `main`. (`CONTRIBUTING.md` still describes the
fork → PR-to-`main` flow for outside contributors.)
