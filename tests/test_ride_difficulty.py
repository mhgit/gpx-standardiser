"""Ride difficulty helpers."""

from __future__ import annotations

from gpx_standardiser.ride_difficulty import (
    TIER_FLAT,
    TIER_HILLY,
    TIER_ROLLING,
    TIER_VERY_HILLY,
    RankedDifficulty,
    assign_ranks,
    average_grade_percent,
    difficulty_tier,
    metres_per_km,
)


def test_metres_per_km() -> None:
    assert metres_per_km(500.0, 50_000.0) == 10.0


def test_average_grade_percent() -> None:
    assert average_grade_percent(500.0, 50_000.0) == 1.0


def test_grade_and_m_per_km_consistent() -> None:
    density = metres_per_km(772.0, 124_000.0)
    grade = average_grade_percent(772.0, 124_000.0)
    assert grade == density / 10.0


def test_difficulty_tiers() -> None:
    assert difficulty_tier(4.9) == TIER_FLAT
    assert difficulty_tier(5.0) == TIER_ROLLING
    assert difficulty_tier(9.9) == TIER_ROLLING
    assert difficulty_tier(10.0) == TIER_HILLY
    assert difficulty_tier(14.9) == TIER_HILLY
    assert difficulty_tier(15.0) == TIER_VERY_HILLY


def test_assign_ranks_hardest_is_one() -> None:
    rows = [
        RankedDifficulty(m_per_km=6.0, grade_pct=0.6, tier=TIER_ROLLING),
        RankedDifficulty(m_per_km=12.0, grade_pct=1.2, tier=TIER_HILLY),
        RankedDifficulty(m_per_km=8.0, grade_pct=0.8, tier=TIER_ROLLING),
    ]
    assign_ranks(rows)
    assert rows[1].rank == 1
    assert rows[2].rank == 2
    assert rows[0].rank == 3


def test_assign_ranks_ties_share_rank() -> None:
    rows = [
        RankedDifficulty(m_per_km=10.0, grade_pct=1.0, tier=TIER_HILLY),
        RankedDifficulty(m_per_km=10.0, grade_pct=1.0, tier=TIER_HILLY),
        RankedDifficulty(m_per_km=5.0, grade_pct=0.5, tier=TIER_ROLLING),
    ]
    assign_ranks(rows)
    assert rows[0].rank == 1
    assert rows[1].rank == 1
    assert rows[2].rank == 3
