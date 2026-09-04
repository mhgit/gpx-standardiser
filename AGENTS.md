# Repository Guidelines

## Project Overview
`gpx-standardiser` is a Python-based CLI tool designed to standardize GPX filenames and metadata for a cycling club. It analyzes GPX files to calculate key metrics (distance and ascent) and renames them according to a canonical format for better organization and sorting.

## Architecture & Data Flow
The project follows a **functional core, thin shell** architecture:
- **Functional Core**: Deterministic modules responsible for GPX parsing, metric calculation (Haversine distance, smoothed ascent), and filename generation.
- **CLI Shell**: A Typer-based interface that handles file I/O, configuration loading, and user interaction.

**Data Flow**:
`Source GPX` $\rightarrow$ `Metric Analysis` $\rightarrow$ `Naming Logic` $\rightarrow$ `Plan/Preview` $\rightarrow$ `Copy to Output Folder (Renamed)`.

**Key Pattern**: **Plan then Execute**.
- `plan`: Dry-run analysis producing a preview/report.
- `rename`: Performs the actual copying of files.
- **Safety**: Source files are **never** modified in place (Copy-only policy).

## Key Directories
- `src/gpx_standardiser/`: Main source code.
- `tests/`: Test suite, including `tests/fixtures/` for GPX XML generation.
- `docs/`: Design documents and Architecture Decision Records (ADRs).
- `config/`: Default application configuration (`config.yaml`).

## Development Commands
All commands should be executed via `uv`.

| Action | Command |
| :--- | :--- |
| Setup Environment | `uv sync` |
| Run CLI | `uv run gpx-standardiser [args]` |
| Run Tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |

## Code Conventions & Common Patterns
- **Naming**: Follows standard Python (PEP 8) conventions.
- **Error Handling**: Custom exception hierarchy (e.g., `NamingError`, `GpxAnalysisError`) for domain-specific failures.
- **Metric Calculation**: 
    - **Distance**: Haversine formula on the first track.
    - **Ascent**: Moving-average smoothing (window=11) to filter barometer noise.
- **Filename Format**: `{distance}{unit}-{ascent}{unit}@{description}.gpx` (zero-padded for lexicographical sorting).
- **Metadata**: Internal GPX `<name>` tags are updated to be description-only.

## Important Files
- `pyproject.toml`: Project manifest, dependencies, and tool configurations.
- `src/gpx_standardiser/cli.py`: Application entry point.
- `config/config.yaml`: Defines basename cleaning (`join_words`) and metadata noise filtering (`description_filter`).
- `docs/design.md`: High-level architecture and flow diagrams.
- `docs/adr/*.md`: Decision records governing technical choices.

## Runtime/Tooling Preferences
- **Runtime**: Python $\ge 3.12$.
- **Package Manager**: `uv` (Mandatory).
- **Build System**: `hatchling`.
- **Linting/Formatting**: `ruff` (Line length: 100).
- **CLI Framework**: `typer`.

## Testing & QA
- **Framework**: `pytest`.
- **Coverage**: `pytest-cov` with a **REQUIRED** minimum of **80%**.
- **Execution**: `uv run pytest` (automatically handles coverage via `pyproject.toml` options).
- **Pattern**: Functional tests for core logic; use `tests/fixtures/gpx_build.py` to generate deterministic GPX blobs for testing.
- **Floating Point**: Use `pytest.approx` for metric comparisons.
