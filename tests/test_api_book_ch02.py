"""Tests for the /book/chapter/2 verse-card payload.

These pin the card payload to the library's own figures so the React cards
cannot drift from ``ch02_true_places`` / ``ch01_mean_motions`` /
``ch03_direction_place_time``. All run offline; the route must not touch the
verse corpus.
"""
from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch02_true_places as ch02
from suryasiddhanta.api.book_ch02 import CARD_ORDER
from suryasiddhanta.api.main import app


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, year: int = 2024, month: int = 4, day: float = 9.0, **extra) -> dict:
    """POST a date to the chapter route and return the whole response body."""
    response = client.post(
        "/book/chapter/2", json={"year": year, "month": month, "day": day, **extra}
    )
    assert response.status_code == 200, response.text
    return response.json()


def _cards(client: TestClient, *args, **kwargs) -> dict:
    """Return only the ``cards`` mapping of the chapter payload."""
    return _body(client, *args, **kwargs)["cards"]


def test_sine_table_card_equals_the_library_table(client: TestClient):
    """ii.15-27 states the 24 tabular sines exactly as ``ch02.JYA_TABLE`` does.

    Expected: jya column equals JYA_TABLE, differences are its first
    differences, versed sines equal ``utkrama_jya``, and the one safe part of
    the v.15 rule (first sine = 1800' / 8) equals the first tabular sine.
    """
    card = _cards(client)["ii.15-27"]

    assert [r["jya"] for r in card["rows"]] == ch02.JYA_TABLE
    assert card["radius"] == ch02.R_SINE
    assert card["first_sine"] == ch02.JYA_TABLE[0] == 1800 / 8
    previous = 0
    for row in card["rows"]:
        assert row["difference"] == row["jya"] - previous
        previous = row["jya"]
        assert row["utkrama"] == pytest.approx(ch02.utkrama_jya(row["degrees"]))
    assert card["rows"][-1]["utkrama"] == ch02.R_SINE


def test_epicycle_card_equals_the_library_constants(client: TestClient):
    """ii.34-38 lists the epicycle sizes without altering them.

    Expected: each body's even/odd manda size equals ``MANDA_EPICYCLE``;
    sighra sizes equal ``SIGHRA_EPICYCLE`` for the five star-planets and are
    null for Sun and Moon.
    """
    card = _cards(client)["ii.34-38"]
    rows = {r["body"]: r for r in card["rows"]}

    assert set(rows) == set(ch01.ALL_PLANETS)
    for body, pair in ch02.MANDA_EPICYCLE.items():
        assert rows[body]["manda_even"] == pair.even
        assert rows[body]["manda_odd"] == pair.odd
    for body in ("Sun", "Moon"):
        assert rows[body]["sighra_even"] is None
    for body, pair in ch02.SIGHRA_EPICYCLE.items():
        assert rows[body]["sighra_even"] == pair.even
        assert rows[body]["sighra_odd"] == pair.odd


def test_interpolation_forward_equals_library_jya():
    """v.31-32's stepwise interpolation reproduces ``ch02.jya``.

    Expected: for arcs across 0..90 degrees the interpolated value equals
    ``jya(arc)``; the edges (0 and 90) do not divide by zero.
    """
    from suryasiddhanta.api.book_ch02 import _interp_forward

    for arc in (0.0, 0.5, 3.75, 10.0, 44.9, 89.99, 90.0):
        assert _interp_forward(arc)["interpolated"] == pytest.approx(ch02.jya(arc))


def test_interpolation_inverse_equals_library_arcjya():
    """v.33's inverse interpolation reproduces ``ch02.arcjya``.

    Expected: for sines across 0..3438 the arc in arcminutes equals
    ``arcjya(sine) * 60``; the edges (0 and R) are handled.
    """
    from suryasiddhanta.api.book_ch02 import _interp_inverse

    for sine in (0.0, 1.0, 225.0, 1000.0, 3437.0, 3438.0):
        assert _interp_inverse(sine)["arcmin"] == pytest.approx(ch02.arcjya(sine) * 60.0)


