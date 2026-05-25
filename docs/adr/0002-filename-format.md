---
status: Accepted
---
# ADR-0002: Filename format

## Context

Club ride files are exchanged through various hosts and dashboards over time; a filename that embeds distance, ascent, and a short textual label travels well regardless of tooling. Older UIs hid file extensions and sometimes truncated visible basenames; that historically nudged the club toward **compact** descriptions, but this project **does not** enforce a fixed character cap in code.

## Decision

- Canonical pattern: `{distance_km}km-{ascent_m}m@{description}.gpx` (distance + ascent integers from GPX; description user-confirmed).
- Separator between stats prefix and label is **`@`** so POSIX shells tolerate unquoted filenames more reliably than **`^`**.
- Older club uploads occasionally used **`…^Description`** purely for heuristic parsing; exporters now emit **`@`**.
- Stem length may grow with long descriptions; hosts and members judge what is practical.
- When a single **`rename`** run would produce multiple files with the same canonical basename (same distance/ascent/description), successive copies are named ``{stem}-2.gpx``, ``{stem}-3.gpx``, … before the extension rather than overwriting or skipping.

## Consequences

Imperial distances are omitted from filenames. Descriptions rely on club culture; very long filenames remain valid at the tooling layer.
