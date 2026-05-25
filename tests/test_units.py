"""Output unit conversion."""

from __future__ import annotations

from gpx_standardiser.naming import format_stem
from gpx_standardiser.units import OutputUnits, convert_for_output, metrics_headline


def test_convert_for_output_metric_is_identity() -> None:
    assert convert_for_output(107, 547, OutputUnits.METRIC) == (107, 547)


def test_convert_for_output_imperial_rounds() -> None:
    assert convert_for_output(107, 547, OutputUnits.IMPERIAL) == (66, 1795)


def test_format_stem_imperial_default() -> None:
    stem = format_stem(107, 547, "Staplehurst")
    assert stem == "066mls-1795ft@Staplehurst"


def test_format_stem_metric_explicit() -> None:
    stem = format_stem(107, 547, "Staplehurst", units=OutputUnits.METRIC)
    assert stem == "107km-547m@Staplehurst"


def test_metrics_headline_imperial() -> None:
    assert metrics_headline(10, 305, OutputUnits.IMPERIAL) == "6 mls - 1001 ft climb"


def test_metrics_headline_metric() -> None:
    assert metrics_headline(10, 305, OutputUnits.METRIC) == "10 km - 305 m climb"