def test_chapter_2_route_never_imports_the_corpus(client: TestClient):
    """The calculation route must work with no corpus present.

    Expected: importing and calling the route leaves ``corpus.retrieve``
    unimported by ``book_ch02``'s own module namespace.
    """
    import suryasiddhanta.api.book_ch02 as module

    _body(client)
    assert "retrieve" not in vars(module)
    assert "corpus" not in vars(module)


@pytest.mark.parametrize(
    "payload",
    [
        {"year": 4001, "month": 1, "day": 1},
        {"year": -3001, "month": 1, "day": 1},
        {"year": 2024, "month": 13, "day": 1},
        {"year": 2024, "month": 1, "day": 1, "latitude": 91},
    ],
)
def test_out_of_range_input_is_rejected(client: TestClient, payload: dict):
    """Out-of-range year, month or latitude is refused, not computed.

    Expected: HTTP 422 for each.
    """
    assert client.post("/book/chapter/2", json=payload).status_code == 422


def test_every_card_is_present_and_in_verse_order(client: TestClient):
    """The route returns all eleven cards, in the chapter's own order.

    Expected: ``order`` equals CARD_ORDER, every id has a card, and each card
    carries the chrome the React VerseCard renders.
    """
    body = _body(client)

    assert body["order"] == CARD_ORDER
    assert len(CARD_ORDER) == 11
    assert set(body["cards"]) == set(CARD_ORDER)
    for card_id in CARD_ORDER:
        card = body["cards"][card_id]
        assert card["id"] == card_id
        assert card["verses"] and card["title"] and card["does"]
        assert isinstance(card["date_dependent"], bool)


def test_manda_card_equals_manda_correction(client: TestClient):
    """ii.39's phala is ``ch02.manda_correction`` for every body.

    Expected: each body's phala equals the library call on the same mean and
    apsis; the corrected place equals ``manda_longitude``.
    """
    card = _cards(client)["ii.39"]
    rows = {r["body"]: r for r in card["rows"]}
    jd = ch01.julian_day(2024, 4, 9.0)

    assert set(rows) == set(ch01.ALL_PLANETS)
    for body in ch01.ALL_PLANETS:
        mean = ch01.mean_longitude(body, jd)
        apsis = ch01.mandocca_longitude(body, jd)
        assert rows[body]["phala"] == pytest.approx(ch02.manda_correction(body, mean, apsis))
        assert rows[body]["corrected"] == pytest.approx(ch02.manda_longitude(body, mean, apsis))


