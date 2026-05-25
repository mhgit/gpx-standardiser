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


def test_format_stem_happy_path() -> None:
    stem = format_stem(107, 547, "Staplehurst")
    assert stem == "107km-547m@Staplehurst"


def test_format_requires_non_empty_description() -> None:
    with raises(NamingError, match="non-empty"):
        format_stem(5, 1, "   ")


def test_format_filename_returns_gpx_suffix() -> None:
    fname = format_filename(10, 20, "Z")
    assert fname.endswith(".gpx")


def test_format_filename_allows_long_stem() -> None:
    long_desc = "X" * 80
    fname = format_filename(9, 9, long_desc)
    assert fname.endswith(".gpx")
    assert long_desc in fname


def test_allocate_unique_returns_primary_then_numbered_suffixes(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    occupied: set[str] = set()
    stem = format_stem(1, 1, "Dup")

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
        == "1km-1m@Dup.gpx"
    )

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
        == "1km-1m@Dup-2.gpx"
    )

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
        == "1km-1m@Dup-3.gpx"
    )


def test_allocate_unique_existing_primary_skips_without_force(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    stem = format_stem(7, 7, "X")
    (dest_dir / "7km-7m@X.gpx").write_text("prior", encoding="utf-8")
    occupied: set[str] = set()

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
        is None
    )


def test_allocate_unique_respects_existing_numbered_until_free_gap(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    stem = format_stem(1, 1, "Dup")
    (dest_dir / "1km-1m@Dup-2.gpx").write_text("p2", encoding="utf-8")

    occupied: set[str] = {"1km-1m@Dup.gpx"}

    got = allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=False)
    assert got == "1km-1m@Dup-3.gpx"


def test_allocate_unique_overwrites_primary_when_force(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    stem = format_stem(3, 3, "Y")
    (dest_dir / "3km-3m@Y.gpx").write_text("prior", encoding="utf-8")
    occupied: set[str] = set()

    assert (
        allocate_unique_gpx_basename(dest_dir, stem, occupied=occupied, overwrite_conflicts=True)
        == "3km-3m@Y.gpx"
    )


def test_allocate_unique_preview_ignores_on_disk_conflict(tmp_path: Path) -> None:
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    stem = format_stem(2, 2, "Both")
    (dest_dir / "2km-2m@Both.gpx").write_text("on-disk", encoding="utf-8")
    occupied: set[str] = set()

    got = allocate_unique_gpx_basename(
        dest_dir,
        stem,
        occupied=occupied,
        overwrite_conflicts=False,
        check_destination_files=False,
    )
    assert got == "2km-2m@Both.gpx"
