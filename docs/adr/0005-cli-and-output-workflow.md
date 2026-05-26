---
status: Accepted
---
# ADR-0005: CLI structure and output workflow

## Context

Input paths must not be hardcoded; local folders `inbound-files/` and `outbound-files/` are gitignored and passed explicitly.

## Decision

- Commands: `plan` (no writes; optional `--interactive` / `-i` to mirror `rename` prompts and emit a final report; optional `--report-csv` for a metrics CSV on stdout) and `rename` (copy + optional metadata update).
- Input: **either** `--route-files <dir>` (all `*.gpx`, sorted by name) **or** a single positional `<file.gpx>` — mutually exclusive.
- Output: `--output-folder` with default `.` (`rename` only). **Never** modify source GPX files; always copy renamed output.
- Duplicate canonical basenames in one **`rename`** run are written as ``{stem}-2.gpx``, ``{stem}-3.gpx``, … (`ADR-0002`).

## Plan CSV report (`--report-csv`)

- Non-interactive **`plan`** only; prints **CSV to stdout** (pipe to a file). Incompatible with `-i`.
- Columns: filename, miles, ascent feet, kilometres, ascent metres, `m_per_km`, `Grade_pct`, `DifficultyTier`, `Rank` (1 = hardest in batch), plus `Error` when a file fails.
- Difficulty uses whole-route **elevation density** (smoothed ascent / horizontal distance) and fixed UK-oriented tier bands — not FIETS (that index targets individual cols, not full club routes).

## Finder upload ordering

Manual ordering in Finder (e.g. by filename) can approximate distance sequencing where the host sorts by upload time. Tool-generated upload-order manifests were **considered** and **rejected** for v1.

## Consequences

Bulk operations require disciplined upload order outside the CLI.
