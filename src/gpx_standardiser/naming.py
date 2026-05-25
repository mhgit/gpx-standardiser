"""Canonical GPX basenames (ADR-0002)."""

from __future__ import annotations

from pathlib import Path

# Shell-friendly separator before rider-facing description slug.
DESCRIPTION_MARKER = "@"


class NamingError(ValueError):
    """Invalid description (or other basename rule breakage)."""


def format_stem(distance_km: int, ascent_m: int, description: str) -> str:
    desc = description.strip()
    if not desc:
        raise NamingError("Description must be non-empty.")
    return f"{distance_km}km-{ascent_m}m{DESCRIPTION_MARKER}{desc}"


def format_filename(distance_km: int, ascent_m: int, description: str) -> str:
    stem = format_stem(distance_km, ascent_m, description)
    return f"{stem}.gpx"


def allocate_unique_gpx_basename(
    dest_dir: Path,
    stem: str,
    *,
    occupied: set[str],
    overwrite_conflicts: bool,
    check_destination_files: bool = True,
) -> str | None:
    """
    Choose ``{stem}.gpx`` when free; otherwise ``{stem}-2.gpx``, ``{stem}-3.gpx``, etc.

    A name is unavailable if listed in ``occupied`` (already written or reserved this run).

    With ``check_destination_files`` true (rename), a path also blocks ``try_take``
    when a regular file of that basename already exists under ``dest_dir``, unless
    ``overwrite_conflicts``.

    With ``check_destination_files`` false (interactive ``plan`` only), collisions
    with files already on disk are ignored so previews match intra-run disambiguation
    for an empty outbound folder.

    Returns ``None`` only when ``{stem}.gpx`` fails ``try_take``, ``stem.gpx``
    remains unoccupied on that attempt, and ``check_destination_files`` is true—the
    classic “destination exists—use `--force` or pick another folder” rename skip.
    """

    primary = f"{stem}.gpx"

    def try_take(name: str) -> bool:
        if name in occupied:
            return False
        if check_destination_files:
            dest_path = dest_dir / name
            if dest_path.is_file():
                return overwrite_conflicts
        return True

    if try_take(primary):
        occupied.add(primary)
        return primary

    if primary not in occupied:
        # Exists on disk, not overwriting: caller skips this source file entirely.
        return None

    i = 2
    max_suffix = 9_999
    while i <= max_suffix:
        candidate = f"{stem}-{i}.gpx"
        if try_take(candidate):
            occupied.add(candidate)
            return candidate
        i += 1
    raise NamingError(
        f"Too many duplicate basenames for stem {stem!r}; refusing suffix beyond {max_suffix}."
    )
