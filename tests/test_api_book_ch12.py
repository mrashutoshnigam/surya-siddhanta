"""Tests for the /book/chapter/12 verse-card payload.

These pin each card to ``ch12_cosmography`` so the React cards cannot drift
from the library. All run offline; the route must not touch the verse corpus.
Chapter 12 is mostly fixed dimensions, so only the regents and the Brahma-day
card depend on the date, and only two cards on the place.
"""
from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch12_cosmography as ch12
from suryasiddhanta.api.book_ch12 import CARD_ORDER
from suryasiddhanta.api.main import app

BODY = {"year": 2024, "month": 1, "day": 1.0, "latitude": 23.18, "longitude": 75.78}


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict = BODY) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/12", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries every card, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER``; every card has ``verses``,
    ``title``, ``does`` and ``date_dependent``.
    """
    body = _body(client)
    assert body["order"] == CARD_ORDER
    for card_id in CARD_ORDER:
        assert {"verses", "title", "does", "date_dependent"} <= body["cards"][card_id].keys()


def test_sphere_aspect_follows_the_latitude(client: TestClient):
    """xii.42-44: the sphere's aspect is the library's for the place's latitude.

    Expected: Ujjain is oblique with the pole raised by its latitude; the
    equator is "right" with a thirty-ghati day.
    """
    card = _body(client)["cards"]["xii.42-44"]
    assert card["kind"] == "oblique"
    assert card["pole_altitude"] == pytest.approx(23.18)
    equator = _body(client, {**BODY, "latitude": 0.0})["cards"]["xii.42-44"]
    assert equator["kind"] == "right" and equator["day_ghatis"] == 30.0


def test_earth_card_matches_the_library(client: TestClient):
    """xii.59-61: circumference, parallel, desantara and polar-day limit agree.

    Expected: circumference is 1600 * sqrt(10); the parallel is the corrected
    circumference at the latitude; the polar-day limit is 66 degrees.
    """
    card = _body(client)["cards"]["xii.59-61"]
    assert card["circumference"] == pytest.approx(1600 * math.sqrt(10))
    assert card["corrected_circumference"] == pytest.approx(ch12.corrected_circumference(23.18))
    assert card["desantara_yojanas"] == pytest.approx(ch12.desantara_yojanas(23.18, 75.78))
    # Ujjain is on the Lanka meridian (SS i.62): no difference of longitude.
    assert card["desantara_yojanas"] == pytest.approx(0.0)
    assert card["moon_correction_arcmin"] == pytest.approx(0.0)
    assert card["polar_day_limit"]["latitude"] == pytest.approx(66.0)


def test_invisibility_and_overhead_band(client: TestClient):
    """xii.63-68: two invisibility parallels and the overhead band match the library.

    Expected: two limits, two-sign case first, and a band of 24 degrees.
    """
    card = _body(client)["cards"]["xii.63-68"]
    assert [l["signs_invisible"] for l in card["limits"]] == [2, 4]
    assert card["limits"][0]["latitude"] == pytest.approx(ch12.invisibility_limits()[0]["latitude"])
    assert card["overhead_band"]["degrees"] == pytest.approx(24.0)


def test_cities_clock_noon_at_ujjayini(client: TestClient):
    """xii.70-71: local hours at every reference place given noon at Ujjayini.

    Expected: Ujjayini reads 12 and the rest match ``cities_clock``.
    """
    card = _body(client)["cards"]["xii.70-71"]
    expected = ch12.cities_clock("Ujjayini", 12.0)
    assert card["anchor"] == "Ujjayini"
    assert {r["name"]: r["hour"] for r in card["hours"]} == pytest.approx(expected)
    assert expected["Ujjayini"] == pytest.approx(12.0)


def test_days_of_gods_manes_and_brahma(client: TestClient):
    """xii.74: the three days and how far into Brahma's day the date falls.

    Expected: figures match the library; the elapsed fraction is just over half.
    """
    card = _body(client)["cards"]["xii.74"]
    jd = ch01.julian_day(2024, 1, 1.0)
    assert card["day_of_the_gods"] == pytest.approx(ch12.day_of_the_gods())
    assert card["day_of_the_manes"] == pytest.approx(ch12.day_of_the_manes())
    assert card["brahma"]["fraction"] == pytest.approx(ch12.brahma_day_elapsed(jd)["fraction"])
    assert 0.45 < card["brahma"]["fraction"] < 0.5


def test_regents_match_the_library(client: TestClient):
    """xii.78-79: regents of day, month and year, and the day's twenty-four horas.

    Expected: names equal the library's; 24 horas starting with the day's lord.
    """
    card = _body(client)["cards"]["xii.78-79"]
    jd = ch01.julian_day(2024, 1, 1.0)
    assert card["day"] == ch12.regent_of_day(jd)
    assert card["month"] == ch12.regent_of_month(jd)
    assert card["year"] == ch12.regent_of_year(jd)
    assert len(card["horas"]) == 24 and card["horas"][0] == card["day"]


def test_orbits_are_per_kalpa(client: TestClient):
    """xii.80-90: the orbit table matches the library, Moon first at 324,000.

    Expected: Moon orbit 324,000 with revolutions per kalpa (not per mahayuga),
    the ether orbit equals the text's 18,712,080,864,000,000, and every orbit
    carries its stated figure and difference.
    """
    card = _body(client)["cards"]["xii.80-90"]
    moon = card["orbits"][0]
    assert moon["body"] == "Moon"
    assert moon["orbit_yojanas"] == pytest.approx(324_000)
    assert moon["revolutions_per_kalpa"] == 57_753_336_000
    assert card["ether_orbit"] == 18_712_080_864_000_000
    assert card["daily_linear_motion"] == pytest.approx(ch12.daily_linear_motion())
    assert all("stated_yojanas" in o and "stated_difference" in o for o in card["orbits"])


def test_date_independent_cards_ignore_the_date(client: TestClient):
    """``date_dependent`` is honest: changing the date leaves those cards unchanged.

    Expected: cards flagged False are identical for two different years.
    """
    a = _body(client)
    b = _body(client, {**BODY, "year": 1500})
    for card_id in CARD_ORDER:
        if not a["cards"][card_id]["date_dependent"]:
            assert a["cards"][card_id] == b["cards"][card_id]


def test_bad_inputs_are_rejected(client: TestClient):
    """Inputs are validated before any calculation.

    Expected: a day of 32 and a latitude of 91 are refused with 422.
    """
    assert client.post("/book/chapter/12", json={**BODY, "day": 32.0}).status_code == 422
    assert client.post("/book/chapter/12", json={**BODY, "latitude": 91.0}).status_code == 422
