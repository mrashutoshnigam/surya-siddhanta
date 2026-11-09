"""Tests for the six Chapter 14 chatbot tools in chatbot/tools.py.

Each tool wraps a ch14_reckoning_time function and shapes it for the LLM
(and the MCP server, which serves the same registry): JSON out, event times
as local clock strings in the requested zone, errors as JSON not exceptions.
"""
import json

import pytest

from suryasiddhanta.chatbot.tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS, dispatch_tool

CH14_TOOLS = {
    "reckon_time", "convert_time_measure", "compute_solar_year",
    "compute_sankranti_punyakala", "compute_pitrya_clock", "compute_barhaspatya_year",
}


def _call(name, **args):
    """Dispatch a tool and parse its JSON result."""
    return json.loads(dispatch_tool(name, args))


def test_ch14_tools_registered():
    """
    All six Ch.14 tools are both defined for the model and dispatchable.
    Expected: each name appears in TOOL_DEFINITIONS and TOOL_FUNCTIONS.
    """
    defined = {d["name"] for d in TOOL_DEFINITIONS}
    assert CH14_TOOLS <= defined
    assert CH14_TOOLS <= set(TOOL_FUNCTIONS)


def test_makara_sankranti_falls_in_requested_gregorian_year():
    """
    Makara entry belongs to the solar year that began the April before, so
    the tool must look one solar year back to find the January event.
    Expected: Makara 2027 is reported on 2027-01-14 or 15 IST, with a
    punyakala window that brackets the entry.
    """
    r = _call("compute_sankranti_punyakala", year=2027, sign="Makara")
    assert "error" not in r
    assert r["sign"] == "Makara"
    assert r["local"].startswith(("2027-01-14", "2027-01-15"))
    assert r["punyakala_begin"] < r["local"] < r["punyakala_end"]


def test_sankranti_accepts_english_sign_name_and_index():
    """
    The sign may be given as an English name or an index 0-11.
    Expected: "aries" and 0 name the same Mesha entry.
    """
    by_name = _call("compute_sankranti_punyakala", year=2026, sign="aries")
    by_index = _call("compute_sankranti_punyakala", year=2026, sign=0)
    assert by_name["sign"] == by_index["sign"] == "Mesha"
    assert by_name["jd"] == by_index["jd"]


def test_sankranti_unknown_sign_returns_error():
    """
    An unrecognised sign is reported back to the model, not raised.
    Expected: a JSON object with an "error" key.
    """
    assert "error" in _call("compute_sankranti_punyakala", year=2026, sign="Ophiuchus")


def test_convert_year_of_gods_to_civil_days():
    """
    One daiva unit (a day and night of the gods) is one sidereal year.
    Expected: about 365.26 savana days.
    """
    r = _call("convert_time_measure", value=1, from_mana="daiva", to_mana="savana")
    assert r["result"] == pytest.approx(365.2588, abs=1e-3)


def test_convert_unknown_mana_lists_known_keys():
    """
    A bad mana key comes back as an error listing the nine valid keys, so
    the model can retry.
    Expected: "error" plus a nine-item "known_manas" list.
    """
    r = _call("convert_time_measure", value=1, from_mana="weeks", to_mana="savana")
    assert "error" in r
    assert len(r["known_manas"]) == 9


def test_solar_year_shape_and_local_times():
    """
    The solar year carries twelve sankrantis, six ritus, both ayanas and both
    visuvats, each event with a local clock string.
    Expected: counts 12 and 6, and "local" strings labelled with the zone.
    """
    r = _call("compute_solar_year", year=2026)
    assert len(r["sankrantis"]) == 12
    assert len(r["ritus"]) == 6
    assert set(r["ayanas"]) == {"dakshinayana", "uttarayana"}
    assert "UTC+05:30" in r["sankrantis"][0]["local"]
    assert "start_local" in r["ritus"][0]


def test_utc_offset_shifts_reported_clock():
    """
    Event times come back in the zone asked for.
    Expected: the same Mesha entry labelled UTC+00:00 when utc_offset=0.
    """
    r = _call("compute_sankranti_punyakala", year=2026, sign="Mesha", utc_offset=0)
    assert "UTC+00:00" in r["local"]


def test_reckon_time_has_nine_readings():
    """
    The panorama expresses one moment in each of the nine manas.
    Expected: nine readings and a summary naming the brahma reading.
    """
    r = _call("reckon_time", year=2026, month=10, day=18)
    assert len(r["readings"]) == 9
    assert "brahma" in r["summary"]


def test_pitrya_clock_next_events_are_in_the_future():
    """
    The Fathers' clock reports their next noon (new moon) and midnight (full
    moon) after the moment asked.
    Expected: both next-event JDs exceed the moment's JD and hour is 0-24.
    """
    r = _call("compute_pitrya_clock", year=2026, month=10, day=18)
    assert 0 <= r["hour"] < 24
    assert r["next_noon_jd"] > r["jd"] and r["next_midnight_jd"] > r["jd"]


def test_barhaspatya_year_mean_is_commentary():
    """
    The mean method is Burgess's reading, not a rule from the verse.
    Expected: source "commentary", a month name, and the sixty-year name.
    """
    r = _call("compute_barhaspatya_year", year=2026, month=10, day=18)
    assert r["source"] == "commentary"
    assert r["name"] and r["sixty_year_name"]