def test_sighra_card_equals_sighra_correction_and_omits_sun_and_moon(client: TestClient):
    """ii.40-42 agrees with the true-place pipeline; Sun and Moon have none.

    Expected: five star-planet rows whose phala equals
    ``ch02.sighra_correction(body, ms2, sighrocca)`` with ms2/sighrocca from
    ``true_longitude_full``, equals the last stage correction of the ii.43-45
    card, and is reproduced by arcsin(bhujaphala / hypotenuse); the anomaly
    equals the ii.29-30 card's sighra kendra; Sun and Moon are listed under
    ``no_sighra`` instead of raising.
    """
    cards = _cards(client)
    card = cards["ii.40-42"]
    rows = {r["body"]: r for r in card["rows"]}
    true_rows = {r["body"]: r for r in cards["ii.43-45"]["rows"]}
    bhuja_rows = {r["body"]: r for r in cards["ii.29-30"]["rows"]}
    jd = ch01.julian_day(2024, 4, 9.0)

    assert set(rows) == {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    assert card["no_sighra"] == ["Sun", "Moon"]
    for body, row in rows.items():
        full = ch02.true_longitude_full(body, jd)
        expected = ch02.sighra_correction(body, full["ms2"], full["sighrocca"])
        assert row["phala"] == pytest.approx(expected, abs=1e-3)
        assert row["phala"] == pytest.approx(true_rows[body]["stages"][-1]["correction"], abs=1e-3)
        assert row["kendra"] == pytest.approx(bhuja_rows[body]["sighra"]["kendra"], abs=1e-3)
        rebuilt = math.degrees(math.asin(row["bhujaphala"] / row["hypotenuse"]))
        assert abs(row["phala"]) == pytest.approx(rebuilt, abs=1e-2)


def test_true_place_card_equals_the_full_pipeline(client: TestClient):
    """ii.43-45's final longitude equals ``ch02.compute`` for each body.

    Expected: true longitude agrees within the pipeline's own 4-decimal
    rounding, and Sun/Moon report two stages (manda only) while the
    star-planets report five.
    """
    card = _cards(client)["ii.43-45"]
    rows = {r["body"]: r for r in card["rows"]}

    for body in ch01.ALL_PLANETS:
        expected = ch02.compute(body, 2024, 4, 9.0).true_longitude
        assert rows[body]["true_longitude"] == pytest.approx(expected, abs=1e-3)
    assert len(rows["Sun"]["stages"]) == 2
    assert len(rows["Moon"]["stages"]) == 2
    assert len(rows["Mars"]["stages"]) == 5


def test_true_place_stage_longitudes_follow_the_pipeline(client: TestClient):
    """ii.43-45's Mars stages carry the pipeline's intermediate longitudes.

    Expected: stage 1 is the mean plus half the first sighra correction,
    stage 2 equals ``ms1``, stage 3 equals ``ms2`` and the last equals the
    true longitude (within the pipeline's 4-decimal rounding).
    """
    jd = ch01.julian_day(2024, 4, 9.0)
    full = ch02.true_longitude_full("Mars", jd)
    stages = {r["body"]: r for r in _cards(client)["ii.43-45"]["rows"]}["Mars"]["stages"]

    assert stages[1]["longitude"] == pytest.approx(
        ch02.normalize(full["mean_lon"] + full["sighra_corr1"] / 2.0), abs=1e-3)
    assert stages[2]["longitude"] == pytest.approx(full["ms1"], abs=1e-3)
    assert stages[3]["longitude"] == pytest.approx(full["ms2"], abs=1e-3)
    assert stages[-1]["longitude"] == pytest.approx(full["true_longitude"], abs=1e-3)


def test_panchanga_cards_equal_the_ch01_functions(client: TestClient):
    """ii.65, ii.66 and ii.67-69 are the ch01 functions on the true Sun and Moon.

    Expected: yoga, tithi and karana equal ``ch01.yoga_from_longitudes``,
    ``tithi_from_elongation`` and ``karana_from_elongation`` on the same
    true longitudes the true-place card reports.
    """
    cards = _cards(client)
    sun = cards["ii.43-45"]["rows"][0]["true_longitude"]
    moon = cards["ii.43-45"]["rows"][1]["true_longitude"]
    assert cards["ii.43-45"]["rows"][0]["body"] == "Sun"

    number, name = ch01.yoga_from_longitudes(sun, moon)
    assert (cards["ii.65"]["number"], cards["ii.65"]["name"]) == (number, name)

    tithi, fraction = ch01.tithi_from_elongation(moon, sun)
    assert cards["ii.66"]["number"] == tithi
    assert cards["ii.66"]["fraction"] == pytest.approx(fraction)

    knum, kname, ktype = ch01.karana_from_elongation(moon, sun)
    assert (cards["ii.67-69"]["number"], cards["ii.67-69"]["name"], cards["ii.67-69"]["kind"]) == (knum, kname, ktype)


def test_date_independent_cards_are_identical_across_dates(client: TestClient):
    """Fixed cards do not vary with the date.

    Expected: ii.15-27, ii.31-33 and ii.34-38 are equal for two dates.
    """
    a, b = _cards(client, 1860, 1, 1.0), _cards(client, 2024, 4, 9.0)
    for card_id in ("ii.15-27", "ii.31-33", "ii.34-38"):
        assert a[card_id] == b[card_id]
        assert a[card_id]["date_dependent"] is False


@pytest.mark.parametrize("year", [-3000, 4000])
def test_extreme_years_still_yield_finite_numbers(client: TestClient, year: int):
    """The bounds of the year range compute without error or NaN.

    Expected: HTTP 200 and every true longitude finite and within [0, 360].
    """
    rows = _cards(client, year)["ii.43-45"]["rows"]
    for row in rows:
        assert math.isfinite(row["true_longitude"])
        assert 0.0 <= row["true_longitude"] <= 360.0


def test_day_length_card_follows_the_verse_and_ch03(client: TestClient):
    """ii.60-63: day-radius is the radius less the versed sine of declination.

    Expected: day_radius equals ``R - utkrama_jya(declination)``; day and
    night lengths equal ``ch03.day_length_ghatis`` / ``night_length_ghatis``
    and sum to 60 ghatis, for the latitude posted.
    """
    from suryasiddhanta.ch03_direction_place_time import day_length_ghatis, night_length_ghatis

    card = _cards(client, latitude=12.0)["ii.60-63"]

    assert card["latitude"] == 12.0
    assert card["day_radius"] == pytest.approx(ch02.R_SINE - ch02.utkrama_jya(card["declination"]))
    assert card["day_ghatis"] == pytest.approx(day_length_ghatis(12.0, card["sun_tropical"]))
    assert card["night_ghatis"] == pytest.approx(night_length_ghatis(12.0, card["sun_tropical"]))
    assert card["day_ghatis"] + card["night_ghatis"] == pytest.approx(60.0)


def test_day_length_card_uses_the_true_sun_and_its_declination(client: TestClient):
    """ii.60-63 starts from the date's true Sun, converted to tropical.

    Expected: sun_tropical equals ``sidereal_to_tropical`` of the pipeline's
    true Sun, and declination equals ``ch03.declination`` of that longitude.
    """
    from suryasiddhanta.ch03_direction_place_time import declination

    jd = ch01.julian_day(2024, 4, 9.0)
    sun = ch02.true_longitude_full("Sun", jd)["true_longitude"]
    card = _cards(client)["ii.60-63"]

    assert card["sun_tropical"] == pytest.approx(ch02.sidereal_to_tropical(sun, jd))
    assert card["declination"] == pytest.approx(declination(card["sun_tropical"]))


def _probe(client: TestClient, **payload):
    """POST a probe request and return the raw response."""
    return client.post("/book/chapter/2/probe", json=payload)


@pytest.mark.parametrize("kendra", [0, 90, 180, 270, 360, -45, 725])
def test_probe_bhuja_koti_handles_quadrant_boundaries(client: TestClient, kendra: float):
    """v.29-30 probe at the quadrant edges and outside 0..360.

    Expected: 200; bhuja and koti in [0, 90] and summing to 90; the quadrant
    is 1..4; 360 and -45 fold onto their equivalents.
    """
    body = _probe(client, card="ii.29-30", kendra=kendra).json()

    assert 0.0 <= body["bhuja"] <= 90.0 and 0.0 <= body["koti"] <= 90.0
    assert body["bhuja"] + body["koti"] == pytest.approx(90.0)
    assert body["quadrant"] in (1, 2, 3, 4)
    assert body["kendra"] == pytest.approx(kendra % 360.0)


def test_probe_interpolation_edges(client: TestClient):
    """v.31-33 probes at the ends of the table.

    Expected: arc 0 gives sine 0, arc 90 gives R; sine 0 gives arc 0, sine R
    gives 90 degrees.
    """
    assert _probe(client, card="ii.31-33", mode="forward", arc_deg=0).json()["interpolated"] == 0.0
    assert _probe(client, card="ii.31-33", mode="forward", arc_deg=90).json()["interpolated"] == ch02.R_SINE
    assert _probe(client, card="ii.31-33", mode="inverse", sine=0).json()["arc_deg"] == 0.0
    assert _probe(client, card="ii.31-33", mode="inverse", sine=3438).json()["arc_deg"] == 90.0


def test_probe_epicycle_matches_library_and_sun_has_no_sighra(client: TestClient):
    """v.34-38 probe returns the library's pulsating sizes.

    Expected: Mars manda and sighra sizes equal the ch02 functions at the
    kendra; the Sun's sighra is null.
    """
    mars = _probe(client, card="ii.34-38", body="Mars", kendra=123.0).json()
    assert mars["manda"] == pytest.approx(ch02.corrected_manda_epicycle("Mars", 123.0))
    assert mars["sighra"] == pytest.approx(ch02.corrected_sighra_epicycle("Mars", 123.0))
    assert _probe(client, card="ii.34-38", body="Sun", kendra=123.0).json()["sighra"] is None


@pytest.mark.parametrize("latitude", [-90, 0, 23.18, 66.0, 90])
def test_probe_day_length_clamps_at_extreme_latitudes(client: TestClient, latitude: float):
    """v.60-63 probe at and near the poles.

    Expected: 200 and finite results; day + night always equals 60 ghatis,
    even when the Sun never rises or never sets.
    """
    body = _probe(client, card="ii.60-63", latitude=latitude, sun_longitude=100.0).json()

    assert math.isfinite(body["day_ghatis"])
    assert body["day_ghatis"] + body["night_ghatis"] == pytest.approx(60.0)
    assert 0.0 <= body["day_ghatis"] <= 60.0


@pytest.mark.parametrize(
    "payload",
    [
        {"card": "ii.29-30"},
        {"card": "ii.34-38", "kendra": 10},
        {"card": "ii.34-38", "body": "Pluto", "kendra": 10},
        {"card": "ii.31-33", "mode": "forward", "arc_deg": 91},
        {"card": "ii.31-33", "mode": "inverse", "sine": 5000},
        {"card": "ii.60-63", "latitude": 95, "sun_longitude": 10},
        {"card": "ii.99"},
    ],
)
def test_probe_rejects_missing_or_bad_arguments(client: TestClient, payload: dict):
    """A probe missing what its card needs, or out of range, is refused.

    Expected: HTTP 422 for each.
    """
    assert _probe(client, **payload).status_code == 422


def test_probe_defaults_equal_the_chapter_card_samples(client: TestClient):
    """A probe with the card's default input returns the card's shipped shape.

    Expected: forward 30 degrees, inverse sine 1000, the Sun at kendra 45 and
    the bare kendra 45 equal the chapter payload's ``forward``, ``inverse``,
    Sun-row ``sample`` and ii.29-30 ``sample`` respectively.
    """
    cards = _cards(client)
    sun_row = next(r for r in cards["ii.34-38"]["rows"] if r["body"] == "Sun")

    cases = [
        (dict(card="ii.31-33", mode="forward", arc_deg=30.0), cards["ii.31-33"]["forward"]),
        (dict(card="ii.31-33", mode="inverse", sine=1000.0), cards["ii.31-33"]["inverse"]),
        (dict(card="ii.34-38", body="Sun", kendra=45.0), sun_row["sample"]),
        (dict(card="ii.29-30", kendra=45.0), cards["ii.29-30"]["sample"]),
    ]
    for payload, expected in cases:
        assert _probe(client, **payload).json() == expected


@pytest.mark.parametrize(
    "payload",
    [
        {"card": "ii.31-33", "mode": "sideways", "arc_deg": 10},
        {"card": "ii.31-33", "arc_deg": 10},
        {"card": "ii.31-33", "mode": "forward"},
        {"card": "ii.31-33", "mode": "inverse"},
        {"card": "ii.60-63", "latitude": 10},
    ],
)
def test_probe_rejects_missing_mode_and_missing_inputs(client: TestClient, payload: dict):
    """Invalid or absent ``mode`` and missing arc/sine/sun_longitude are refused.

    Expected: HTTP 422 for each.
    """
    assert _probe(client, **payload).status_code == 422
