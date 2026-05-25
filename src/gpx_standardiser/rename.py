"""High-level orchestration between GPX IO, naming, and metadata updates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import gpxpy

from gpx_standardiser.description_hints import description_hint_from_original
from gpx_standardiser.gpx_stats import TrackMetrics, compute_track_metrics
from gpx_standardiser.naming import DESCRIPTION_MARKER


@dataclass
class PlanRow:
    """One input file with computed naming preview fields."""

    path: Path
    metrics: TrackMetrics
    hint: str

    def proposed_stem(self) -> str:
        return (
            f"{self.metrics.distance_km}km-{self.metrics.ascent_m}m{DESCRIPTION_MARKER}{self.hint}"
            if self.hint
            else f"{self.metrics.distance_km}km-{self.metrics.ascent_m}m{DESCRIPTION_MARKER}"
        )


def plan_row(path: Path, xml_text: str, *, config_file: Path | None = None) -> PlanRow:
    metrics = compute_track_metrics(xml_text)
    hint = description_hint_from_original(path.name, config_file=config_file)
    return PlanRow(path=path, metrics=metrics, hint=hint)


def apply_description_metadata(xml_text: str, description: str) -> str:
    """ADR-0004: metadata + track `<name>` become the description-only label."""

    root = gpxpy.parse(xml_text)
    label = description.strip()
    root.name = label
    for track in getattr(root, "tracks", []) or []:
        track.name = label

    serialized = root.to_xml()
    if isinstance(serialized, bytes):  # pragma: no cover
        return serialized.decode("utf-8")
    return serialized


def write_renamed_copy(
    source: Path,
    dest_dir: Path,
    *,
    distance_km: int,
    ascent_m: int,
    description: str,
    dest_filename: str | None = None,
) -> Path:
    """Copy GPX with updated `<name>` fields into ``dest_dir`` using the canonical filename."""

    from gpx_standardiser.naming import format_filename

    fname = dest_filename or format_filename(distance_km, ascent_m, description)
    dest = dest_dir / fname

    xml_in = source.read_text(encoding="utf-8")
    xml_out = apply_description_metadata(xml_in, description.strip())

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(xml_out, encoding="utf-8")
    return dest
