"""Tests for the /book/chapter/4 verse-card payload.

These pin each card to ``ch04_lunar_eclipses`` so the React cards cannot
drift from the library. All run offline; the route must not touch the verse
corpus.
"""
from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch04_lunar_eclipses as ch04
from suryasiddhanta.api.book_ch04 import CARD_ORDER
from suryasiddhanta.api.main import app


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _find_month(want_eclipse: bool) -> tuple[int, int]:
    """First (year, month) from 2020 on whose full moon is / is not an eclipse."""
    for year in range(2020, 2027):
        for month in range(1, 13):
            if ch04.compute_lunar_eclipse(year, month, 15.0).is_eclipse == want_eclipse:
                return year, month
    raise AssertionError("no such month found in 2020-2026")


def _body(client: TestClient, year: int, month: int, day: float = 15.0) -> dict:
    """POST a date to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/4", json={"year": year, "month": month, "day": day})
    assert response.status_code == 200, response.text
    return response.json()


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all five cards, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER`` (five ids); every card has
    ``verses``, ``title``, ``does`` and ``date_dependent``.
    """
    body = _body(client, 2024, 3)
    assert body["order"] == CARD_ORDER
    assert len(CARD_ORDER) == 5
    for card_id in CARD_ORDER:
        for field in ("verses", "title", "does", "date_dependent"):
            assert field in body["cards"][card_id]


def test_diameter_and_shadow_cards_equal_the_library(client: TestClient):
    """iv.1-2 and iv.4-5 report the library's diameters and the suci shadow.

    Expected: apparent diameters equal the ``ch04`` functions at the payload's
    JD; the shadow built from 1600 - (6500-1600)*480/6500 yojanas over 15
    equals both ``earth_shadow_diameter`` and the catalogued figure.
    """
    body = _body(client, 2024, 3)
    jd = body["jd"]
    diameters = body["cards"]["iv.1-2"]
    assert diameters["sun_arcmin"] == pytest.approx(ch04.apparent_diameter_sun(jd))
    assert diameters["moon_arcmin"] == pytest.approx(ch04.apparent_diameter_moon(jd))

    shadow = body["cards"]["iv.4-5"]
    assert shadow["shadow_arcmin"] == pytest.approx(ch04.earth_shadow_diameter(jd))
    assert shadow["shadow_arcmin"] == pytest.approx(ch04.APPARENT_DIAMETER_ARCMIN["Shadow"])
    assert shadow["shadow_arcmin"] == pytest.approx(shadow["library_arcmin"])


def test_opposition_card_is_a_full_moon(client: TestClient):
    """iv.7-8 finds the full moon the library finds.

    Expected: the card's day equals ``find_full_moon`` for the same guess and
    the Moon is within 0.05 degree of 180 from the Sun.
    """
    year, month = 2024, 3
    card = _body(client, year, month)["cards"]["iv.7-8"]
    assert card["day"] == pytest.approx(ch04.find_full_moon(year, month, 15.0))
    assert card["elongation"] == pytest.approx(180.0, abs=0.05)


def test_eclipse_cards_equal_compute_lunar_eclipse_in_an_eclipse_month(client: TestClient):
    """iv.10-11 and iv.12-13 reproduce the library's eclipse, step by step.

    Expected: latitude, type, magnitude, half-duration and (if total) the
    half-time of totality equal ``compute_lunar_eclipse`` for the month.
    """
    year, month = _find_month(True)
    eclipse = ch04.compute_lunar_eclipse(year, month, 15.0)
    cards = _body(client, year, month)["cards"]

    obscuration = cards["iv.10-11"]
    assert obscuration["latitude"] == pytest.approx(eclipse.moon_latitude, abs=0.01)
    assert obscuration["eclipse_type"] == eclipse.eclipse_type
    assert obscuration["magnitude"] == pytest.approx(eclipse.magnitude, abs=1e-3)
    assert obscuration["obscured"] == pytest.approx(
        obscuration["half_sum"] - abs(obscuration["latitude"])
    )

    duration = cards["iv.12-13"]
    assert duration["half_duration_min"] == pytest.approx(eclipse.half_duration, abs=0.05)
    if eclipse.totality_half is None:
        assert duration["totality_half_min"] is None
    else:
        assert duration["totality_half_min"] == pytest.approx(eclipse.totality_half, abs=0.05)


