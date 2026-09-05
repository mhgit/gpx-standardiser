# Repository Guidelines

`gpx-standardiser` is a CLI that renames a cycling club's GPX files to a canonical,
sortable format. It reads each route's geometry, derives distance and ascent, and copies
the file out under a name built from those metrics plus a cleaned-up description.

This file is the single source of truth for agent instructions; `CLAUDE.md` imports it.

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
Ruff runs at line length 100; the build backend is `hatchling`; the CLI is `typer`.

`pytest` fails under 80% coverage (`cli.py` omitted). `pythonpath = ["tests"]` in `pyproject.toml`
is what makes `from fixtures.gpx_build import track_xml_simple` work — build GPX fixtures with that
helper rather than hand-written XML, and compare metrics with `pytest.approx`.

Ruff 0.16 lints and formats Python code fences inside Markdown, so `ruff check .` / `ruff format
--check .` cover the docs too. Today every fence in `README.md`, `CONTRIBUTING.md`, and `docs/` is
`bash`/`text`/`mermaid`; adding a ```python fence puts it under the formatter. The same pass reads
every `.md` file end to end, so a non-UTF-8 file with a `.md` extension fails the gate outright.

## Architecture

A Typer CLI with two commands over a set of pure, typed helpers — functional core, thin shell.
`cli.py` is routing and I/O only; new logic belongs in a module with a mirrored
`tests/test_<module>.py`. Domain failures raise a custom hierarchy (`NamingError`,
`GpxAnalysisError`) rather than bare exceptions.

Pipeline: `gpx_stats` (metrics from geometry) → `description_hints` (slug guess from the old
basename, needs config) → `naming` (canonical stem + collision suffixes) → `units` (metric maths
converted at the display/filename boundary) → either stdout (`plan`, `plan_report`) or a copy
(`rename`).

**Plan then execute**: `plan` is a dry run that previews and reports; `rename` performs the copy.

Load-bearing invariants, each backed by an ADR in `docs/adr/`:

- **`rename` copies; sources are never modified** (ADR-0005). `write_renamed_copy` reads the source
  text, rewrites `<name>`, and writes to the destination.
- **Metrics come from the first `<trk>` only** (ADR-0003). Extra tracks and any `<rte>` produce
  non-fatal `TrackMetrics.warnings`; missing tracks or fewer than two elevation points raise
  `GpxAnalysisError`, which callers turn into a per-file skip, not an abort. Distance is Haversine.
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

## Layout

- `src/gpx_standardiser/` — source; `cli.py` is the entry point.
- `tests/` — suite, with `tests/fixtures/gpx_build.py` generating deterministic GPX blobs.
- `config/config.yaml` — `join_words` (basename cleaning) and `description_filter` (metadata noise).
- `docs/design.md` — architecture overview and backlog; `docs/adr/*.md` — the decision records.
- `pyproject.toml` — manifest, dependencies, and all tool configuration.

## Branches

`develop` is the working branch — CI runs on `main` and `develop`, and Dependabot version updates
target `develop`, which is then promoted to `main`. (`CONTRIBUTING.md` still describes the
fork → PR-to-`main` flow for outside contributors.)
