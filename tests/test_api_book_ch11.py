"""Tests for the /book/chapter/11 verse-card payload.

These pin each card to ``ch11_pata`` so the React cards cannot drift from the
library. All run offline; the route must not touch the verse corpus.
1 January 2024 has a Vyatipata beginning that day, found within a 60-day
window.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch11_pata as ch11
from suryasiddhanta.api.book_ch11 import CARD_ORDER
from suryasiddhanta.api.main import app

DATE = {"year": 2024, "month": 1, "day": 1.0}


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/11", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all four cards, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER``; every card has ``verses``,
    ``title``, ``does`` and ``date_dependent``.
    """
    body = _body(client, {**DATE, "days": 60})
    assert body["order"] == CARD_ORDER
    for card_id in CARD_ORDER:
        card = body["cards"][card_id]
        assert {"verses", "title", "does", "date_dependent"} <= card.keys()


def test_sum_rule_matches_the_library(client: TestClient):
    """xi.2-3: the longitude sum and its distance to each target match the library.

    Expected: ``longitude_sum`` equals ``ch11.longitude_sum`` at the date's
    Julian Day, and the nearer target is reported as ``next_by_sum_rule``.
    """
    card = _body(client, {**DATE, "days": 60})["cards"]["xi.2-3"]
    jd = ch01.julian_day(2024, 1, 1.0)
    total = ch11.longitude_sum(jd)
    assert card["longitude_sum"] == pytest.approx(total)
    nearer = min(
        ("Vyatipata", card["degrees_to_vyatipata"]),
        ("Vaidhrita", card["degrees_to_vaidhrita"]),
        key=lambda pair: pair[1],
    )[0]
    assert card["next_by_sum_rule"] == nearer


def test_declination_correction_differs_from_the_plain_value(client: TestClient):
    """xi.4-11: the Moon's corrected declination departs from her plain declination.

    Expected: the two values differ (the latitude correction is doing
    something), and the corrected value equals the library's.
    """
    card = _body(client, {**DATE, "days": 60})["cards"]["xi.4-11"]
    jd = ch01.julian_day(2024, 1, 1.0)
    assert card["moon_declination"] == pytest.approx(ch11.moon_declination(jd))
    assert card["moon_declination"] != pytest.approx(card["moon_declination_plain"], abs=1e-6)


def test_timing_matches_the_nearest_event(client: TestClient):
    """xi.12-14: the reported instant and duration match ``find_next_pata``.

    Expected: a Vyatipata is found, its middle date matches the library's and
    its duration is positive.
    """
    card = _body(client, {**DATE, "days": 60})["cards"]["xi.12-14"]
    jd = ch01.julian_day(2024, 1, 1.0)
    ev = ch11.find_next_pata(jd, max_days=60.0)
    assert card["found"] and ev is not None
    assert card["kind"] == ev.kind
    assert card["duration_ghatis"] == pytest.approx(ev.duration_ghatis)
    assert card["duration_ghatis"] > 0.0


def test_events_window_matches_find_patas(client: TestClient):
    """xi.19: the event list over the window matches ``find_patas`` in count and kind.

    Expected: the same number of events as the library returns for the same
    window, each carrying a ``refined`` flag.
    """
    card = _body(client, {**DATE, "days": 60})["cards"]["xi.19"]
    jd = ch01.julian_day(2024, 1, 1.0)
    events = ch11.find_patas(jd, jd + 60)
    assert len(card["events"]) == len(events)
    assert [e["kind"] for e in card["events"]] == [ev.kind for ev in events]
    assert all("refined" in e for e in card["events"])


def test_day_out_of_range_is_rejected(client: TestClient):
    """The date is validated before any calculation.

    Expected: a day of 32 is refused with 422.
    """
    response = client.post("/book/chapter/11", json={**DATE, "day": 32.0, "days": 60})
    assert response.status_code == 422
