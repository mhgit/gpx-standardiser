"""Minimal GPX documents for deterministic tests."""

from __future__ import annotations

from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint, GPXTrackSegment


def track_xml_simple(
    points: list[tuple[float, float, float | None]],
    *,
    add_second_track: bool = False,
) -> str:
    root = GPX()
    segment = GPXTrackSegment()

    for lat, lon, ele in points:
        pt = GPXTrackPoint(latitude=lat, longitude=lon, elevation=ele)
        segment.points.append(pt)

    primary = GPXTrack(name="fixture")
    primary.segments.append(segment)
    root.tracks.append(primary)

    if add_second_track:
        extra_seg = GPXTrackSegment()
        extra_seg.points.extend(
            [
                GPXTrackPoint(latitude=0.02, longitude=0.02, elevation=123.0),
                GPXTrackPoint(latitude=0.03, longitude=0.03, elevation=133.0),
            ]
        )
        extra = GPXTrack(name="noise")
        extra.segments.append(extra_seg)
        root.tracks.append(extra)

    blob = root.to_xml()
    if isinstance(blob, bytes):  # pragma: no cover
        return blob.decode("utf-8")
    return blob
