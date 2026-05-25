"""Typer CLI: plan (dry-run) and rename (copy + metadata update)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from gpx_standardiser.description_hints import description_hint_from_original
from gpx_standardiser.gpx_stats import GpxAnalysisError, compute_track_metrics
from gpx_standardiser.naming import (
    NamingError,
    allocate_unique_gpx_basename,
    format_stem,
)
from gpx_standardiser.rename import plan_row as build_plan_row
from gpx_standardiser.rename import write_renamed_copy
from gpx_standardiser.units import OutputUnits, metrics_headline

ConfigPathOption = Annotated[
    Path | None,
    typer.Option(
        "--config",
        "-c",
        metavar="YAML",
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help=(
            "Application config (join_words + description_filter). "
            'Omit to resolve "config/config.yaml" next to pyproject.toml, '
            "then upward from cwd, then the bundled copy in installs."
        ),
    ),
]


UnitsOption = Annotated[
    OutputUnits,
    typer.Option(
        "--units",
        case_sensitive=False,
        help="Output units for distance and ascent in filenames and prompts (default: imperial).",
    ),
]


_APP_HELP = """Standardise GPX basenames to "<dist>-<ascent>@<desc>.gpx" (see docs/adr/)."""

_APP_EPILOG = """\
Use `plan --interactive` (-i) to walk the same prompts as `rename`, then print a report (nothing written).
For real copies use `rename` with --output-folder / -o, --desc/-d, --force, --non-interactive.
Optional: -c / --config for application YAML (join_words, description_filter); omit for default discovery.

Examples:
  gpx-standardiser plan --route-files ./inbound-files/
  gpx-standardiser plan -i --route-files ./inbound-files/
  gpx-standardiser rename --route-files ./inbound-files/ --output-folder ./outbound-files/

