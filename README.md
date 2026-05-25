# GPX Standardiser

Utility to propose **canonical GPX filenames** from each track's **distance** and **ascent**. Decisions live in **[Architecture Decision Records](docs/adr/)**.

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

`@` separates the measurable prefix (`NNNkm-MMMm`) from the descriptive slug. Some filesystem UI only show limited chars from the filename; the tool does **not** cap manually keep descriptions short by convention. If **`rename`** would write two identical basenames in one run, successive files become ``stem-2.gpx``, ``stem-3.gpx``, … (`ADR-0002`).

The description slug becomes the GPX **`name`** (flattened `<metadata>/<trk>` field in `gpxpy`) so head units show something short while distance/ascent stay in geometry (`ADR-0004`).

## Commands & help shortcuts

Exactly **one** input mode per invocation:

| Mode | Argument |
|------|----------|
| Directory | `--route-files <DIR>` scans `*.gpx` alphabetically |
| Single file | `FILE.gpx` positional |

`rename` Perform disk actions; `plan` can use **`--interactive` / `-i`** for a _dry run_ without writing (`rename -h` for copy options):

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

Application YAML **`config.yaml`** drives description hints (**`ADR-0004`**). Canonical copy in Git: **`config/config.yaml`** next to **`pyproject.toml`** — keys **`join_words:`** (English joiners, club acronym tokens such as **`occ`**) and **`description_filter:`** (unit/meta noise). Matching is **case-insensitive**, **whole basename segments** only (`_`, spaces, hyphen splits). Tune direction words sparingly (**`ADR-0004`** commentary in the sample file).

**Discovery** when the CLI loads config (**`ADR-0007`**): by default it resolves **`config/config.yaml`** via checkout layout (**`pyproject.toml`** sibling), walking upward from **`cwd`**, then **`bundled_config.yaml`** in wheels. Pass **`-c`** / **`--config`** on **`plan`** or **`rename`** to use a different YAML file.

Incorrect or missing YAML causes startup failure once config is parsed.

## Trial workflow (`ADR-0005`)

1. `uv sync` if dependencies changed.
2. `uv run gpx-standardiser plan --route-files …` to sanity‑check maths + hints (`ADR-0004`), or **`plan -i`** with the same folder to walk descriptions and print a **report** for the chair (still no files written).
3. `uv run gpx-standardiser rename …`, accepting/editing prompts.
4. Sort / organise in Finder before upload to whoever hosts routes.
5. Ship an outbound-folder listing + ADR excerpt to whoever owns approvals.

### Notes & caveats

- **Elevations / ascent**: the tool sums **gain on a smoothed** elevation trace (moving average, eleven samples; see **`ADR-0003`**), avoiding the inflation you get by summing every raw `<ele>` bump on dense barometer tracks. Benchmarking against common online GPX tooling we found the approximation sufficient for the purposes of gauging route difficulty.  The script may report **above or below** our number on the same file (often tens of metres, depending on route and another systems corrections).
- **`inbound-files/` / `outbound-files/`**: intentionally gitignored; always pass folders via CLI per `ADR-0005`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks (Ruff, pytest) and the fork / pull request workflow.

