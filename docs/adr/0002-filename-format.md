---
status: Accepted
---
# ADR-0002: Filename format

## Context

Club ride files are exchanged through various hosts and dashboards over time; a filename that embeds distance, ascent, and a short textual label travels well regardless of tooling. Older UIs hid file extensions and sometimes truncated visible basenames; that historically nudged the club toward **compact** descriptions, but this project **does not** enforce a fixed character cap in code.

## Decision

- Canonical pattern: `{distance}{dist_unit}-{ascent}{ascent_unit}@{description}.gpx` (distance + ascent integers derived from GPX geometry; description user-confirmed).
- Units are selected by **`--units`**, which defaults to **imperial**: `053mls-1234ft@Tea-Room-Tour.gpx`. `--units metric` emits `085km-376m@Tea-Room-Tour.gpx`. All internal maths stays metric (`ADR-0003`); conversion happens only at the filename / prompt boundary (`units.py`).
- Distance is zero-padded to at least three digits so hosts that sort lexicographically list rides in distance order; ascent is unpadded and grows naturally past the field width.
- Separator between stats prefix and label is **`@`** so POSIX shells tolerate unquoted filenames more reliably than **`^`**.
- Older club uploads occasionally used **`…^Description`** purely for heuristic parsing; exporters now emit **`@`**.
- Stem length may grow with long descriptions; hosts and members judge what is practical.
- When a single **`rename`** run would produce multiple files with the same canonical basename (same distance/ascent/description), successive copies are named ``{stem}-2.gpx``, ``{stem}-3.gpx``, … before the extension rather than overwriting or skipping.

## Consequences

A basename records only the unit system it was written with, so a folder built from mixed `--units` runs mixes `mls`/`ft` and `km`/`m` stems; pick one per batch. Imperial values are converted from the already-rounded metric integers rather than from raw geometry, so they can sit a unit away from a direct conversion, and the two forms are not exactly interconvertible. Descriptions rely on club culture; very long filenames remain valid at the tooling layer.
