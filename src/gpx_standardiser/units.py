"""Output unit conversion (metric GPX maths → imperial or metric filenames)."""

from __future__ import annotations

from enum import Enum

KM_PER_MILE = 1.609344
M_PER_FOOT = 0.3048


class OutputUnits(str, Enum):
    """Filename and CLI display units."""

    IMPERIAL = "imperial"
    METRIC = "metric"


def convert_for_output(
    distance_km: int,
    ascent_m: int,
    units: OutputUnits,
) -> tuple[int, int]:
    """Convert rounded metric stats for basename / prompt display."""

    if units is OutputUnits.METRIC:
        return distance_km, ascent_m
    distance_mls = int(round(distance_km / KM_PER_MILE))
    ascent_ft = int(round(ascent_m / M_PER_FOOT))
    return distance_mls, ascent_ft


def distance_unit_suffix(units: OutputUnits) -> str:
    return "km" if units is OutputUnits.METRIC else "mls"


def ascent_unit_suffix(units: OutputUnits) -> str:
    return "m" if units is OutputUnits.METRIC else "ft"


def metrics_headline(distance_km: int, ascent_m: int, units: OutputUnits) -> str:
    """Human-readable distance/ascent snippet for interactive prompts."""

    dist, ascent = convert_for_output(distance_km, ascent_m, units)
    d_suffix = distance_unit_suffix(units)
    a_suffix = ascent_unit_suffix(units)
    return f"{dist} {d_suffix} - {ascent} {a_suffix} climb"
