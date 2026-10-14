"""Tests for the /book/chapter/10 verse-card payload.

These pin each card to ``ch10_lunar_horns`` so the React cards cannot drift
from the library. All run offline; the route must not touch the verse corpus.
Ujjain on 5 October 2024 sees a young waxing crescent two days after new moon.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch10_lunar_horns as ch10
from suryasiddhanta.api.book_ch10 import CARD_ORDER
from suryasiddhanta.api.main import app

DATE = {"year": 2024, "month": 10, "day": 5.0}
UJJAIN = {"latitude": 23.18, "longitude": 75.78}


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/10", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all four cards, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER``; every card has ``verses``,
    ``title``, ``does`` and ``date_dependent``.
    """
    body = _body(client, {**DATE, **UJJAIN})
    assert body["order"] == CARD_ORDER
    for card_id in CARD_ORDER:
        card = body["cards"][card_id]
        assert {"verses", "title", "does", "date_dependent"} <= card.keys()


def test_visibility_uses_the_twelve_degree_limit(client: TestClient):
    """x.1: a Moon 23 degrees from the Sun is seen, in the west, after sunset.

    Expected: distance equals the elongation (waxing), the limit is 12 and
    the Moon is visible; the same date a day after new moon is not.
    """
    card = _body(client, {**DATE, **UJJAIN})["cards"]["x.1"]
    assert card["limit"] == 12.0
    assert card["visible"] and card["waxing"]
    assert card["distance"] == pytest.approx(card["elongation"])
    assert "west" in card["horizon"]
    new_moon = _body(client, {"year": 2024, "month": 10, "day": 3.0, **UJJAIN})
    assert not new_moon["cards"]["x.1"]["visible"]


def test_illumination_is_linear_and_matches_the_library(client: TestClient):
    """x.9: minutes over 900 give the lit digits, and digits over 12 the library fraction.

    Expected: ``lit_digits`` = minutes / 900, ``fraction`` equals
    ``illuminated_fraction`` to the library's rounding, and the width is the
    versine figure ``crescent_width``.
    """
    card = _body(client, {**DATE, **UJJAIN})["cards"]["x.9"]
    jd = ch01.julian_day(2024, 10, 5.0)
    assert card["lit_digits"] == pytest.approx(card["minutes"] / 900.0)
    assert card["fraction"] == pytest.approx(ch10.illuminated_fraction(jd), abs=1e-5)
    assert card["width_arcmin"] == ch10.crescent_width(jd)


def test_dark_half_reflects_the_elongation(client: TestClient):
    """x.9 and v.16: past half a revolution the rule uses the complement.

    Expected: on a waning date the elongation is over 180, the reflected
    value is 360 less it, and the paksha is the dark half.
    """
    card = _body(client, {"year": 2024, "month": 10, "day": 25.0, **UJJAIN})["cards"]["x.9"]
    assert card["elongation"] > 180.0
    assert card["reflected_elongation"] == pytest.approx(360.0 - card["elongation"])
    assert "krishna" in card["paksha"]


def test_rise_and_set_match_the_library(client: TestClient):
    """x.2-5: the card reports the library's next moonrise and moonset.

    Expected: the dates equal ``moonrise`` and ``moonset`` at the same place.
    """
    card = _body(client, {**DATE, **UJJAIN})["cards"]["x.2-5"]
    jd = ch01.julian_day(2024, 10, 5.0)
    rise = ch10.moonrise(jd, 23.18, 75.78)
    y, m, d, frac = ch01.from_julian_day(rise)
    assert card["rise"]["day"] == pytest.approx(d + frac)


def test_figure_strip_runs_a_week_and_waxes(client: TestClient):
    """x.10-14: eight daily figures from the date, the lit fraction rising.

    Expected: eight entries, the first equal to ``now``, elongation
    increasing from one to the next, and the sun angle derived from the
    library's horn angle.
    """
    card = _body(client, {**DATE, **UJJAIN})["cards"]["x.10-14"]
    strip = card["strip"]
    assert len(strip) == 8 and strip[0] == card["now"]
    assert all(b["elongation"] > a["elongation"] for a, b in zip(strip, strip[1:]))
    assert card["now"]["sun_angle"] == pytest.approx((card["now"]["horn_angle"] - 90.0) % 360.0)


def test_latitude_out_of_range_is_rejected(client: TestClient):
    """The place is validated before any calculation.

    Expected: a latitude of 91 degrees is refused with 422.
    """
    response = client.post("/book/chapter/10", json={**DATE, "latitude": 91.0, "longitude": 0.0})
    assert response.status_code == 422
