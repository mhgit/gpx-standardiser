"""Whole-route difficulty helpers (distance + smoothed ascent from GPX)."""

from __future__ import annotations

from dataclasses import dataclass

TIER_FLAT = "Flat"
TIER_ROLLING = "Rolling"
TIER_HILLY = "Hilly"
TIER_VERY_HILLY = "Very hilly"

# UK road-cycling bands (m climb per km horizontal); tunable later.
TIER_ROLLING_MIN_M_PER_KM = 5.0
TIER_HILLY_MIN_M_PER_KM = 10.0
TIER_VERY_HILLY_MIN_M_PER_KM = 15.0


def metres_per_km(ascent_m: float, distance_m: float) -> float:
    """Elevation density (m gained per km horizontal)."""

    if distance_m <= 0.0:
        return 0.0
    return ascent_m / (distance_m / 1000.0)


def average_grade_percent(ascent_m: float, distance_m: float) -> float:
    """Average gradient proxy: 100 × ascent / horizontal distance."""

    if distance_m <= 0.0:
        return 0.0
    return 100.0 * ascent_m / distance_m


def difficulty_tier(m_per_km: float) -> str:
    if m_per_km < TIER_ROLLING_MIN_M_PER_KM:
        return TIER_FLAT
    if m_per_km < TIER_HILLY_MIN_M_PER_KM:
        return TIER_ROLLING
    if m_per_km < TIER_VERY_HILLY_MIN_M_PER_KM:
        return TIER_HILLY
    return TIER_VERY_HILLY


@dataclass
class RankedDifficulty:
    m_per_km: float
    grade_pct: float
    tier: str
    rank: int | None = None


def assign_ranks(rows: list[RankedDifficulty]) -> None:
    """Set ``rank`` on each row: 1 = hardest (highest m/km); competition ranking for ties."""

    indexed = sorted(enumerate(rows), key=lambda item: item[1].m_per_km, reverse=True)
    rank = 0
    prev_density: float | None = None
    for position, (_idx, row) in enumerate(indexed, start=1):
        if prev_density is None or row.m_per_km < prev_density:
            rank = position
            prev_density = row.m_per_km
        row.rank = rank
