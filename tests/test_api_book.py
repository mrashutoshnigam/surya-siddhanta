"""Tests for the /book/chapter/1 verse-card payload.

These pin the card payload to the library's own figures. The point is that
the React cards cannot drift away from ``ch01_mean_motions``: every number
the page shows either appears here as an equality against the module, or
is derived in the browser from a constant that does.

All of them run offline. The route must not touch the verse corpus, which
lives outside the repository -- one test asserts exactly that.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta.api.book import CARD_ORDER
from suryasiddhanta.api.main import app


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _cards(client: TestClient, year: int, month: int = 1, day: float = 1.0) -> dict:
    """POST a date to the route and return its ``cards`` mapping."""
    response = client.post(
        "/book/chapter/1", json={"year": year, "month": month, "day": day}
    )
    assert response.status_code == 200, response.text
    return response.json()["cards"]


def test_every_card_is_present_and_in_verse_order(client: TestClient):
    """The route returns all twelve cards, in the chapter's own order.

    Expected: ``order`` equals CARD_ORDER, every id in it has a card, and
    each card carries the chrome the React VerseCard renders.
    """
    body = client.post("/book/chapter/1", json={"year": 2024, "month": 4, "day": 9}).json()

    assert body["order"] == CARD_ORDER
    assert set(body["cards"]) == set(CARD_ORDER)
    for card_id in CARD_ORDER:
        card = body["cards"][card_id]
        assert card["id"] == card_id
        assert card["verses"]
        assert card["title"]
        assert card["does"]
        assert isinstance(card["date_dependent"], bool)


def test_bhagana_card_reproduces_the_library_table_exactly(client: TestClient):
    """i.29-34 states the revolution counts, unrounded and unrederived.

    Expected: every row equals ``ch01.BHAGANA`` and ``MEAN_DAILY_MOTION``
    for that body, so the card cannot introduce a figure of its own.
    """
    card = _cards(client, 2024, 4, 9)["i.29-34"]

    rows = {row["body"]: row for row in card["rows"]}
    assert set(rows) == set(ch01.BHAGANA)
    for body, revolutions in ch01.BHAGANA.items():
        assert rows[body]["revolutions"] == revolutions
        assert rows[body]["daily_motion_deg"] == pytest.approx(
            ch01.MEAN_DAILY_MOTION[body]
        )
    assert card["civil_days_per_mahayuga"] == ch01.CIVIL_DAYS_PER_MAHAYUGA


def test_epoch_card_matches_burgess_worked_example_for_1860(client: TestClient):
    """i.23-24 on Jan 1, 1860 gives Burgess's own ahargana and era year.

    Expected: 1,811,945 days since the Kali epoch, falling in Kali year
    4961 -- the example the library's own verse-route test is pinned to.
    """
    card = _cards(client, 1860, 1, 1)["i.23-24"]

    assert card["ahargana"] == 1_811_945
    assert card["kali_era_year"] == 4961
    assert card["kali_epoch_jd"] == ch01.KALI_EPOCH_JD


def test_ahargana_route_card_reaches_the_same_day_count(client: TestClient):
    """i.48-51 runs the text's route and compares it with plain subtraction.

    Expected: for Jan 1, 1860 the derived triple is Burgess's (4960 y.,
    9 m., 7 d.), the route returns the same civil days as ``ahargana``,
    and the card reports no difference between the two.
    """
    card = _cards(client, 1860, 1, 1)["i.48-51"]

    assert card["input"] == {"years": 4960, "months": 9, "tithis": 7}
    assert card["route"]["civil_days"] == card["direct_ahargana"] == 1_811_945
    assert card["difference_days"] == 0
    assert card["adhimasa_per_mahayuga"] == ch01.ADHIMASA_PER_MAHAYUGA
    assert card["tithikshaya_per_mahayuga"] == ch01.TITHIKSHAYA_PER_MAHAYUGA


def test_time_unit_chains_close_on_the_texts_own_units(client: TestClient):
    """i.11-13 ships a chain the converter can walk without a gap.

    Expected: thirty kalas make one ghatika and two ghatikas one muhurta,
    every step's ratio is a whole number, and the units the SS itself
    states are marked apart from the ones Burgess's note supplies.
    """
    card = _cards(client, 2024, 4, 9)["i.11-13"]

    seconds = card["units_seconds"]
    assert 30 * seconds["kala"] == pytest.approx(seconds["nadi"])
    assert 2 * seconds["nadi"] == pytest.approx(seconds["muhurta"])
    assert 18 * seconds["nimesha"] == pytest.approx(seconds["kashtha"])
    assert 6 * seconds["prana"] == pytest.approx(seconds["vinadi"])
    assert 60 * seconds["vinadi"] == pytest.approx(seconds["nadi"])

    for key in ("ss", "puranic"):
        chain = next(c for c in card["chains"] if c["key"] == key)
        for unit in chain["units"]:
            if unit["per_next"] is not None:
                assert unit["per_next"] == pytest.approx(round(unit["per_next"]))

    # The longer measures are the one chain that does not close on a whole
    # number: two ayanas of six thirty-day months are 360 days, while the
    # SS's own sidereal year (v.37) is 365.2587565 of them.
    long_chain = next(c for c in card["chains"] if c["key"] == "long")
    ayana = next(u for u in long_chain["units"] if u["unit"] == "ayana")
    assert ayana["per_next"] == pytest.approx(ch01.SIDEREAL_YEAR_DAYS / 180.0, abs=1e-6)

    ss_chain = next(c for c in card["chains"] if c["key"] == "ss")
    assert all(unit["in_ss_text"] for unit in ss_chain["units"])
    puranic = next(c for c in card["chains"] if c["key"] == "puranic")
    assert puranic["source"] == "commentary"
    assert not next(u for u in puranic["units"] if u["unit"] == "kala")["in_ss_text"]


def test_epoch_positions_match_the_libraries_epoch_tables(client: TestClient):
    """i.56-58 carries the apsis and node positions at the Kali epoch.

    Expected: the figures equal ``MANDOCCA_AT_EPOCH`` and ``NODE_AT_EPOCH``,
    which are themselves pinned to Burgess's Iron-Age table, and the
    creation-to-Kali interval is the library's own constant.
    """
    card = _cards(client, 2024, 4, 9)["i.56-58"]

    rows = {row["planet"]: row for row in card["rows"]}
    for planet, longitude in ch01.MANDOCCA_AT_EPOCH.items():
        assert rows[planet]["mandocca"] == pytest.approx(longitude)
    for planet, longitude in ch01.NODE_AT_EPOCH.items():
        assert rows[planet]["node"] == pytest.approx(longitude)
    assert rows["Moon"]["node"] == 180.0
    assert card["years_creation_to_kali"] == ch01.YEARS_CREATION_TO_KALI
    assert card["civil_days_creation_to_kali"] == ch01.CIVIL_DAYS_CREATION_TO_KALI


def test_slider_constants_let_the_browser_reproduce_the_server(client: TestClient):
    """The mean-place card ships enough to recompute v.35 in the browser.

    Expected: applying the card's own ``bodies`` constants to its own
    ahargana gives back the longitudes the card already states, which is
    what the page's sliders do between requests.
    """
    card = _cards(client, 2024, 4, 9)["i.52-54"]

    stated = {row["planet"]: row["longitude"] for row in card["rows"]}
    for body in card["bodies"]:
        travelled = (
            body["bhagana"] * card["ahargana"] / card["civil_days_per_mahayuga"]
        ) * 360.0
        expected = (
            body["epoch"] - travelled if body["retrograde"] else body["epoch"] + travelled
        ) % 360.0
        assert stated[body["planet"]] == pytest.approx(expected, abs=1e-9)


def test_date_independent_cards_do_not_move_with_the_date(client: TestClient):
    """The four fixed cards return the same payload whatever the date.

    Expected: identical dicts for two dates a millennium apart, and a
    ``date_dependent`` flag that says so.
    """
    early = _cards(client, 999, 6, 15)
    late = _cards(client, 2024, 4, 9)

    for card_id in ["i.11-13", "i.15-22", "i.29-34", "i.56-58"]:
        assert early[card_id] == late[card_id]
        assert early[card_id]["date_dependent"] is False
    for card_id in ["i.23-24", "i.35-37", "i.48-51", "i.52-54", "i.55"]:
        assert early[card_id]["date_dependent"] is True


def test_year_outside_the_bounds_is_rejected(client: TestClient):
    """The route bounds the year rather than returning a meaningless figure.

    Expected: 422 from the Ch01In model, not a 200 with wild numbers.
    """
    assert client.post("/book/chapter/1", json={"year": 99999}).status_code == 422
    assert client.post("/book/chapter/1", json={"year": -9999}).status_code == 422


def test_route_does_not_depend_on_the_verse_corpus(monkeypatch, client: TestClient):
    """The calculations stand whether or not the corpus is reachable.

    The corpus is an external path (``SS_CORPUS_JSON_PATH``) that is often
    absent. Expected: pointing both corpus paths at nothing changes no
    figure the route returns.
    """
    monkeypatch.setenv("SS_CORPUS_DB_PATH", "nowhere.db")
    monkeypatch.setenv("SS_CORPUS_JSON_PATH", "nowhere.json")

    assert _cards(client, 2024, 4, 9)["i.23-24"]["ahargana"] == ch01.ahargana(
        ch01.julian_day(2024, 4, 9)
    )