Use "SUBCOMMAND -h" for full options."""

app = typer.Typer(
    help=_APP_HELP,
    epilog=_APP_EPILOG,
    no_args_is_help=True,
    add_completion=False,
    suggest_commands=False,
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def resolve_input_paths(route_files: str | None, gpx_path: Path | None) -> list[Path]:
    if (route_files is None) == (gpx_path is None):
        raise typer.BadParameter(
            "Specify exactly one of: --route-files <DIR>  OR a single ROUTE.gpx path.",
        )
    if route_files is not None:
        rd = Path(route_files).expanduser()
        if not rd.is_dir():
            raise typer.BadParameter(f"--route-files is not a directory: {rd}")
        found = sorted(p for p in rd.iterdir() if p.suffix.lower() == ".gpx")
        if not found:
            raise typer.BadParameter(f"No *.gpx files under {rd}")
        return found

    assert gpx_path is not None
    gf = Path(gpx_path).expanduser()
    if gf.suffix.lower() != ".gpx":
        raise typer.BadParameter(f"Not a .gpx file: {gf}")
    if not gf.is_file():
        raise typer.BadParameter(f"GPX file not found: {gf}")
    return [gf]


_PLAN_EPILOG = (
    "Writes nothing. Try --interactive / -i to confirm descriptions like `rename`, then print a report. "
    'Destination folder is `rename` only (-o / --output-folder). Say "rename -h".'
)


@app.command(epilog=_PLAN_EPILOG)
def plan(
    gpx_file: Path | None = typer.Argument(
        None,
        metavar="FILE.gpx",
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help=(
            "One GPX file to analyse (mutually exclusive with --route-files; "
            "quote paths with spaces or tricky shell punctuation)."
        ),
    ),
    route_files: str | None = typer.Option(
        None,
        "--route-files",
        help=(
            "Directory scanned for *.gpx (bulk, sorted by name); mutually exclusive with FILE.gpx."
        ),
        metavar="DIR",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help=(
            "Ask for each description like `rename`, then print a single report at the end; "
            "still writes no files."
        ),
    ),
    config_file: ConfigPathOption = None,
    units: UnitsOption = OutputUnits.IMPERIAL,
) -> None:
    """Print distance, ascent, and filename hints — no writes."""

    paths = resolve_input_paths(route_files, gpx_file)

    if interactive:
        typer.echo(
            "Interactive plan: answer each prompt; a report prints at the end (nothing is written)."
        )
        typer.echo("")

        report_lines: list[str] = []
        n_ok = 0
        n_skip = 0
        n_err = 0
        basename_occupied: set[str] = set()

        for path in paths:
            try:
                xml = path.read_text(encoding="utf-8")
                metrics = compute_track_metrics(xml)
            except GpxAnalysisError as exc:
                typer.echo(f"{path.name}: ERROR: {exc}")
                report_lines.append(f"{path.name} -> ERROR: {exc}")
                n_err += 1
                continue

            for w in metrics.warnings:
                typer.echo(f"  warning: {w}")

            hint = description_hint_from_original(path.name, config_file=config_file)
            picked = _prompt_until_valid_stem(
                metrics.distance_km,
                metrics.ascent_m,
                path,
                hint,
                units=units,
            )
            if picked is None:
                typer.echo("[skip] blank choice - untouched.")
                report_lines.append(f"{path.name} -> SKIPPED (blank)")
                n_skip += 1
                continue

            stem = format_stem(metrics.distance_km, metrics.ascent_m, picked, units=units)
            outfile = allocate_unique_gpx_basename(
                Path("."),
                stem,
                occupied=basename_occupied,
                overwrite_conflicts=False,
                check_destination_files=False,
            )

            assert outfile is not None  # batch-only collisions always resolve (-2.gpx …)

            suffix_note = ""
            if outfile != f"{stem}.gpx":
                suffix_note = " (suffix added - duplicate basename in this preview)"
            report_lines.append(f"{path.name} -> {outfile}{suffix_note}")
            n_ok += 1

        typer.echo("")
        typer.echo("--- Plan report (nothing written) ---")
        for line in report_lines:
            typer.echo(line)
        typer.echo("")
        typer.echo(f"Would rename: {n_ok}; skipped: {n_skip}; errors: {n_err}.")
        return

    typer.echo("original basename -> projected stem (+ warnings)")
    typer.echo("-" * 70)
    for path in paths:
        try:
            xml = path.read_text(encoding="utf-8")
            row = build_plan_row(path, xml, config_file=config_file, units=units)
        except GpxAnalysisError as exc:
            typer.echo(f"{path.name}: ERROR: {exc}")
            continue
        for w in row.metrics.warnings:
            typer.echo(f"  warning: {w}")
        typer.echo(f"{path.name}\n  -> {row.proposed_stem()}")


def _friendly_dest_message(dest_abs: Path) -> str:
    try:
        return str(dest_abs.resolve().relative_to(Path.cwd()))
    except ValueError:
        return str(dest_abs.resolve())


def _prompt_until_valid_stem(
    distance_km: int,
    ascent_m: int,
    path: Path,
    hint: str,
    *,
    units: OutputUnits,
) -> str | None:
    """Interactive loop returning a valid description string, or ``None`` to skip file."""

    headline = f'Description for "{path.name}" [{metrics_headline(distance_km, ascent_m, units)}]'

    hint_default = hint or ""
    while True:
        if hint_default:
            raw = typer.prompt(headline, default=hint_default, show_default=True)
        else:
            raw = typer.prompt(
                headline + "\n(blank skips this file)",
                default="",
                show_default=False,
            )
        trimmed = (raw or "").strip()
        if not trimmed:
            return None

        try:
            format_stem(distance_km, ascent_m, trimmed, units=units)
        except NamingError as exc:
            typer.echo(f"Try again: {exc}")
            hint_default = trimmed
            continue
        return trimmed


@app.command(
    epilog=(
        "Same input modes as plan. Adds --output-folder/-o, "
        "--desc/-d, --force/-f, --non-interactive."
    ),
)
def rename(
    gpx_file: Path | None = typer.Argument(
        None,
        metavar="FILE.gpx",
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help=(
            "One GPX to copy with a canonical filename (mutually exclusive with "
            "--route-files; quote paths with spaces or unusual shell punctuation)."
        ),
    ),
    route_files: str | None = typer.Option(
        None,
        "--route-files",
        metavar="DIR",
        help=("Directory of *.gpx files to rename in one run (bulk, sorted alphabetically)."),
    ),
    output_folder: Path = typer.Option(
        Path("."),
        "--output-folder",
        "-o",
        metavar="PATH",
        resolve_path=True,
        help=(
            "Destination directory for rewritten files (folders are created as needed); "
            "sources are never altered."
        ),
    ),
    desc: str | None = typer.Option(
        None,
        "--desc",
        "-d",
        metavar="TEXT",
        help="Fixed description label (allowed only alongside a lone FILE.gpx; skips prompting).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite a destination *.gpx that already shares the canonical name.",
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help=(
            "Disable prompts - must pair with `--desc` for a lone FILE.gpx; incompatible with "
            "`--route-files` batches (v1)."
        ),
    ),
    config_file: ConfigPathOption = None,
    units: UnitsOption = OutputUnits.IMPERIAL,
) -> None:
    """Copy GPX files using the ADR basename pattern and refreshed `<name>` metadata."""
    paths = resolve_input_paths(route_files, gpx_file)
    dest_root = Path(output_folder).expanduser()

    if desc is not None and len(paths) != 1:
        raise typer.BadParameter("`--desc` can only accompany a single FILE.gpx.")

    if non_interactive and len(paths) > 1:
        raise typer.BadParameter(
            "`--non-interactive` cannot be combined with `--route-files` batches in v1.",
        )

    copied = 0
    skipped = 0
    basename_occupied: set[str] = set()

    for path in paths:
        xml_text = path.read_text(encoding="utf-8")

        try:
            metrics = compute_track_metrics(xml_text)
        except GpxAnalysisError as exc:
            typer.echo(f"[skip] {path.name}: {exc}")
            skipped += 1
            continue

        for w in metrics.warnings:
            typer.echo(f"  warning: {w}")

        hint = description_hint_from_original(path.name, config_file=config_file)
        chosen_desc: str | None

        if desc is not None:
            try:
                format_stem(metrics.distance_km, metrics.ascent_m, desc.strip(), units=units)
            except NamingError as exc:
                typer.echo(f"[error] `--desc`: {exc}")
                raise typer.Exit(code=1) from exc
            chosen_desc = desc.strip()
        elif non_interactive:
            typer.echo(f"[skip] {path.name}: `--desc` required with `--non-interactive`.")
            skipped += 1
            continue
        else:
            picked = _prompt_until_valid_stem(
                metrics.distance_km,
                metrics.ascent_m,
                path,
                hint,
                units=units,
            )
            if picked is None:
                typer.echo("[skip] blank choice - untouched.")
                skipped += 1
                continue
            chosen_desc = picked

        assert chosen_desc is not None
        stem = format_stem(metrics.distance_km, metrics.ascent_m, chosen_desc, units=units)
        canonical_name = f"{stem}.gpx"
        outfile = allocate_unique_gpx_basename(
            dest_root,
            stem,
            occupied=basename_occupied,
            overwrite_conflicts=force,
        )

        if outfile is None:
            typer.echo(f"[skip] {canonical_name} exists - rerun with `--force`.")
            skipped += 1
            continue

        dest_abs = dest_root / outfile
        msg = _friendly_dest_message(dest_abs)
        write_renamed_copy(
            path,
            dest_root,
            distance_km=metrics.distance_km,
            ascent_m=metrics.ascent_m,
            description=chosen_desc,
            dest_filename=outfile,
        )
        copied += 1
        if outfile != canonical_name:
            typer.echo(f"wrote {msg} (suffix added - duplicate basename in this run)")
        else:
            typer.echo(f"wrote {msg}")

    typer.echo(f"\nCopied {copied} file(s); skipped {skipped}.")


def main() -> None:
    """Console script entry."""

    app()
