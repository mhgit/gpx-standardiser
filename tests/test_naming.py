"""Filename stem helpers."""

from __future__ import annotations

from pathlib import Path

from pytest import raises

from gpx_standardiser.naming import (
    NamingError,
    allocate_unique_gpx_basename,
    format_filename,
    format_stem,
)
from gpx_standardiser.units import OutputUnits


def test_format_stem_happy_path() -> None:
    stem = format_stem(107, 547, "Staplehurst", units=OutputUnits.METRIC)
    assert stem == "107km-547m@Staplehurst"


def test_format_stem_zero_pads_short_distances() -> None:
    stem = format_stem(10, 104, "tonbridge-east-west-path", units=OutputUnits.METRIC)
    assert stem == "010km-104m@tonbridge-east-west-path"


def test_format_stem_allows_long_distances() -> None:
    stem = format_stem(1000, 100, "Audax", units=OutputUnits.METRIC)
    assert stem == "1000km-100m@Audax"


def test_format_requires_non_empty_description() -> None:
    with raises(NamingError, match="non-empty"):
        format_stem(5, 1, "   ")


def test_format_filename_returns_gpx_suffix() -> None:
    fname = format_filename(10, 20, "Z", units=OutputUnits.METRIC)
    assert fname.endswith(".gpx")


def test_format_filename_allows_long_stem() -> None:
    long_desc = "X" * 80
    fname = format_filename(9, 9, long_desc, units=OutputUnits.METRIC)
    assert fname.endswith(".gpx")
    assert long_desc in fname


def test_allocate_unique_returns_primary_then_numbered_suffixes(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    occupied: set[str] = set()
    stem = format_stem(1, 1, "Dup", units=OutputUnits.METRIC)

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
        == "001km-1m@Dup.gpx"
    )

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
        == "001km-1m@Dup-2.gpx"
    )

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
        == "001km-1m@Dup-3.gpx"
    )


def test_allocate_unique_existing_primary_skips_without_force(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    stem = format_stem(7, 7, "X", units=OutputUnits.METRIC)
    (dest_dir / "007km-7m@X.gpx").write_text("prior", encoding="utf-8")
    occupied: set[str] = set()

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
        is None
    )


def test_allocate_unique_respects_existing_numbered_until_free_gap(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    stem = format_stem(1, 1, "Dup", units=OutputUnits.METRIC)
    (dest_dir / "001km-1m@Dup-2.gpx").write_text("p2", encoding="utf-8")

    occupied: set[str] = {"001km-1m@Dup.gpx"}

    got = allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
    assert got == "001km-1m@Dup-3.gpx"


def test_allocate_unique_overwrites_primary_when_force(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    stem = format_stem(3, 3, "Y", units=OutputUnits.METRIC)
    (dest_dir / "003km-3m@Y.gpx").write_text("prior", encoding="utf-8")
    occupied: set[str] = set()

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=True)
        == "003km-3m@Y.gpx"
    )


def test_allocate_unique_preview_ignores_on_disk_conflict(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    stem = format_stem(2, 2, "Both", units=OutputUnits.METRIC)
    (dest_dir / "002km-2m@Both.gpx").write_text("on-disk", encoding="utf-8")
    occupied: set[str] = set()

    got = allocate_unique_gpx_basename(
        dest_dir,
        stem,
        occupied=occupied,
        overwrite_conflicts=False,
        check_destination_files=False,
    )
    assert got == "002km-2m@Both.gpx"
