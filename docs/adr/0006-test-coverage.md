---
status: Accepted
---
# ADR-0006: Test coverage thresholds

## Context

Heavy logic sits in parsers and naming; CLI should remain thin glue.

## Decision

- Aim for **≥80% line coverage** on **`gpx_stats`**, **`naming`**, **`description_hints`**, and **`rename`** combined.
- **`cli.py`** is excluded from coverage enforcement (minimal tests optional).
- Enforce locally/CI via `pytest-cov` and `coverage`/`pyproject.toml` configuration.

## Consequences

Regression safety focuses on deterministic modules; CLI behaviour is exercised indirectly.
