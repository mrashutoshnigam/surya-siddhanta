"""Tests for the /book/chapter/7 verse-card payload.

These pin each card to ``ch07_conjunctions`` / ``ch02_true_places`` so the
React cards cannot drift from the library. All run offline; the route must
not touch the verse corpus. Mars and Venus draw together in February 2024
(``PAIR`` below); Jupiter and Saturn meet in early 2020.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch02_true_places as ch02
from suryasiddhanta import ch07_conjunctions as ch07
from suryasiddhanta.api.book_ch07 import CARD_ORDER, daily_motion, separating
from suryasiddhanta.api.main import app

PAIR = {"planet1": "Mars", "planet2": "Venus", "year": 2024, "month": 2, "day": 1.0}


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, payload: dict) -> dict:
    """POST to the chapter route and return the whole response body."""
    response = client.post("/book/chapter/7", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all five cards, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER``; every card has ``verses``,
    ``title``, ``does`` and ``date_dependent``.
    """
    body = _body(client, PAIR)
    assert body["order"] == CARD_ORDER
    assert len(CARD_ORDER) == 5
    for card_id in CARD_ORDER:
        for field in ("verses", "title", "does", "date_dependent"):
            assert field in body["cards"][card_id]


def test_separating_is_the_verse_rule():
    """v.2-3: the conjunction is past when the gap and the relative speed agree in sign.

    Expected: a faster body ahead is past; behind is to come; a retrograde
    body reverses it; both direct and both retrograde follow the same sign rule.
    """
    assert separating(5.0, 0.5) is True        # swifter ahead: past
    assert separating(-5.0, 0.5) is False      # swifter behind: to come
    assert separating(5.0, -0.5) is False      # slower ahead: drawing together
    assert separating(-5.0, -0.5) is True


def test_who_meets_whom(client: TestClient):
    """v.1: two star-planets may fight; the Sun and Moon never do.

    Expected: Mars-Venus is ``both_taragraha``; Mars-Moon and Mars-Sun are not.
    """
    assert _body(client, PAIR)["cards"]["vii.1"]["both_taragraha"] is True
    moon = _body(client, {**PAIR, "planet2": "Moon", "search_days": 60.0})["cards"]["vii.1"]
    sun = _body(client, {**PAIR, "planet2": "Sun"})["cards"]["vii.1"]
    assert moon["both_taragraha"] is False and "Moon" in moon["relation"]
    assert sun["both_taragraha"] is False and "set" in sun["relation"]


def test_direction_card_matches_the_library_motions(client: TestClient):
    """v.2-3: the gap and motions are the library's, and the status follows them.

    Expected: motions equal ``daily_motion``; gap equals ``longitude_difference``;
    before the February 2024 conjunction the status is ``to come``.
    """
    card = _body(client, PAIR)["cards"]["vii.2-3"]
    jd = ch01.julian_day(2024, 2, 1.0)
    assert card["motion1"] == pytest.approx(daily_motion("Mars", jd))
    assert card["gap"] == pytest.approx(ch07.longitude_difference(
        ch07._planet_lon("Mars", jd), ch07._planet_lon("Venus", jd)))
    assert card["status"] == "to come"
    after = _body(client, {**PAIR, "day": 25.0})["cards"]["vii.2-3"]
    assert after["status"] == "past"


def test_correction_steps_settle_on_the_library_conjunction(client: TestClient):
    """v.4-6: repeating the correction converges to the bisected conjunction.

    Expected: the steps shrink to under 0.001 day, the first one adds (the
    conjunction is to come), and the settled time is within 0.05 day of
    ``nearest_conjunction``.
    """
    card = _body(client, PAIR)["cards"]["vii.4-6"]
    steps = card["steps"]
    assert steps[0]["rule"] == "add"
    assert abs(steps[-1]["move_days"]) < 1e-3
    assert abs(steps[0]["move_days"]) > abs(steps[-1]["move_days"])
    jd = ch01.julian_day(2024, 2, 1.0)
    conj = ch07.nearest_conjunction("Mars", "Venus", jd)
    assert card["library_jd"] == pytest.approx(conj.jd)
    assert card["final_jd"] == pytest.approx(conj.jd, abs=0.05)
    assert card["agrees"] is True


def test_move_in_ghatis_is_sixty_a_day(client: TestClient):
    """v.4: the correction in nadis is the days moved times sixty.

    Expected: ``move_ghatis`` equals ``move_days`` x 60 on every step.
    """
    for step in _body(client, PAIR)["cards"]["vii.4-6"]["steps"]:
        assert step["move_ghatis"] == pytest.approx(step["move_days"] * 60.0)


def test_latitude_card_uses_the_library_latitudes(client: TestClient):
    """v.12: the two latitudes are ``planet_latitude`` at the conjunction.

    Expected: they equal the library's; opposite directions add, same
    directions subtract; the verse gap is within 0.1' of the library separation.
    """
    card = _body(client, PAIR)["cards"]["vii.12"]
    assert card["found"] is True
    assert card["latitude1"] == pytest.approx(ch02.planet_latitude("Mars", card["jd"]))
    assert card["latitude2"] == pytest.approx(ch02.planet_latitude("Venus", card["jd"]))
    expect = (abs(abs(card["latitude1"]) - abs(card["latitude2"])) if card["same_direction"]
              else abs(card["latitude1"]) + abs(card["latitude2"]))
    assert card["verse_gap"] == pytest.approx(expect)
    assert card["verse_gap"] == pytest.approx(card["library_separation_arcmin"], abs=0.1)


def test_classification_names_the_northern_planet_victor(client: TestClient):
    """v.19-22: within a degree two star-planets are in yuddha, the northern one wins.

    Expected: Mars-Venus in February 2024 is yuddha at under 1 degree; the
    winner is Venus, the planet of greater latitude.
    """
    card = _body(client, PAIR)["cards"]["vii.19-22"]
    assert card["type"] == "yuddha"
    assert card["separation_deg"] < card["limit_deg"]
    assert card["winner"] == "Venus" == card["north_planet"]
    assert card["latitude2"] > card["latitude1"]


def test_no_conjunction_in_the_window_is_reported_not_raised(client: TestClient):
    """A pair with no conjunction in the window leaves the dependent cards saying so.

    Expected: Jupiter-Saturn within 30 days of mid-2024 finds none; the
    conjunction cards carry ``found`` false and the step card has no library answer.
    """
    body = _body(client, {"planet1": "Jupiter", "planet2": "Saturn", "year": 2024,
                          "month": 6, "day": 1.0, "search_days": 30.0})
    assert body["cards"]["vii.12"]["found"] is False
    assert body["cards"]["vii.19-22"]["found"] is False
    assert body["cards"]["vii.4-6"]["library_jd"] is None


def test_same_body_twice_is_refused(client: TestClient):
    """A body cannot meet itself.

    Expected: 400 for Mars with Mars.
    """
    r = client.post("/book/chapter/7", json={**PAIR, "planet2": "Mars"})
    assert r.status_code == 400


def test_out_of_range_inputs_are_rejected(client: TestClient):
    """The schema bounds the bodies, the date and the search window.

    Expected: 422 for an unknown body, month 13 and a 5000-day window.
    """
    for bad in ({**PAIR, "planet1": "Pluto"}, {**PAIR, "month": 13},
                {**PAIR, "search_days": 5000.0}):
        assert client.post("/book/chapter/7", json=bad).status_code == 422
