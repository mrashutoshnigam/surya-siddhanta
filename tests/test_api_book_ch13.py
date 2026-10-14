"""Tests for the /book/chapter/13 verse-card payload.

These pin each card to ``ch13_instruments`` so the React cards cannot drift
from the library. All run offline; the route must not touch the verse corpus.
The default is Ujjain on 1 January 2024, with a gnomon shadow of 20 digits
read in the forenoon (the Sun's noon shadow there is shorter than 12).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch13_instruments as ch13
from suryasiddhanta.api.book_ch13 import CARD_ORDER
from suryasiddhanta.api.main import app

BODY = {"year": 2024, "month": 1, "day": 1.0, "latitude": 23.18, "longitude": 75.78,
        "shadow": 20.0, "forenoon": True}
JD = ch01.julian_day(2024, 1, 1.0)


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict = BODY) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/13", json=payload)
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


def test_hoops_card_counts_match_the_sphere(client: TestClient):
    """xiii.4-9: the hoops card lists the great, solar and stellar hoops.

    Expected: 4 great circles, 6 solar hoops with the 24-degree extremes, and
    28 junction plus 7 fixed stellar hoops, the horizon excluded.
    """
    card = _body(client)["cards"]["xiii.4-9"]
    assert len(card["great"]) == 4
    assert len(card["solar"]) == 6
    assert max(abs(h["declination"]) for h in card["solar"]) == pytest.approx(24.0)
    assert card["stars"] == {"junction_stars": 28, "fixed_stars": 7}


def test_points_card_has_signs_and_the_chord(client: TestClient):
    """xiii.10-11: four cardinal points, twelve signs, and the chord of thirty.

    Expected: counts 4 and 12 and the library's chord of 30 degrees.
    """
    card = _body(client)["cards"]["xiii.10-11"]
    assert len(card["cardinal"]) == 4 and len(card["signs"]) == 12
    assert card["chord_of_thirty"] == pytest.approx(ch13.chord_of_thirty())
    assert card["signs"][1]["tropical_longitude"] == pytest.approx(30.0)


def test_lagnas_match_the_library(client: TestClient):
    """xiii.13-14: the lagna, asta-lagna, madhya-lagna and Sun for the moment.

    Expected: keys in the library's order and the asta-lagna 180 degrees from
    the lagna.
    """
    card = _body(client)["cards"]["xiii.13-14"]
    expected = ch13.sphere_points(JD, 23.18, 75.78)
    assert [p["key"] for p in card["points"]] == [p.key for p in expected]
    lagna, asta = card["points"][0], card["points"][1]
    assert (asta["tropical_longitude"] - lagna["tropical_longitude"]) % 360 == pytest.approx(180.0, abs=1e-3)


def test_sines_card_carries_both_antyas_and_the_pole(client: TestClient):
    """xiii.14-15: the sines for the Sun's declination, and the pole's altitude.

    Expected: both antya values match the library and the pole altitude equals
    the latitude.
    """
    card = _body(client)["cards"]["xiii.14-15"]
    sines = ch13.sphere_sines(23.18, ch13.sun_declination(JD))
    assert card["sines"]["antya_small_circle"] == pytest.approx(sines["antya_small_circle"])
    assert card["sines"]["antya_great_circle"] == pytest.approx(sines["antya_great_circle"])
    assert card["pole_altitude"] == pytest.approx(23.18)


def test_instruments_agree_on_the_time(client: TestClient):
    """xiii.20-24: the four instruments, fed one moment, give one time.

    Expected: the gnomon matches ``nara_yantra_time``; wheel, arc and staff
    agree with it to a few thousandths of a ghati; sources are verse for the
    gnomon and commentary for the rest; the clepsydra day matches the library.
    """
    card = _body(client)["cards"]["xiii.20-24"]
    assert card["found"] is True
    nara = ch13.nara_yantra_time(20.0, JD, 23.18)
    by_key = {t["instrument"]: t for t in card["instruments"]}
    assert set(by_key) == {"nara", "cakra", "dhanus", "yashti"}
    assert by_key["nara"]["ghatis_since_sunrise"] == pytest.approx(nara.ghatis_since_sunrise, abs=1e-3)
    for key in ("cakra", "dhanus", "yashti"):
        assert by_key[key]["ghatis_since_sunrise"] == pytest.approx(
            by_key["nara"]["ghatis_since_sunrise"], abs=5e-3)
        assert by_key[key]["source"] == "commentary"
    assert by_key["nara"]["source"] == "verse"
    assert card["clepsydra"]["day_ghatis"] == pytest.approx(ch13.clepsydra_day(JD, 23.18)["day_ghatis"])


def test_a_shadow_the_sun_never_casts_is_reported_not_raised(client: TestClient):
    """xiii.20-24: an impossible reading is a result, not an error.

    Expected: a 12-digit shadow in a January forenoon at Ujjain is shorter than
    the noon shadow, so the card says it was not found, with a reason, and the
    status is still 200.
    """
    card = _body(client, {**BODY, "shadow": 12.0})["cards"]["xiii.20-24"]
    assert card["found"] is False and card["reason"]
    assert "clepsydra" in card


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

    Expected: a pole latitude and a negative shadow are refused with 422.
    """
    assert client.post("/book/chapter/13", json={**BODY, "latitude": 90.0}).status_code == 422
    assert client.post("/book/chapter/13", json={**BODY, "shadow": -1.0}).status_code == 422
