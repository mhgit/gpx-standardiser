---
status: Accepted
---
# ADR-0007: Application `config.yaml` location and discovery

## Context

Editors look for knobs in an obvious repo-level place (`config/`), while the packaged CLI must keep working without a sibling checkout (`pip` / `uv` wheel installs).

## Decision

1. **Authoritative YAML in Git** lives at **`config/config.yaml`** at the repository root (next to **`pyproject.toml`**). Keys **`join_words`** and **`description_filter`** keep the meanings from **`ADR-0004`** — only the filesystem path moves out of **`src/`**.
2. **Discovery order** (`gpx_standardiser.config.load_config_yaml_raw` when **`config_file` is omitted):
   - **Checkout-root**: nearest ancestor directory of the installed **`gpx_standardiser.config`** package that contains both **`pyproject.toml`** and **`config/config.yaml`**. Stable for editable installs regardless of **`cwd`** within the checkout.
   - **Working-directory walk**: walk **`Path.cwd()`** and its parents looking for **`config/config.yaml`** (covers clones when something changes **`cwd`** before import).
   - **Wheel fallback**: Hatch **`wheel.force-include`** maps **`config/config.yaml`** into the wheel next to **`gpx_standardiser`** as **`bundled_config.yaml`**. **`sdist.force-include`** mirrors the same repo path inside the source distribution so builds that produce a wheel **from** an sdist still find the file before remapping (Hatchling ≥ 1.19 behaviour).
3. **Explicit path**: pass **`-c` / `--config PATH`** on **`plan`** and **`rename`**; library loaders accept an optional **`config_file`** for tests and programmatic use.
4. **Caching**: Parsed config is memoised once per process per resolved path (`load_app_config`); restarting the CLI reloads YAML.

## Consequences

- Club members editing join words open **`config/config.yaml`** without diving into **`src/`**.
- **Packaging**: wheel and sdist rely on paired Hatch **`force-include`** entries in **`pyproject.toml`**; renaming paths breaks builds until it is updated.
- **Isolation tests** must monkeypatch resolver helpers (`_path_from_*`, `_bundled_yaml_text_or_none`) because **`Path(__file__)`** discovery still reaches the checkout under test even when **`chdir`** is elsewhere.
