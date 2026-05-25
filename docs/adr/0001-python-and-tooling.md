---
status: Accepted
---
# ADR-0001: Python and tooling

## Context

The tool must run locally for club members comfortable with terminals. Python is already installed; static binaries were considered but deprioritized.

## Decision

- Language: Python 3.14+ compatible (supports 3.12+ in `requires-python`).
- Package and environment management **exclusively** via **[uv](https://docs.astral.sh/uv/)** — no pip/poetry in project docs or CI examples.
- Tests with **pytest** and **pytest-cov** only.

## Consequences

Contributors sync with `uv sync` and invoke the CLI via `uv run gpx-standardiser`.
