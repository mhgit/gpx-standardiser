"""CSV metrics report for ``plan --report-csv``."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path

from gpx_standardiser.gpx_stats import GpxAnalysisError, compute_track_metrics
from gpx_standardiser.ride_difficulty import (
    RankedDifficulty,
    assign_ranks,
    average_grade_percent,
    difficulty_tier,
    metres_per_km,
)
from gpx_standardiser.units import OutputUnits, convert_for_output

CSV_COLUMNS = [
    "Filename",
    "Miles",
    "Ascent Feet",
    "Kilometers",
    "Ascent Meters",
    "m_per_km",
    "Grade_pct",
    "DifficultyTier",
    "Rank",
    "Error",
]


@dataclass
class PlanReportRow:
    filename: str
    miles: int | None = None
    ascent_feet: int | None = None
    kilometers: int | None = None
    ascent_meters: int | None = None
    m_per_km: float | None = None
    grade_pct: float | None = None
    difficulty_tier: str | None = None
    rank: int | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def build_plan_report_rows(paths: list[Path]) -> list[PlanReportRow]:
    rows: list[PlanReportRow] = []
    difficulties: list[RankedDifficulty] = []

    for path in paths:
        row = PlanReportRow(filename=path.name)
        try:
            xml = path.read_text(encoding="utf-8")
            metrics = compute_track_metrics(xml)
        except GpxAnalysisError as exc:
            row.error = str(exc)
            rows.append(row)
            continue

        miles, feet = convert_for_output(
            metrics.distance_km,
            metrics.ascent_m,
            OutputUnits.IMPERIAL,
        )
        density = metres_per_km(metrics.ascent_m_exact, metrics.distance_m)
        grade = average_grade_percent(metrics.ascent_m_exact, metrics.distance_m)
        tier = difficulty_tier(density)
        difficulty = RankedDifficulty(m_per_km=density, grade_pct=grade, tier=tier)
        difficulties.append(difficulty)

        row.miles = miles
        row.ascent_feet = feet
        row.kilometers = metrics.distance_km
        row.ascent_meters = metrics.ascent_m
        row.m_per_km = density
        row.grade_pct = grade
        row.difficulty_tier = tier
        rows.append(row)

    assign_ranks(difficulties)
    diff_iter = iter(difficulties)
    for row in rows:
        if row.ok:
            row.rank = next(diff_iter).rank

    return rows


def format_plan_report_csv(rows: list[PlanReportRow]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "Filename": row.filename,
                "Miles": "" if row.miles is None else row.miles,
                "Ascent Feet": "" if row.ascent_feet is None else row.ascent_feet,
                "Kilometers": "" if row.kilometers is None else row.kilometers,
                "Ascent Meters": "" if row.ascent_meters is None else row.ascent_meters,
                "m_per_km": "" if row.m_per_km is None else f"{row.m_per_km:.1f}",
                "Grade_pct": "" if row.grade_pct is None else f"{row.grade_pct:.2f}",
                "DifficultyTier": row.difficulty_tier or "",
                "Rank": "" if row.rank is None else row.rank,
                "Error": row.error or "",
            }
        )
    return buffer.getvalue()
