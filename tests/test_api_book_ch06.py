"""Tests for the /book/chapter/6 projection payload.

Lengths are pinned to ``ch06_eclipse_projection`` / ``ch04`` / ``ch05``; the
signs are pinned to the verses (v.4 contact side, v.8 latitude direction)
and the corrected library geometry. All run offline.
December 2019 at Ujjain is a partial solar eclipse and March 2026 a total
lunar one.
"""
from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch04_lunar_eclipses as ch04
from suryasiddhanta import ch06_eclipse_projection as ch06
from suryasiddhanta.api.book_ch06 import CARD_ORDER, contact_sign, path_point
from suryasiddhanta.api.main import app

UJJAIN = {"latitude": 23.18, "longitude": 75.78}
SOLAR = {"kind": "solar", "year": 2019, "month": 12, "day": 20.0, **UJJAIN}
LUNAR = {"kind": "lunar", "year": 2026, "month": 3, "day": 15.0, **UJJAIN}


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _cards(client: TestClient, payload: dict) -> dict:
    """POST to the chapter route and return its cards."""
    response = client.post("/book/chapter/6", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["cards"]


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all eight cards with the fields the page needs.

    Expected: all ``CARD_ORDER`` ids, each with verses, title, does, date_dependent.
    """
    cards = _cards(client, LUNAR)
    assert list(cards) == CARD_ORDER
    for card in cards.values():
        for field in ("verses", "title", "does", "date_dependent"):
            assert field in card


def test_lunar_chord_and_valana_equal_the_library(client: TestClient):
    """vi.14-16 / vi.4-9: lengths and valana are the library's.

    Expected: half chord equals the library's path half-length within its
    0.01' rounding; valana equals ``eclipse_contact_points``' valana.
    """
    cards = _cards(client, LUNAR)
    ecl = ch04.compute_lunar_eclipse(2026, 3, 15.0)
    path = ch06.project_eclipse_path(ecl)
    assert cards["vi.14-16"]["chord_half"] == pytest.approx(abs(path[-1][0]), abs=0.01)
    contacts = ch06.eclipse_contact_points(ecl, UJJAIN["latitude"], UJJAIN["longitude"])
    assert cards["vi.4-9"]["valana"] == pytest.approx(contacts["valana"], abs=0.01)


def test_lunar_signs_follow_the_verses(client: TestClient):
    """v.4 and v.8: a lunar eclipse begins on the east with the latitude reversed.

    Expected: contact limb east; the eclipser's contact point has positive x;
    its y is minus the Moon's latitude; the separation is the mirror image.
    """
    cards = _cards(client, LUNAR)
    g = cards["vi.14-16"]
    assert cards["vi.4-9"]["contact_limb"] == "east"
    assert g["contact"][0] > 0 > g["separation"][0]
    assert g["contact"][1] == pytest.approx(-g["latitude"])
    assert g["separation"][1] == pytest.approx(g["contact"][1])


def test_solar_signs_follow_the_verses(client: TestClient):
    """v.4 and v.8: a solar eclipse begins on the west with the latitude as it is.

    Expected: contact limb west; contact x negative; y equals the latitude.
    """
    cards = _cards(client, SOLAR)
    g = cards["vi.14-16"]
    assert cards["vi.4-9"]["contact_limb"] == "west"
    assert g["contact"][0] < 0 < g["separation"][0]
    assert g["contact"][1] == pytest.approx(g["latitude"])


def test_contact_valana_is_the_reverse_of_separation(client: TestClient):
    """v.5: the two valanas are equal and opposite, flipped between lunar and solar.

    Expected: separation = -contact; lunar contact valana = valana, solar = -valana.
    """
    for payload, sign in ((LUNAR, 1), (SOLAR, -1)):
        card = _cards(client, payload)["vi.4-9"]
        assert card["separation_valana"] == pytest.approx(-card["contact_valana"])
        assert card["contact_valana"] == pytest.approx(sign * card["valana"])


def test_stick_meets_the_path_at_the_stated_distance(client: TestClient):
    """v.17-19: the point found is exactly one stick from the centre.

    Expected: hypot(point) equals half the sum less the obscuration, for both
    ends of the path.
    """
    card = _cards(client, LUNAR)["vi.17-19"]
    assert card["reaches_path"] is True
    for key in ("contact_point", "separation_point"):
        assert math.hypot(*card[key]) == pytest.approx(card["stick"])


def test_immersion_stick_is_half_the_difference(client: TestClient):
    """v.20-22: a total lunar eclipse has immersion at half the difference of the disks.

    Expected: stick = shadow radius - Moon radius; the point lies that far out.
    """
    card = _cards(client, LUNAR)["vi.20-22"]
    assert card["has_immersion"] is True
    assert card["stick"] == pytest.approx(card["eclipser_radius"] - card["eclipsed_radius"])
    assert math.hypot(*card["contact_point"]) == pytest.approx(card["stick"], abs=1e-9)


def test_partial_solar_has_no_immersion(client: TestClient):
    """A partial eclipse has no immersion: the half-difference stick cannot reach the path.

    Expected: ``has_immersion`` false and no points.
    """
    card = _cards(client, SOLAR)["vi.20-22"]
    assert card["has_immersion"] is False
    assert card["contact_point"] is None


def test_visibility_thresholds(client: TestClient):
    """v.13: a twelfth of the Moon's disk, or three minutes of the Sun's.

    Expected: lunar threshold = moon diameter / 12; solar threshold = 3'.
    """
    cards = _cards(client, LUNAR)
    assert cards["vi.13"]["threshold"] == pytest.approx(
        2 * cards["vi.2"]["eclipsed_radius"] / 12)
    assert _cards(client, SOLAR)["vi.13"]["threshold"] == 3.0
    assert cards["vi.13"]["visible"]


def test_colours_follow_the_phase(client: TestClient):
    """v.23: total lunar is tawny, a more-than-half partial is black.

    Expected: lunar March 2026 tawny; solar December 2019 (magnitude 0.78) black.
    """
    assert _cards(client, LUNAR)["vi.23"]["at_maximum"].startswith("tawny")
    assert _cards(client, SOLAR)["vi.23"]["at_maximum"] == "black"


def test_path_point_helpers():
    """The sign helpers encode v.4 and v.8.

    Expected: lunar contact +x, solar contact -x; lunar y reversed.
    """
    assert contact_sign("lunar") == 1 and contact_sign("solar") == -1
    assert path_point("lunar", 5.0, 10.0, True) == (10.0, -5.0)
    assert path_point("solar", 5.0, 10.0, True) == (-10.0, 5.0)
    assert path_point("solar", 5.0, 10.0, False) == (10.0, 5.0)


def test_probe_lays_the_stick(client: TestClient):
    """The probe returns the point one stick from the centre on the path.

    Expected: stick 35 at latitude 10 puts the point on the path (y = -10 for
    lunar) at distance 35 from the centre along the stick; a stick shorter
    than the latitude does not reach the path.
    """
    base = {"card": "vi.17-19", "kind": "lunar", "eclipsed_radius": 15.0,
            "eclipser_radius": 40.0, "latitude_arcmin": 10.0}
    r = client.post("/book/chapter/6/probe", json={**base, "obscured": 20.0}).json()
    assert r["stick"] == pytest.approx(35.0)
    assert math.hypot(*r["point"]) == pytest.approx(35.0)
    assert r["point"][1] == pytest.approx(-10.0)
    r = client.post("/book/chapter/6/probe", json={**base, "obscured": 50.0}).json()
    assert r["reaches_path"] is False and r["point"] is None


def test_out_of_range_inputs_are_rejected(client: TestClient):
    """The schema bounds the kind, the date and the place.

    Expected: 422 for kind 'both', latitude 80 and month 0.
    """
    for bad in ({**LUNAR, "kind": "both"}, {**LUNAR, "latitude": 80.0}, {**LUNAR, "month": 0}):
        assert client.post("/book/chapter/6", json=bad).status_code == 422
