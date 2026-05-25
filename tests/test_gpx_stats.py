"""Tests for GPX maths (ADR-0003)."""

from __future__ import annotations

import pytest

import gpx_standardiser.gpx_stats as gs
from fixtures.gpx_build import track_xml_simple
from gpx_standardiser.gpx_stats import GpxAnalysisError, compute_track_metrics, total_ascent_metres


def test_three_metre_threshold_optional_gate() -> None:
    gain = total_ascent_metres([100.0, 103.9, 110.0], threshold=3.0)
    assert pytest.approx(gain) == 10.0


def test_default_counts_small_positive_steps() -> None:
    elevations = [100.0, 101.0, 101.5, 110.5]
    assert pytest.approx(total_ascent_metres(elevations)) == 10.5


def test_ascent_handles_short_series() -> None:
    assert total_ascent_metres([10.5]) == pytest.approx(0.0)
    assert total_ascent_metres([]) == pytest.approx(0.0)


def test_moving_average_short_series_returns_raw() -> None:
    elevations = list(range(5))
    smoothed = gs.smooth_elevation_moving_average(elevations, window=11)
    assert smoothed == elevations


def test_moving_average_smooths_then_sum_lowers_hf_plateau_noise() -> None:
    elevations: list[float] = []
    v = 100.0
    for i in range(250):
        elevations.append(v)
        v += 0.35 if i % 4 < 2 else -0.30

    raw_gain = gs.total_ascent_metres(elevations)
    smooth_gain = gs.total_ascent_metres(gs.smooth_elevation_moving_average(elevations, window=11))
    assert raw_gain > smooth_gain * 1.25
    assert smooth_gain >= 0.0


def test_horizontal_distance_via_monkeypatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gs, "_haversine_m", lambda *_args, **_kw: 750.25)
    pts = [
        (0.41, -0.2, 100.05),
        (0.419, -0.199, 134.93),
    ]
    text = track_xml_simple(pts)
    metrics = compute_track_metrics(text)
    assert metrics.distance_km == pytest.approx(1)
    assert metrics.ascent_m == pytest.approx(35)


def test_multi_track_logs_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gs, "_haversine_m", lambda *_args, **_kw: 100.0)
    pts = [
        (53.000, -1.540, 200.0),
        (53.001, -1.539, 210.0),
    ]
    text = track_xml_simple(pts, add_second_track=True)
    metrics = compute_track_metrics(text)
    assert any("track" in w.lower() for w in metrics.warnings)


def test_route_only_file_not_supported() -> None:
    from gpxpy.gpx import GPX, GPXRoute, GPXRoutePoint

    root = GPX()
    route = GPXRoute(name="solo")
    route.points.extend(
        [
            GPXRoutePoint(latitude=50.01, longitude=-0.1, elevation=10.0),
            GPXRoutePoint(latitude=50.02, longitude=-0.11, elevation=22.0),
        ]
    )
    root.routes.append(route)
    xml_blob = root.to_xml()
    if isinstance(xml_blob, bytes):  # pragma: no cover
        xml_blob = xml_blob.decode()
    with pytest.raises(GpxAnalysisError, match=r"route|rte"):
        compute_track_metrics(xml_blob)


def test_missing_elevation_raises() -> None:
    raw = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><name>X</name>
    <trkseg>
      <trkpt lat="51.0" lon="-0.1"></trkpt>
      <trkpt lat="51.005" lon="-0.099"></trkpt>
    </trkseg>
  </trk>
</gpx>
"""
    with pytest.raises(GpxAnalysisError):
        compute_track_metrics(raw)


def test_need_two_track_points_raises() -> None:
    lone = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><name>X</name>
    <trkseg>
      <trkpt lat="51.0" lon="-0.1"><ele>10</ele></trkpt>
    </trkseg>
  </trk>
</gpx>
"""
    with pytest.raises(GpxAnalysisError):
        compute_track_metrics(lone)


def test_totally_empty_gpx_errors() -> None:
    naked = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"></gpx>
"""
    with pytest.raises(GpxAnalysisError, match=r"trk"):
        compute_track_metrics(naked)


def test_route_nodes_warn_but_do_not_shadow_tracks() -> None:
    import gpxpy
    from gpxpy.gpx import GPXRoute, GPXRoutePoint

    scaffold = track_xml_simple(
        [
            (53.951, -1.068, 40.51),
            (53.952, -1.069, 45.93),
            (53.953, -1.0705, 50.24),
        ]
    )

    merged = gpxpy.parse(scaffold)

    diversion = GPXRoute(name="alt")
    diversion.points.extend(
        [
            GPXRoutePoint(latitude=53.961, longitude=-1.078, elevation=140.62),
            GPXRoutePoint(latitude=53.962, longitude=-1.079, elevation=154.71),
        ]
    )

    merged.routes.append(diversion)

    xml_combo = merged.to_xml()
    if isinstance(xml_combo, bytes):  # pragma: no cover
        xml_combo = xml_combo.decode()

    verdict = compute_track_metrics(xml_combo)
    assert any("route" in cue.lower() for cue in verdict.warnings)
