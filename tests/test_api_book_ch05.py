"""Tests for the /book/chapter/5 verse-card payload.

These pin each card to ``ch05_solar_eclipses`` so the React cards cannot
drift from the library. All run offline; the route must not touch the verse
corpus. June 2020 at Ujjain is a partial solar eclipse near noon in the SS
reckoning (``SOLAR`` below; the real one peaked about 12:10 IST); June 2024
is a new moon with no eclipse at Ujjain.
"""
from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch03_direction_place_time as ch03
from suryasiddhanta import ch05_solar_eclipses as ch05
from suryasiddhanta.api.book_ch05 import CARD_ORDER, lambana_verse, madhyalagna, nati_verse
from suryasiddhanta.api.main import app

UJJAIN = {"latitude": 23.18, "longitude": 75.78}
SOLAR = {"year": 2020, "month": 6, "day": 15.0, **UJJAIN}
NO_ECLIPSE = {"year": 2024, "month": 6, "day": 1.0, **UJJAIN}


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/5", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _solar_jd() -> float:
    """Julian Day of the June 2020 new moon, as the route finds it."""
    return ch01.julian_day(2020, 6, ch05.find_new_moon(2020, 6, 15.0))


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all seven cards, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER``; every card has ``verses``,
    ``title``, ``does`` and ``date_dependent``.
    """
    body = _body(client, SOLAR)
    assert body["order"] == CARD_ORDER
    assert len(CARD_ORDER) == 7
    for card_id in CARD_ORDER:
        for field in ("verses", "title", "does", "date_dependent"):
            assert field in body["cards"][card_id]


def test_madhyalagna_has_the_local_sidereal_time_as_its_right_ascension():
    """The meridian ecliptic-point is the ecliptic point on the meridian.

    Expected: for any sidereal time, the right ascension of the returned
    longitude equals that time.
    """
    for lst in (0.0, 37.0, 91.0, 179.0, 200.0, 271.0, 359.0):
        assert ch03.right_ascension(madhyalagna(lst)) == pytest.approx(lst, abs=1e-6)


def test_drkksepa_card_matches_the_library_nonagesimal(client: TestClient):
    """v.5-7: the verse's drkksepa and the library's agree at low drkksepa.

    Expected: ``drkksepa_library`` equals ``ch05.nonagesimal``'s drkksepa and
    the plane-triangle verse figure is within half a degree of it.
    """
    card = _body(client, SOLAR)["cards"]["v.5-7"]
    lst = ch03.local_sidereal_time(_solar_jd(), UJJAIN["longitude"])
    _, drk = ch05.nonagesimal(lst, UJJAIN["latitude"])
    assert card["drkksepa_library"] == pytest.approx(drk)
    assert abs(card["drkksepa_gap"]) < 0.5
    assert card["drggati"] == pytest.approx(math.cos(math.radians(drk)))


def test_lambana_card_agrees_with_the_library_in_sign_and_size(client: TestClient):
    """v.8-9: the verse's lambana, applied as the verse says, tracks the library's.

    Expected: ``library_arcmin`` equals ``ch05.lambana_correction``; the
    verse figure has the same sign and is within 2' of it; ``rule`` is
    ``subtract`` exactly when the interval is positive.
    """
    card = _body(client, SOLAR)["cards"]["v.8-9"]
    expected = ch05.lambana_correction(_solar_jd(), UJJAIN["latitude"], UJJAIN["longitude"])
    assert card["library_arcmin"] == pytest.approx(expected)
    assert card["verse_arcmin"] * expected > 0
    assert card["verse_arcmin"] == pytest.approx(expected, abs=2.0)
    assert (card["rule"] == "subtract") == (card["interval"] > 0)


def test_nati_card_matches_the_library(client: TestClient):
    """v.10-12: 49' x sin(drkksepa) and the library nati agree.

    Expected: ``library_arcmin`` equals ``ch05.nati_correction``; the verse
    magnitude is within 1' of it; the corrected latitude is the Moon's plus
    the nati, to the 0.01' the stored ``SolarEclipse.moon_latitude`` keeps.
    """
    card = _body(client, SOLAR)["cards"]["v.10-12"]
    expected = ch05.nati_correction(_solar_jd(), UJJAIN["latitude"], UJJAIN["longitude"])
    assert card["library_arcmin"] == pytest.approx(expected)
    assert card["verse_arcmin"] == pytest.approx(abs(expected), abs=1.0)
    assert card["corrected_latitude"] == pytest.approx(card["moon_latitude"] + expected, abs=0.006)


def test_nati_shortcut_forms_agree(client: TestClient):
    """v.11 gives two forms of the same figure: sin/70 and sin x 49/R.

    Expected: they differ by under 0.5' at a drkksepa of 40 degrees.
    """
    r = client.post("/book/chapter/5/probe", json={"card": "v.10-12", "drkksepa": 40.0}).json()
    assert r["shortcut_arcmin"] == pytest.approx(r["verse_arcmin"], abs=0.5)


def test_result_card_equals_the_topocentric_eclipse(client: TestClient):
    """v.13: the card reports exactly what ``compute_solar_eclipse_topocentric`` returns.

    Expected: type, magnitude, half-duration, lambana and nati equal the
    library's for the same new moon and place.
    """
    card = _body(client, SOLAR)["cards"]["v.13"]
    day = ch05.find_new_moon(2020, 6, 15.0)
    ecl = ch05.compute_solar_eclipse_topocentric(
        2020, 6, day, UJJAIN["latitude"], UJJAIN["longitude"])
    assert card["is_eclipse"] is True
    assert card["eclipse_type"] == ecl.eclipse_type
    assert card["magnitude"] == pytest.approx(ecl.magnitude)
    assert card["half_duration_min"] == pytest.approx(ecl.half_duration)
    assert card["lambana"] == pytest.approx(ecl.lambana)
    assert card["nati"] == pytest.approx(ecl.nati)


def test_contact_card_adjusts_half_durations_by_the_parallax_change(client: TestClient):
    """v.15-17: each half-duration moves by the change of lambana, over the speed.

    Expected: the two adjustments sum to the change of lambana between
    contact and separation over the relative speed, and each corrected
    half-duration is the library's plus its adjustment.
    """
    card = _body(client, SOLAR)["cards"]["v.15-17"]
    speed = card["speed_arcmin_per_min"]
    total = card["contact_adjust_min"] + card["separation_adjust_min"]
    assert total == pytest.approx(
        (card["lambana_separation"] - card["lambana_contact"]) / speed)
    assert card["contact_half_min"] == pytest.approx(
        card["half_duration_min"] + card["contact_adjust_min"])
    assert card["separation_half_min"] == pytest.approx(
        card["half_duration_min"] + card["separation_adjust_min"])


def test_no_eclipse_month_still_answers_every_card(client: TestClient):
    """A new moon with no eclipse at the place leaves the parallax cards intact.

    Expected: v.13 says no eclipse and v.15-17 says so too; the parallax
    cards still carry numbers.
    """
    cards = _body(client, NO_ECLIPSE)["cards"]
    assert cards["v.13"]["is_eclipse"] is False
    assert cards["v.15-17"]["is_eclipse"] is False
    assert "contact_half_min" not in cards["v.15-17"]
    assert isinstance(cards["v.8-9"]["library_arcmin"], float)


def test_probe_matches_the_verse_formulas(client: TestClient):
    """The sliders use the same formulas as the cards.

    Expected: v.8-9 returns -4 cos(drk) sin(interval) ghatis; v.10-12 returns
    49 sin(drk) and the library's -48.76 sin(drk).
    """
    r = client.post("/book/chapter/5/probe",
                    json={"card": "v.8-9", "drkksepa": 20.0, "interval": 30.0})
    assert r.status_code == 200
    assert r.json()["verse_ghatis"] == pytest.approx(
        -4 * math.cos(math.radians(20)) * math.sin(math.radians(30)))
    assert r.json()["verse_ghatis"] == pytest.approx(lambana_verse(30.0, 20.0))
    r = client.post("/book/chapter/5/probe", json={"card": "v.10-12", "drkksepa": 20.0})
    assert r.json()["verse_arcmin"] == pytest.approx(nati_verse(20.0))
    assert r.json()["library_arcmin"] == pytest.approx(
        -ch05.PARALLAX_DIFF_ARCMIN * math.sin(math.radians(20)))


def test_probe_rejects_missing_inputs(client: TestClient):
    """A probe without the input its card needs is refused, not guessed.

    Expected: 422 for no drkksepa, and for v.8-9 without an interval.
    """
    assert client.post("/book/chapter/5/probe", json={"card": "v.10-12"}).status_code == 422
    assert client.post("/book/chapter/5/probe",
                       json={"card": "v.8-9", "drkksepa": 5.0}).status_code == 422


def test_out_of_range_inputs_are_rejected(client: TestClient):
    """The schema bounds the date and the place.

    Expected: 422 for latitude 80, month 13 and a year past 4000.
    """
    for bad in ({**SOLAR, "latitude": 80.0}, {**SOLAR, "month": 13}, {**SOLAR, "year": 5000}):
        assert client.post("/book/chapter/5", json=bad).status_code == 422
