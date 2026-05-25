"""Rename/copy helpers touching GPX."""

from pathlib import Path

import gpxpy

from fixtures.gpx_build import track_xml_simple
from gpx_standardiser.rename import apply_description_metadata, plan_row, write_renamed_copy


def test_plan_row_reflects_hints(tmp_path: Path) -> None:
    monkey_points = [(0.01, -0.01, 101.0), (0.02, -0.02, 105.5)]
    gpx_txt = track_xml_simple(monkey_points)
    gp = tmp_path / "Tanhouse_53_Miles.gpx"
    gp.write_text(gpx_txt, encoding="utf-8")
    row = plan_row(gp, gpx_txt)
    assert row.hint == "Tanhouse"
    assert row.proposed_stem().endswith("@Tanhouse")


def test_write_renamed_copy_keeps_source(tmp_path: Path) -> None:
    src_txt = track_xml_simple(
        [
            (51.258, -0.003, 100.0),
            (51.259, -0.002, 118.5),
            (51.2595, -0.0019, 120.7),
        ]
    )

    inp = tmp_path / "dirty_name_45km.gpx"
    inp.write_text(src_txt, encoding="utf-8")
    unchanged = inp.read_bytes()

    outp = tmp_path / "done"
    write_renamed_copy(
        inp,
        outp,
        distance_km=999,
        ascent_m=1000,
        description="SmokeTest",
        dest_filename="999km-1000m@SmokeTest.gpx",
    )

    produced = outp / "999km-1000m@SmokeTest.gpx"
    assert inp.read_bytes() == unchanged

    rewritten = produced.read_text(encoding="utf-8")
    rebuilt = gpxpy.parse(rewritten)
    assert rebuilt.name == "SmokeTest"
    assert rebuilt.tracks[0].name == "SmokeTest"


def test_apply_description_updates_names() -> None:
    snippet = track_xml_simple(
        [
            (0.41, -0.2, 5.0),
            (0.42, -0.19, 9.8),
        ]
    )

    rewritten = apply_description_metadata(snippet, "Head-unit label")
    reparsed = gpxpy.parse(rewritten)
    assert reparsed.name == "Head-unit label"
    assert reparsed.tracks[0].name == "Head-unit label"
