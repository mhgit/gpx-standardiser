# Contributing

## Local checks

Before opening a PR, run:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest     # Coverage gate enforced in pyproject.toml
```

CI runs on push and pull request to `main` (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Forks and pull requests

1. **Fork** this repository on GitHub (your own copy).
2. **Branch** off `main` with a short, descriptive branch name (`git checkout -b fix-thing-or-add-feature`).
3. **Implement** your change; keep commits and the PR focused on one topic.
4. **Push** to your fork and open a **pull request** targeting **`main`** on the upstream repo.
5. Ensure **CI passes**; revise if reviewers ask.

Hint tuning uses **`config/config.yaml`** at the repo root ([`ADR-0007`](docs/adr/0007-application-config-location.md)); if you rename packaging paths keep **`tool.hatch.build.targets.(sdist|wheel).force-include`** in **`pyproject.toml`** coherent.

Larger behaviour changes should align with **[Architecture Decision Records](docs/adr/)** (`ADR-0002`/`0003`/etc.) and include tests where they add real coverage.
