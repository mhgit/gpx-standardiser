"""CLI plan --interactive (Typer runner)."""

from pathlib import Path

from typer.testing import CliRunner

from fixtures.gpx_build import track_xml_simple
from gpx_standardiser.cli import app


def test_plan_interactive_report_after_prompts(tmp_path: Path) -> None:
    monkey_points = [(0.01, -0.01, 101.0), (0.02, -0.02, 105.5)]
    gpx_txt = track_xml_simple(monkey_points)
    gp = tmp_path / "Tanhouse_53_Miles.gpx"
    gp.write_text(gpx_txt, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["plan", "-i", str(gp)],
        input="ChairDemoRoute\n",
    )
    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    out = result.stdout
    assert "Plan report (nothing written)" in out
    assert "Would rename: 1" in out
    assert "skipped: 0" in out
    assert "errors: 0" in out
    assert "ChairDemoRoute" in out
    assert "Tanhouse_53_Miles.gpx ->" in out


def test_plan_interactive_blank_skips_and_reports(tmp_path: Path) -> None:
    gpx_txt = track_xml_simple([(0.01, -0.01, 100.0), (0.02, -0.02, 102.0)])
    gp = tmp_path / "107_108_109.gpx"
    gp.write_text(gpx_txt, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["plan", "--interactive", str(gp)], input="\n")
    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    out = result.stdout
    assert "SKIPPED (blank)" in out
    assert "Would rename: 0" in out
    assert "skipped: 1" in out
