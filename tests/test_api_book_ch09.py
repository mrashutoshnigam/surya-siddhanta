"""Tests for the /book/chapter/9 verse-card payload.

These pin each card to ``ch09_heliacal`` so the React cards cannot drift from
the library. All run offline; the route must not touch the verse corpus.
Venus on 1 January 2024 is a morning star about to be lost in the Sun's glare.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch09_heliacal as ch09
from suryasiddhanta.api.book_ch09 import CARD_ORDER
from suryasiddhanta.api.main import app

VENUS = {"planet": "Venus", "year": 2024, "month": 1, "day": 1.0, "months": 12}


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/9", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all five cards, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER``; every card has ``verses``,
    ``title``, ``does`` and ``date_dependent``.
    """
    body = _body(client, VENUS)
    assert body["order"] == CARD_ORDER
    for card_id in CARD_ORDER:
        card = body["cards"][card_id]
        assert {"verses", "title", "does", "date_dependent"} <= card.keys()


def test_threshold_table_is_the_librarys(client: TestClient):
    """The v.6-9 table lists each planet's (retrograde, direct) limits.

    Expected: one row per planet in ``VISIBILITY_THRESHOLDS`` with identical
    figures, and exactly the chosen planet selected.
    """
    card = _body(client, VENUS)["cards"]["ix.6-9"]
    assert {r["planet"]: (r["retrograde"], r["direct"]) for r in card["rows"]} == \
        ch09.VISIBILITY_THRESHOLDS
    assert [r["planet"] for r in card["rows"] if r["selected"]] == ["Venus"]


def test_visibility_matches_the_library(client: TestClient):
    """The visibility card agrees with ``is_planet_visible`` and the signed elongation.

    Expected: ``visible`` and ``elongation`` equal the library's at the same
    JD; the margin is |elongation| less the threshold.
    """
    card = _body(client, VENUS)["cards"]["ix.6-9"]
    jd = ch01.julian_day(2024, 1, 1.0)
    assert card["visible"] == ch09.is_planet_visible("Venus", jd)
    assert card["elongation"] == pytest.approx(ch09.sun_elongation("Venus", jd))
    assert card["margin"] == pytest.approx(abs(card["elongation"]) - card["threshold"])


def test_direction_rule_follows_v2_and_v3(client: TestClient):
    """A direct Venus west of the Sun is about to set in the east (swift rule).

    Expected: negative elongation, rule ``swift``, event ``setting``,
    horizon ``east``; Jupiter on the same date follows the slow rule.
    """
    venus = _body(client, VENUS)["cards"]["ix.2-3"]
    assert venus["elongation"] < 0 and not venus["retrograde"]
    assert (venus["rule"], venus["event"], venus["horizon"]) == ("swift", "setting", "east")
    jupiter = _body(client, {**VENUS, "planet": "Jupiter"})["cards"]["ix.2-3"]
    assert jupiter["rule"] == "slow"


def test_next_event_hand_method_is_signed_and_near_the_library(client: TestClient):
    """The one-step days-to-event figure is positive and the library's event follows.

    Expected: the wanted event is ``setting`` (Venus is visible), the hand
    figure is positive and within ten days of the library's scan, which is
    the date of ``ch09.next_heliacal``.
    """
    card = _body(client, VENUS)["cards"]["ix.10-11"]
    jd = ch01.julian_day(2024, 1, 1.0)
    expected = ch09.next_heliacal("Venus", jd, "setting")
    assert card["event"] == "setting"
    assert card["library"]["jd"] == expected.jd
    assert card["hand_days"] > 0
    assert card["days_apart"] < 10


def test_next_event_without_a_hand_figure_when_the_planet_is_closing_the_wrong_way(client: TestClient):
    """Mercury just inside its limit and nearing the Sun has no one-step answer.

    Expected: ``hand_days`` is None (the planet must first pass the Sun)
    while the library still finds the rising.
    """
    card = _body(client, {"planet": "Mercury", "year": 2024, "month": 6, "day": 1.0,
                          "months": 12})["cards"]["ix.10-11"]
    assert card["event"] == "rising"
    assert card["hand_days"] is None
    assert card["library"] is not None


def test_events_match_visibility_events_after_the_date(client: TestClient):
    """The events list is the library's, cut to those after the date.

    Expected: every event is at or after the date, alternating rising and
    setting, and the first one equals the library's first event after it.
    """
    card = _body(client, VENUS)["cards"]["ix.6-11"]
    jd = ch01.julian_day(2024, 1, 1.0)
    events = card["events"]
    assert events and all(e["jd"] >= jd for e in events)
    types = [e["type"] for e in events]
    assert all(a != b for a, b in zip(types, types[1:]))
    lib = [e for e in ch09.visibility_events("Venus", 2024, 12) if e.jd >= jd]
    assert events[0]["jd"] == lib[0].jd


def test_star_card_lists_the_verse_groups(client: TestClient):
    """The star card is static: five limits and the six never-extinguished stars.

    Expected: limits 13, 14, 15, 21 and 17 degrees, and Abhijit among the
    stars that are never swallowed by the Sun's rays.
    """
    card = _body(client, VENUS)["cards"]["ix.12-18"]
    assert [g["degrees"] for g in card["groups"]] == [13, 14, 15, 21, 17]
    assert "Abhijit" in card["circumpolar"]


def test_unknown_planet_is_rejected(client: TestClient):
    """The Sun is not a heliacal planet.

    Expected: the schema answers 422 before any calculation runs.
    """
    response = client.post("/book/chapter/9", json={**VENUS, "planet": "Sun"})
    assert response.status_code == 422


def test_window_is_bounded(client: TestClient):
    """The events scan is daily, so the months field has a ceiling.

    Expected: 37 months is refused with 422.
    """
    response = client.post("/book/chapter/9", json={**VENUS, "months": 37})
    assert response.status_code == 422
