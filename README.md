# GPX Standardiser

Club utility to propose **canonical GPX filenames** from each track's **distance** and **ascent**. Decisions live in **[Architecture Decision Records](docs/adr/)**.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (preferred). **Python 3.12+** is required ([`pyproject.toml`](pyproject.toml)); the repo pins **3.14** in [`.python-version`](.python-version) for local `uv` and CI.
- Typical install / sync:

```bash
uv sync
```

## Naming convention (`ADR-0002`)

Basename pattern:

```text
{km}km-{ascent_m}m@{description}.gpx
```

`@` separates the measurable prefix (`NNNkm-MMMm`) from the descriptive slug—a shell‑friendlier convention than experimenting with punctuation like `^`. Some club hosts show only part of long names in their UI; the tool does **not** cap length—you can still keep descriptions short by convention. If **`rename`** would write two identical basenames in one run, successive files become ``stem-2.gpx``, ``stem-3.gpx``, … (`ADR-0002`).

The description slug becomes the GPX **`name`** (flattened `<metadata>/<trk>` field in `gpxpy`) so head units show something short while distance/ascent stay in geometry (`ADR-0004`).

## Commands & help shortcuts

Exactly **one** input mode per invocation:

| Mode | Argument |
|------|----------|
| Directory | `--route-files <DIR>` scans `*.gpx` alphabetically |
| Single file | `FILE.gpx` positional |

`rename` adds disk-related controls; `plan` can use **`--interactive` / `-i`** for the same prompts without writing (`rename -h` for copy options):

| Scope | Flag | Purpose |
|------|------|---------|
| `plan` | `--interactive`, `-i` | Prompt for each description like `rename`, then print one report at the end; **no writes** |
| `rename` | `--output-folder`, `-o` | Destination folder (defaults to `.`) |
| `rename` | `--desc`, `-d` | Fixed description (needs exactly **one** input GPX) |
| `rename` | `--force`, `-f` | Overwrite a destination basename collision |
| `rename` | `--non-interactive` | Skips prompts; forbid `--route-files` batches in **v1** |

`plan -i` shows the same ``stem-2.gpx``, ``stem-3.gpx`` numbering for duplicates **within that preview**, but does not scan any output directory for clashes. **`rename`** into a chosen folder respects existing files (skip unless **`--force`**, per-file).

```bash
uv run gpx-standardiser plan -h
uv run gpx-standardiser rename -h

# Typical flows (`plan` never writes files)
uv run gpx-standardiser plan --route-files ./inbound-files/
# Interactive:
uv run gpx-standardiser plan -i --route-files ./inbound-files/

# Renaming files
uv run gpx-standardiser rename --route-files ./inbound-files/ --output-folder ./outbound-files/

uv run gpx-standardiser rename ./ride.gpx -o ./outbound-files/ -d 'Tea-Room-Tour' -f
```

## Configuration

Join words for hint cleanup live in **`src/gpx_standardiser/config/join_words.yaml`** (YAML list of quoted strings; quote words like `on` so PyYAML does not treat them as booleans). Words are matched **case-insensitively** as **whole** basename segments (`_`, spaces, `-` separators); they are dropped **wherever they appear**. In the rare case a real place reads like a join word, type it again at the prompt. The file must ship with the install or the CLI errors on startup.

## Trial workflow (`ADR-0005`)

1. `uv sync` if dependencies changed.
2. `uv run gpx-standardiser plan --route-files …` to sanity‑check maths + hints (`ADR-0004`), or **`plan -i`** with the same folder to walk descriptions and print a **report** for the chair (still no files written).
3. `uv run gpx-standardiser rename …`, accepting/editing prompts.
4. Sort / organise in Finder before upload to whoever hosts routes.
5. Ship an outbound-folder listing + ADR excerpt to whoever owns approvals.

### Notes & caveats

- **Elevations / ascent**: the tool sums **gain on a smoothed** elevation trace (moving average, eleven samples; see **`ADR-0003`**), avoiding the inflation you get by summing every raw `<ele>` bump on dense barometer tracks. Garmin Connect remains a **benchmark**, not ground truth—it may report **above or below** our number on the same file (often tens of metres, depending on route and Garmin’s corrections). Prefer our value for **consistent club filenames**, not handset debates.
- **Legacy filenames**: some downloads still embed `…^PlaceName`; quote them until you rerun `rename`.
- **`inbound-files/` / `outbound-files/`**: intentionally gitignored; always pass folders via CLI per `ADR-0005`.

## Development

**Repository slug:** The PyPI package and CLI stay `gpx-standardiser`. If you want a different **GitHub repo name**, rename only the checkout folder before `gh repo create` (no code changes needed).

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest     # Coverage gate enforced in pyproject.toml
```

CI runs on push and pull request to `main` (see `.github/workflows/ci.yml`).
