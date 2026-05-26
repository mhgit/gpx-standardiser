"""CLI plan --report-csv."""

from pathlib import Path

from typer.testing import CliRunner

from fixtures.gpx_build import track_xml_simple
from gpx_standardiser.cli import app


def test_plan_report_csv_stdout(tmp_path: Path) -> None:
    gpx_txt = track_xml_simple([(0.01, -0.01, 101.0), (0.02, -0.02, 105.5)])
    gp = tmp_path / "sample.gpx"
    gp.write_text(gpx_txt, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["plan", "--report-csv", str(gp)])
    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    out = result.stdout
    assert out.startswith("Filename,Miles,Ascent Feet,Kilometers,Ascent Meters")
    assert "sample.gpx" in out
    assert "original basename" not in out


def test_plan_report_csv_rejects_interactive(tmp_path: Path) -> None:
    gpx_txt = track_xml_simple([(0.01, -0.01, 101.0), (0.02, -0.02, 105.5)])
    gp = tmp_path / "sample.gpx"
    gp.write_text(gpx_txt, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["plan", "--report-csv", "-i", str(gp)])
    assert result.exit_code != 0
    assert "interactive" in (result.stdout + (result.stderr or "")).lower()
