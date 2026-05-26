"""Plan CSV report."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from fixtures.gpx_build import track_xml_simple
from gpx_standardiser.plan_report import build_plan_report_rows, format_plan_report_csv


def test_build_and_format_csv_row(tmp_path: Path) -> None:
    gpx_txt = track_xml_simple([(0.01, -0.01, 101.0), (0.02, -0.02, 105.5)])
    gp = tmp_path / "107km-547m@Legacy.gpx"
    gp.write_text(gpx_txt, encoding="utf-8")

    rows = build_plan_report_rows([gp])
    assert len(rows) == 1
    assert rows[0].ok
    assert rows[0].filename == "107km-547m@Legacy.gpx"
    assert rows[0].kilometers is not None
    assert rows[0].miles is not None
    assert rows[0].rank == 1

    payload = format_plan_report_csv(rows)
    parsed = list(csv.DictReader(io.StringIO(payload)))
    assert parsed[0]["Filename"] == "107km-547m@Legacy.gpx"
    assert parsed[0]["Kilometers"]
    assert parsed[0]["Miles"]
    assert parsed[0]["DifficultyTier"]
    assert parsed[0]["Rank"] == "1"


def test_error_row_in_csv(tmp_path: Path) -> None:
    bad = tmp_path / "empty.gpx"
    bad.write_text(
        '<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"></gpx>',
        encoding="utf-8",
    )
    rows = build_plan_report_rows([bad])
    assert len(rows) == 1
    assert not rows[0].ok
    assert rows[0].error

    payload = format_plan_report_csv(rows)
    parsed = list(csv.DictReader(io.StringIO(payload)))
    assert parsed[0]["Error"]
    assert parsed[0]["Rank"] == ""


def test_batch_rank_orders_by_m_per_km(tmp_path: Path) -> None:
    flat = tmp_path / "flat.gpx"
    flat.write_text(
        track_xml_simple([(0.01, -0.01, 100.0), (0.02, -0.01, 100.0)]),
        encoding="utf-8",
    )
    hilly = tmp_path / "hilly.gpx"
    hilly.write_text(
        track_xml_simple([(0.01, -0.01, 100.0), (0.011, -0.01, 150.0), (0.012, -0.01, 200.0)]),
        encoding="utf-8",
    )

    rows = build_plan_report_rows([flat, hilly])
    ok_rows = [r for r in rows if r.ok]
    assert len(ok_rows) == 2
    by_name = {r.filename: r for r in ok_rows}
    assert by_name["hilly.gpx"].rank == 1
    assert by_name["flat.gpx"].rank == 2
