"""Tests for the /book/chapter/8 verse-card payload.

The polar longitudes are derived here from the shares the verses print (v.2-5)
and the rule of v.1, then compared with ``ch08_stars``'s catalog, which was
taken from Burgess's table: the two routes agreeing is the check on both.
All run offline; the route must not touch the verse corpus.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch07_conjunctions as ch07
from suryasiddhanta import ch08_stars as ch08
from suryasiddhanta.api.book_ch08 import (
    BHOGA_MINUTES, CARD_ORDER, SHARES, dhruvaka_minutes,
)
from suryasiddhanta.api.main import app

BASE = {"star": "Rohini", "planet": "Jupiter", "year": 2024, "month": 1, "day": 1.0}


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/8", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all four cards, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER``; every card has ``verses``,
    ``title``, ``does``, ``date_dependent`` and ``text_verses``.
    """
    body = _body(client, BASE)
    assert body["order"] == CARD_ORDER
    for card_id in CARD_ORDER:
        for field in ("verses", "title", "does", "date_dependent", "text_verses"):
            assert field in body["cards"][card_id]


def test_dhruvaka_from_shares_equals_the_catalog_for_all_27():
    """v.1-5: share x 10 plus the earlier bhogas reproduces Burgess's table.

    Expected: for every one of the 27 asterisms the derived polar longitude
    is within 0.01 degree of ``NAKSHATRA_DATA``'s longitude.
    """
    for nak in ch08.NAKSHATRA_DATA:
        minutes, _ = dhruvaka_minutes(nak.number)
        assert minutes / 60.0 == pytest.approx(nak.longitude, abs=0.01), nak.name


def test_share_formula_on_a_worked_case():
    """v.1 worked by hand for Bharani.

    Expected: share 40 x 10 = 400' plus one bhoga of 800' is 1200', 20 degrees.
    """
    assert SHARES[2] == 40
    assert dhruvaka_minutes(2) == (1200.0, "share")
    assert BHOGA_MINUTES == 800


def test_positioned_asterisms_follow_the_verse_rules():
    """v.4: four asterisms are placed by position, not by share.

    Expected: Uttara-Ashadha at 260 (middle of Purva-Ashadha's bhoga), Shravana
    at 280 (end of Uttara-Ashadha's), Dhanishta at 290 (three-quarters through
    Shravana's), and none of them has a share.
    """
    for number, degrees in ((21, 260.0), (22, 280.0), (23, 290.0)):
        assert number not in SHARES
        minutes, rule = dhruvaka_minutes(number)
        assert minutes / 60.0 == pytest.approx(degrees)
        assert rule != "share"


def test_longitude_card_rows_all_match_and_flag_the_chosen_star(client: TestClient):
    """The card lists 27 rows, all agreeing with the library, one of them selected.

    Expected: 27 rows, every ``matches`` true, exactly one ``selected`` (Rohini),
    and Abhijit at the end of Purva-Ashadha equal to the library's Abhijit.
    """
    card = _body(client, BASE)["cards"]["viii.1-4"]
    assert len(card["rows"]) == 27
    assert all(r["matches"] for r in card["rows"])
    assert [r["name"] for r in card["rows"] if r["selected"]] == ["Rohini"]
    assert card["abhijit_degrees"] == pytest.approx(card["abhijit_library_degrees"], abs=0.01)


def test_latitude_card_lists_the_library_latitudes_and_abhijit(client: TestClient):
    """v.5-9: the 27 latitudes plus Abhijit's sixty degrees north.

    Expected: 28 rows; each latitude equals the catalog's; Abhijit is last at
    60 north; Pushya is on the ecliptic.
    """
    rows = _body(client, BASE)["cards"]["viii.5-9"]["rows"]
    assert len(rows) == 28
    for row in rows[:27]:
        assert row["latitude"] == ch08.get_nakshatra(row["name"]).latitude
    assert rows[-1]["name"] == "Abhijit" and rows[-1]["latitude"] == 60.0
    assert next(r for r in rows if r["name"] == "Pushya")["direction"] == "on the ecliptic"


def test_position_card_equals_star_position_and_rise_set(client: TestClient):
    """The applied card reports ``star_position`` and ``star_rise_set`` unchanged.

    Expected: tropical longitude, right ascension and declination equal the
    library's for Rohini on 1 January 2024; a rise and a set are reported.
    """
    card = _body(client, BASE)["cards"]["viii.1-9"]
    jd = ch01.julian_day(2024, 1, 1.0)
    pos = ch08.star_position("Rohini", jd)
    assert card["tropical_lon"] == pytest.approx(pos.tropical_lon)
    assert card["right_ascension"] == pytest.approx(pos.right_ascension)
    assert card["declination"] == pytest.approx(pos.declination_val)
    assert card["rise"] is not None and card["set"] is not None
    assert card["bhoga_of"] == "Rohini"


def test_circumpolar_star_has_no_rise(client: TestClient):
    """A star that never sets at a high latitude has no rise or set.

    Expected: Bharani (declination 27 N on 1 January 2024) at latitude 65 N reports
    ``circumpolar`` and no rise time.
    """
    card = _body(client, {**BASE, "star": "Bharani", "latitude": 65.0})["cards"]["viii.1-9"]
    assert card["circumpolar"] is True
    assert card["rise"] is None


def test_conjunction_card_equals_planet_star_conjunction(client: TestClient):
    """v.14-15: the card lists exactly the library's planet-star conjunctions.

    Expected: the same JDs, in order, for Jupiter and Rohini over 2024.
    """
    card = _body(client, BASE)["cards"]["viii.14-15"]
    expected = ch07.planet_star_conjunction("Jupiter", "Rohini", 2024, 12)
    assert [c["jd"] for c in card["conjunctions"]] == [c.jd for c in expected]
    assert card["star_longitude"] == 49.5


def test_corpus_records_are_named_for_the_cards_that_have_text(client: TestClient):
    """Ch.8's corpus numbering is out of step, so each card names its own records.

    Expected: the two table cards point at records 1-4 and 5; the applied
    cards point at none.
    """
    cards = _body(client, BASE)["cards"]
    assert cards["viii.1-4"]["text_verses"] == "1-4"
    assert cards["viii.5-9"]["text_verses"] == "5-5"
    assert cards["viii.1-9"]["text_verses"] is None
    assert cards["viii.14-15"]["text_verses"] is None


def test_out_of_range_inputs_are_rejected(client: TestClient):
    """The schema bounds the star, the planet, the window and the place.

    Expected: 422 for an unknown star, the Sun as the planet, 40 months and latitude 95.
    """
    for bad in ({**BASE, "star": "Vega"}, {**BASE, "planet": "Sun"},
                {**BASE, "months": 40}, {**BASE, "latitude": 95.0}):
        assert client.post("/book/chapter/8", json=bad).status_code == 422
