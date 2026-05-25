---
status: Accepted
---
# ADR-0004: Description hints and `<name>` metadata

## Context

Interactive renaming should be fast; filenames often encode place names inconsistently.

## Decision

1. **Description** remains user-confirmed. The CLI may pre-fill a **hint** derived from the original basename: tokenise; strip numbers/units/ability tiers; prefer trailing text after the final **`@`** (then the legacy **`^`** suffix); then drop tokens whose lowercase form appears in **`join_words`**, and treat tokens listed under **`description_filter`**, both read from **`config.yaml`** (`ADR-0007`; canonical repository path **`config/config.yaml`**), as units/ride-meta noise removed the same way (whole-token matches only, case-insensitive). **Caveat:** a join word that is a real place token (rare) could be removed. If config cannot be resolved or YAML is invalid, the tool fails at startup.
2. **GPX metadata**: Set `<metadata><name>` and each `<trk><name>` to the **description only** (not the full new filename) so head units show a short label; distance and climb remain available in the route data (`gpxpy` merges metadata fields onto `GPX.name` internally).

## Consequences

Hints can be wrong; users must review. Stored GPX names are description-only (`ADR-0004` Decision 2), not the full metric-prefixed filename.
