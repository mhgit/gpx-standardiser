---
status: Accepted
---
# ADR-0003: GPX distance and ascent

## Context

Filenames historically embed inconsistent distances and climb figures. Source of truth is the GPX track geometry.

## Decision

- **Distance**: Sum horizontal (haversine) segment lengths along **the first `<trk>` only**, concatenating `<trkseg>` segments in order; round **nearest integer kilometres**.
- **Ascent**: Apply a centred **moving-average smooth** over consecutive `<ele>` samples (odd window; default **11** points — typical horizontal spacing on the ground scales with sampling rate). On the smoothed series, sum only positive elevation deltas; round **nearest integer metre**. Tracks with fewer samples than the window skip smoothing but still sum raw positive deltas (`ADR` implementation mirrors this rule). Matches typical Garmin Connect ascent on many exports better than a raw \(\Delta\text{elev}\) sum (which balloons on dense barometer noise).
- Multiple `<trk>` elements: compute stats from the **first** track; emit a warning for additional tracks (not supported for stats aggregation in v1).
- No `<ele>` on any sampled point logic: treated as unsupported for ascent — fail with readable error (see implementation).
- Route-only GPX (`<rtept>`): not supported in v1.

## Consequences

Garmin Connect, Strava, and similar UIs apply **their own smoothing, barometer logic, DEM correction, or rounding**. Our figure is reproducible from the file alone and avoids the gross **inflate-every-micro-bump** failure mode of summing raw `<ele>` positives. Compared with Garmin Connect on the **same GPX**, totals often land within **tens of metres**—either direction (e.g. one hilly Surrey route may read higher than Garmin while another reads lower).

Use ascent in filenames as **practical guidance** for leaders and filenames, not a guarantee of handheld agreement with any one vendor dashboard.
