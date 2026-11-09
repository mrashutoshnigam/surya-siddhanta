"""Tests for the tools added after the coverage audit: find_new_full_moon,
compute_latitude_from_shadow and identify_star (chatbot/tools.py)."""
import json

import pytest

from suryasiddhanta.chatbot.tools import dispatch_tool


def _call(name, **args):
    """Dispatch a tool and parse its JSON result."""
    return json.loads(dispatch_tool(name, args))


def test_current_datetime_in_requested_zone():
    """
    The clock tool reports now in the zone asked, with a library JD that
    round-trips to the same civil date.
    Expected: zone label UTC+05:30, and the date matches clock_from_jd(jd).
    """
    from suryasiddhanta.ch01_mean_motions import clock_from_jd

    r = _call("get_current_datetime", utc_offset=5.5)
    assert r["zone"] == "UTC+05:30"
    y, m, d, _ = clock_from_jd(r["jd"], 5.5)
    assert f"{y}-{m:02d}-{d:02d}" == r["date"]


def test_new_and_full_moons_alternate_after_start():
    """
    Two of each kind from a date come back in time order, all on or after the
    start, alternating new and full about 14.8 days apart.
    Expected: four events, kinds alternate, gaps between 13 and 16.5 days.
    """
    r = _call("find_new_full_moon", year=2026, month=10, day=20, count=2)
    events = r["events"]
    assert len(events) == 4
    kinds = [e["kind"] for e in events]
    assert all(a != b for a, b in zip(kinds, kinds[1:]))
    gaps = [b["jd"] - a["jd"] for a, b in zip(events, events[1:])]
    assert all(13.0 < g < 16.5 for g in gaps)


def test_full_moon_matches_fathers_midnight():
    """
    The full moon is the Fathers' midnight (Ch.14 v.14), found by a different
    solver in ch14, so the two must agree.
    Expected: the next full moon and the next pitrya midnight within an hour.
    """
    full = _call("find_new_full_moon", year=2026, month=10, day=20, kind="full")["events"][0]
    clock = _call("compute_pitrya_clock", year=2026, month=10, day=20)
    assert full["jd"] == pytest.approx(clock["next_midnight_jd"], abs=1 / 24)


def test_bad_kind_is_an_error():
    """
    An unknown kind is reported, not raised.
    Expected: a JSON object with an "error" key.
    """
    assert "error" in _call("find_new_full_moon", year=2026, kind="half")


def test_latitude_from_shadow_round_trips_ujjain():
    """
    The noon shadow that compute_gnomon_shadow gives at Ujjain on the
    equinox, fed back into compute_latitude_from_shadow, recovers Ujjain's
    latitude.
    Expected: 23.18 deg within 0.1 deg (the shadow is rounded to 0.01).
    """
    noon = 21 + (12 + (5.5 - 75.78 / 15)) / 24  # Ujjain mean noon, in IST
    shadow = _call("compute_gnomon_shadow", year=2026, month=3, day=noon,
                   latitude=23.18, longitude=75.78)
    r = _call("compute_latitude_from_shadow", shadow_length=shadow["shadow_length"],
              year=2026, month=3, day=21, shadow_direction="north")
    assert r["latitude"] == pytest.approx(23.18, abs=0.1)


def test_identify_star_at_rohini():
    """
    A position at Rohini's junction star names Rohini both as the nearest
    star and as the containing segment.
    Expected: nearest "Rohini" within a degree, segment "Rohini".
    """
    r = _call("identify_star", longitude=49.75, latitude=-4.5)
    assert r["nearest_yogatara"]["name"] == "Rohini"
    assert r["nearest_yogatara"]["separation_deg"] < 1.0
    assert r["nakshatra_segment"] == "Rohini"
