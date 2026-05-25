"""CLI `rename --help`: destination flags documentation."""

from typer.testing import CliRunner

from gpx_standardiser.cli import app


def test_rename_help_lists_destination_flags_not_outbound_files_alias() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["rename", "-h"])
    payload = result.stdout + (result.stderr or "")
    assert result.exit_code == 0, payload

    assert "--output-folder" in payload
    assert "-o, --output-folder" in payload
    assert "--outbound-files" not in payload
