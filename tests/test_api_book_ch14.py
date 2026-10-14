"""Tests for the /book/chapter/14 verse-card payload.

These pin each card to ``ch14_reckoning_time`` so the React cards cannot drift
from the library. All run offline; the route must not touch the verse corpus.
The default is 1 January 2024, converting one year of the gods into civil days.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch14_reckoning_time as ch14
from suryasiddhanta.api.book_ch14 import CARD_ORDER
from suryasiddhanta.api.main import app

BODY = {"year": 2024, "month": 1, "day": 1.0, "value": 1.0,
        "from_mana": "daiva", "to_mana": "savana", "heliacal": False}
JD = ch01.julian_day(2024, 1, 1.0)


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict = BODY) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/14", json=payload)
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


def test_nine_manas_card(client: TestClient):
    """xiv.1-2: nine modes in verse order, four flagged practical, each with a reading.

    Expected: the library's keys in order and a count for each.
    """
    card = _body(client)["cards"]["xiv.1-2"]
    assert [m["key"] for m in card["manas"]] == [m.key for m in ch14.manas()]
    assert sum(1 for m in card["manas"] if m["practical"]) == 4
    assert all("count" in m and "description" in m for m in card["manas"])


def test_shadasitimukha_card(client: TestClient):
    """xiv.4-6: the four marks, the Virgo remainder, and Burgess's caveat.

    Expected: longitudes 266, 352, 78, 164; arcs summing to 360; a note that
    the purpose is not in the text.
    """
    card = _body(client)["cards"]["xiv.4-6"]
    assert [m["longitude"] for m in card["marks"][:4]] == [266, 352, 78, 164]
    assert sum(m["arc_degrees"] for m in card["marks"]) == 360
    assert "purpose" in card["note"].lower() or "explanation" in card["note"].lower()
    assert card["marks"][0]["date"]["year"] in (2024, 2025)


def test_sankranti_card(client: TestClient):
    """xiv.7-11: twelve sankrantis with punyakala, two ayanas, two visuvats, six ritus.

    Expected: counts match the library and the Mesha entry is in April 2024.
    """
    card = _body(client)["cards"]["xiv.7-11"]
    assert len(card["sankrantis"]) == 12 and len(card["ritus"]) == 6
    first = card["sankrantis"][0]
    assert first["sign"] == "Mesha" and first["date"]["month"] == 4
    assert first["punyakala_total_nadis"] == pytest.approx(33.0, abs=1.5)
    assert card["ayanas"]["dakshinayana"]["sign"] == "Karka"
    assert card["visuvats"]["autumnal"]["sign"] == "Tula"


def test_fathers_clock_card(client: TestClient):
    """xiv.12-14: the tithi and the Fathers' hour for the moment.

    Expected: the hour matches the library and the next noon lies ahead.
    """
    card = _body(client)["cards"]["xiv.12-14"]
    clock = ch14.pitrya_clock(JD)
    assert card["hour"] == pytest.approx(clock.hour)
    assert card["tithi"] == clock.tithi and card["tithi_name"]
    assert card["next_noon"]["year"] >= 2024


def test_month_asterism_card(client: TestClient):
    """xiv.15-16: the table, and the Moon's asterism with its month.

    Expected: twelve months, 27 asterisms, and the Moon's month matches the table.
    """
    card = _body(client)["cards"]["xiv.15-16"]
    assert len(card["months"]) == 12
    assert sum(len(m["asterisms"]) for m in card["months"]) == 27
    assert ch14.asterism_month(card["moon_asterism"]) == card["moon_month"]


def test_jupiter_card_mean_and_optional_heliacal(client: TestClient):
    """xiv.17: the mean-method year, twelve cycle years, heliacal only on request.

    Expected: mean matches the library with source commentary; no heliacal
    by default, commentary-sourced when asked; the cycle advances sum to 12.
    """
    card = _body(client)["cards"]["xiv.17"]
    assert card["mean"]["name"] == ch14.barhaspatya_year(JD).name
    assert card["mean"]["source"] == "commentary" and card["heliacal"] is None
    assert len(card["cycle"]) == 12 and sum(y["advance"] for y in card["cycle"]) == 12
    asked = _body(client, {**BODY, "heliacal": True})["cards"]["xiv.17"]
    assert asked["heliacal"]["source"] == "commentary"


def test_converter_and_structure_card(client: TestClient):
    """xiv.18-21: the conversion, the unit table and the kalpa's structure.

    Expected: one year of the gods is a sidereal year of civil days; fourteen
    manvantaras and fifteen sandhis sum to a kalpa.
    """
    card = _body(client)["cards"]["xiv.18-21"]
    assert card["result"] == pytest.approx(ch14.convert(1.0, "daiva", "savana"))
    assert len(card["units"]) == 9
    s = card["structure"]
    assert s["manvantaras"] == 14 and s["sandhis"] == 15
    assert s["total_years"] == ch01.KALPA


def test_date_independent_cards_ignore_the_date(client: TestClient):
    """``date_dependent`` is honest: changing the date leaves those cards unchanged.

    Expected: cards flagged False are identical for two different years.
    """
    a = _body(client)
    b = _body(client, {**BODY, "year": 1500})
    for card_id in CARD_ORDER:
        if not a["cards"][card_id]["date_dependent"]:
            assert a["cards"][card_id] == b["cards"][card_id]


def test_old_dates_still_compute(client: TestClient):
    """The library's point is that old dates work. Expected: 200 for 500 BCE."""
    _body(client, {**BODY, "year": -500})


def test_bad_inputs_are_rejected(client: TestClient):
    """Inputs are validated before any calculation.

    Expected: an unknown mana and a day of 32 are refused with 422.
    """
    assert client.post("/book/chapter/14", json={**BODY, "from_mana": "nope"}).status_code == 422
    assert client.post("/book/chapter/14", json={**BODY, "day": 32.0}).status_code == 422
