"""Distance and ascent from GPX track geometry."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import gpxpy
import gpxpy.gpx

ELEVATION_DELTA_THRESHOLD_M = 0.0

# Smooth dense device <ele> (barometer / fused GPS jitter) before summing climb;
# nearer Garmin Connect ascent than raw Δele positives (ADR-0003).
ASCENT_MOVING_AVG_WINDOW = 11


@dataclass
class TrackMetrics:
    """Computed stats plus non-fatal notes for the CLI."""

    distance_km: int
    ascent_m: int
    distance_m: float = 0.0
    ascent_m_exact: float = 0.0
    warnings: list[str] = field(default_factory=list)


class GpxAnalysisError(RuntimeError):
    """Raised when a file cannot satisfy ADR metrics rules."""


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points (metres)."""
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(1e-12, 1.0 - a)))
    return 6_371_000.0 * c


def smooth_elevation_moving_average(
    values: list[float],
    window: int = ASCENT_MOVING_AVG_WINDOW,
) -> list[float]:
    """Centred moving-average; ``window`` is coerced odd. Tracks shorter than the window unchanged."""

    n = len(values)
    if n < 2:
        return list(values)

    win = window if window % 2 == 1 else window + 1
    if win < 3:
        return list(values)
    if n < win:
        return list(values)

    half = win // 2
    padded = [values[0]] * half + values + [values[-1]] * half

    smoothed: list[float] = []
    for i in range(n):
        span = padded[i : i + win]
        smoothed.append(sum(span) / float(win))
    return smoothed


def horizontal_distance_metres(points: list[gpxpy.gpx.GPXTrackPoint]) -> float:
    total = 0.0
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        total += _haversine_m(a.latitude, a.longitude, b.latitude, b.longitude)
    return total


def total_ascent_metres(
    elevs: list[float], threshold: float = ELEVATION_DELTA_THRESHOLD_M
) -> float:
    if len(elevs) < 2:
        return 0.0
    gain = 0.0
    prev = elevs[0]
    for cur in elevs[1:]:
        delta = cur - prev
        prev = cur
        if delta > threshold:
            gain += delta
    return gain


def track_points_flat(track: gpxpy.gpx.GPXTrack) -> list[gpxpy.gpx.GPXTrackPoint]:
    pts: list[gpxpy.gpx.GPXTrackPoint] = []
    for segment in track.segments:
        pts.extend(segment.points)
    return pts


def compute_track_metrics(xml_text: str) -> TrackMetrics:
    """ADR-0003: first track stats; warn on extra tracks; require elevation."""

    warnings: list[str] = []

    root = gpxpy.parse(xml_text)

    if root.routes:
        warnings.append(
            "Route (<rte>) elements present; track metrics use <trk> only; routes are ignored.",
        )

    tracks = getattr(root, "tracks", []) or []

    if not tracks:
        if root.routes:
            raise GpxAnalysisError(
                "Only route (<rte>) data found — route-only GPX is not supported in v1."
            )
        raise GpxAnalysisError("No <trk> elements found in GPX.")

    if len(tracks) > 1:
        warnings.append(
            f"{len(tracks)} tracks (<trk>) found; metrics use the first track only.",
        )

    track = tracks[0]
    points = track_points_flat(track)

    if len(points) < 2:
        raise GpxAnalysisError("Need at least two track points for distance.")

    dist_m = horizontal_distance_metres(points)
    distance_km = int(round(dist_m / 1000.0))

    elevations: list[float] = []
    for p in points:
        if p.elevation is None:
            continue
        elevations.append(float(p.elevation))

    if len(elevations) < 2:
        raise GpxAnalysisError(
            "Insufficient <ele> data on track points — cannot compute climb (ADR v1 requires elevation).",
        )

    for_smoothing = smooth_elevation_moving_average(elevations)
    ascent_exact = total_ascent_metres(for_smoothing)
    ascent = int(round(ascent_exact))

    return TrackMetrics(
        distance_km=distance_km,
        ascent_m=ascent,
        distance_m=dist_m,
        ascent_m_exact=ascent_exact,
        warnings=list(warnings),
    )
