"""Tests for the compute_panchanga tool's instant, tithi name and tithi edges.

Offline: the tool calls the library directly. Dates are fixed so the
expected tithi changes are stable library results, not wall-clock readings.
"""
import json

from suryasiddhanta.chatbot.tools import TOOL_DEFINITIONS, dispatch_tool


def panchanga(**args):
    """compute_panchanga for 2026-10-28 (IST unless overridden), decoded."""
    return json.loads(dispatch_tool("compute_panchanga", {"year": 2026, "month": 10, "day": 28, **args}))


def test_panchanga_names_the_instant_it_used():
    """
    A whole day is local midnight and an hour moves the instant, and the
    result says which one it used (the model once reported a midnight result
    as 11:32).
    Expected: ``at`` reads 00:00 for the bare date and 11:30 for hour 11.5.
    """
    assert panchanga()["at"] == "2026-10-28 00:00 (UTC+05:30)"
    assert panchanga(hour=11.5)["at"] == "2026-10-28 11:30 (UTC+05:30)"


def test_fractional_day_matches_the_same_hour():
    """
    ``day`` with a fraction and ``day`` plus ``hour`` are the same moment.
    Expected: identical tithi, with 28.5 equal to 28 and hour 12.
    """
    assert panchanga(day=28.5)["tithi"] == panchanga(hour=12)["tithi"]


def test_tithi_has_name_paksha_and_edges_that_bracket_the_moment():
    """
    The tithi carries a name, paksha and start/end so a caller never guesses.
    At 11:30 IST on 2026-10-28 the library is in tithi 18 (Krishna Tritiya),
    which began at 06:30 that morning and ends at 04:26 the next.
    Expected: those values, to the minute.
    """
    tithi = panchanga(hour=11.5)["tithi"]
    assert (tithi["number"], tithi["name"], tithi["paksha"]) == (18, "Tritiya", "Krishna")
    assert tithi["starts"] == "2026-10-28 06:30 (UTC+05:30)"
    assert tithi["ends"] == "2026-10-29 04:26 (UTC+05:30)"


def test_midnight_and_late_morning_fall_in_different_tithis():
    """
    The same civil day can hold two tithis, which is why the instant matters.
    Expected: midnight is tithi 17 ending at 06:30, and the next tithi
    starts exactly where that one ends.
    """
    early, late = panchanga()["tithi"], panchanga(hour=11.5)["tithi"]
    assert (early["number"], late["number"]) == (17, 18)
    assert early["ends"] == late["starts"]


def test_tithi_edges_follow_the_requested_zone():
    """
    Edges come back in ``utc_offset``, like the instant.
    Expected: the same tithi ends 5h30m earlier on the clock in UTC.
    """
    ist = panchanga(hour=11.5)["tithi"]["ends"]
    utc = panchanga(hour=6.0, utc_offset=0)["tithi"]["ends"]
    assert ist == "2026-10-29 04:26 (UTC+05:30)"
    assert utc == "2026-10-28 22:56 (UTC+00:00)"


def test_hour_is_in_the_tool_schema():
    """
    The model can only pass ``hour`` if the schema offers it.
    Expected: compute_panchanga lists an ``hour`` property with a description.
    """
    schema = next(d for d in TOOL_DEFINITIONS if d["name"] == "compute_panchanga")["input_schema"]
    assert "description" in schema["properties"]["hour"]