def test_eclipse_cards_in_a_month_without_an_eclipse_say_none(client: TestClient):
    """A full moon outside the shadow zone is a verdict, not an error.

    Expected: HTTP 200, type "none", magnitude 0, and null durations.
    """
    year, month = _find_month(False)
    cards = _body(client, year, month)["cards"]
    assert cards["iv.10-11"]["eclipse_type"] == "none"
    assert cards["iv.10-11"]["magnitude"] == 0.0
    assert cards["iv.12-13"]["half_duration_min"] is None
    assert cards["iv.12-13"]["totality_half_min"] is None


def test_probe_applies_the_verses_formulas(client: TestClient):
    """The probe evaluates the verse geometry for any latitude.

    Expected: latitude 0 with the mean disks (32', 82.54') is total with
    magnitude (16 + 41.27 - 0) / 32; latitude 100' exceeds the half-sum 57.27'
    and gives "none" with no durations.
    """
    total = client.post(
        "/book/chapter/4/probe",
        json={"card": "iv.10-11", "moon_diameter": 32.0, "shadow_diameter": 82.5436, "latitude_arcmin": 0.0},
    ).json()
    assert total["eclipse_type"] == "total"
    assert total["magnitude"] == pytest.approx((16.0 + 41.2718) / 32.0)
    assert total["half_duration_min"] > total["totality_half_min"] > 0

    none = client.post(
        "/book/chapter/4/probe",
        json={"card": "iv.12-13", "moon_diameter": 32.0, "shadow_diameter": 82.5436, "latitude_arcmin": 100.0},
    ).json()
    assert none["eclipse_type"] == "none"
    assert none["half_duration_min"] is None


@pytest.mark.parametrize("year", [-3000, 4000])
def test_chapter_route_accepts_the_schemas_extreme_years(client: TestClient, year: int):
    """The bounds of the date schema are valid input, not errors.

    Expected: HTTP 200 and all five cards for both edge years.
    """
    assert len(_body(client, year, 6)["cards"]) == 5


def test_a_boundary_day_guess_that_crosses_the_month_still_answers(client: TestClient):
    """The day is only a starting guess, so the full moon may fall in the
    previous or next month.

    Expected: HTTP 200 for day 1.0 and day 31.9 of the same month, each with a
    finite JD.
    """
    for day in (1.0, 31.9):
        assert math.isfinite(_body(client, 2024, 3, day)["jd"])


def test_chapter_4_route_never_imports_the_corpus(client: TestClient):
    """The calculation route must work with no corpus present.

    Expected: ``book_ch04``'s own namespace holds no corpus module.
    """
    import suryasiddhanta.api.book_ch04 as module

    _body(client, 2024, 3)
    assert "retrieve" not in vars(module)
    assert "corpus" not in vars(module)


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/book/chapter/4", {"year": 5000, "month": 1}),
        ("/book/chapter/4", {"year": 2024, "month": 13}),
        ("/book/chapter/4/probe", {"card": "iv.99", "moon_diameter": 32, "shadow_diameter": 80, "latitude_arcmin": 0}),
        ("/book/chapter/4/probe", {"card": "iv.10-11", "moon_diameter": 32, "shadow_diameter": 80}),
        ("/book/chapter/4/probe", {"card": "iv.10-11", "moon_diameter": 32, "shadow_diameter": 80, "latitude_arcmin": 900}),
    ],
)
def test_invalid_input_is_refused(client: TestClient, path: str, payload: dict):
    """Out-of-range dates, an unknown card, a missing or out-of-range field.

    Expected: HTTP 422 for each.
    """
    assert client.post(path, json=payload).status_code == 422
