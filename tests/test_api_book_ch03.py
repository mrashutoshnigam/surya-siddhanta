"""Tests for the /book/chapter/3 verse-card payload.

These pin each card to the library's own figures so the React cards cannot
drift from ``ch03_direction_place_time`` / ``ch02_true_places``. All run
offline; the route must not touch the verse corpus.
"""
from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch02_true_places as ch02
from suryasiddhanta import ch03_direction_place_time as ch03
from suryasiddhanta.api.book_ch03 import CARD_ORDER
from suryasiddhanta.api.main import app


@pytest.fixture
def client() -> TestClient:
    """A TestClient over the whole FastAPI app."""
    return TestClient(app)


def _body(client: TestClient, year: int = 2024, month: int = 4, day: float = 9.0, **extra) -> dict:
    """POST a date to the chapter route and return the whole response body."""
    response = client.post(
        "/book/chapter/3", json={"year": year, "month": month, "day": day, **extra}
    )
    assert response.status_code == 200, response.text
    return response.json()


def _cards(client: TestClient, *args, **kwargs) -> dict:
    """Return only the ``cards`` mapping of the chapter payload."""
    return _body(client, *args, **kwargs)["cards"]


def _probe(client: TestClient, **payload) -> dict:
    """POST to the probe route and return the JSON answer."""
    response = client.post("/book/chapter/3/probe", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_every_card_id_is_present_with_its_chrome(client: TestClient):
    """The payload carries all nine cards, each with the fields the page needs.

    Expected: ``order`` equals ``CARD_ORDER`` (nine ids) and every card has
    ``verses``, ``title``, ``does`` and ``date_dependent``.
    """
    body = _body(client)
    assert body["order"] == CARD_ORDER
    assert len(CARD_ORDER) == 9
    for card_id in CARD_ORDER:
        card = body["cards"][card_id]
        for field in ("verses", "title", "does", "date_dependent"):
            assert field in card, f"{card_id} missing {field}"


def test_direction_card_equals_dik_from_gnomon(client: TestClient):
    """iii.1-4 reports the library's direction for two shadow-tip points.

    Expected: the default card's angle and cardinal equal ``dik_from_gnomon``
    of its own two tips; the probe agrees for other tips.
    """
    card = _cards(client)["iii.1-4"]
    (x1, y1), (x2, y2) = card["tip1"], card["tip2"]
    angle, cardinal = ch03.dik_from_gnomon(
        x1, y1, x2, y2, noon_shadow_direction=card["noon_shadow_direction"],
    )
    assert card["ns_angle"] == pytest.approx(angle)
    assert card["cardinal"] == cardinal

    answer = _probe(
        client, card="iii.1-4", x1=-6.0, y1=4.0, x2=5.0, y2=7.0,
        noon_shadow_direction="north",
    )
    angle, cardinal = ch03.dik_from_gnomon(
        -6.0, 4.0, 5.0, 7.0, noon_shadow_direction="north",
    )
    assert answer["ns_angle"] == pytest.approx(angle)
    assert answer["cardinal"] == cardinal


def test_direction_probe_rejects_coincident_tips(client: TestClient):
    """Identical tips cannot define a meridian line."""
    response = client.post(
        "/book/chapter/3/probe",
        json={"card": "iii.1-4", "x1": 0, "y1": 0, "x2": 0, "y2": 0,
              "noon_shadow_direction": "north"},
    )
    assert response.status_code == 422


def test_direction_probe_uses_noon_shadow_side(client: TestClient):
    """Tips south of the foot still identify geographic north when the Sun is north."""
    answer = _probe(
        client, card="iii.1-4", x1=-2.0, y1=-3.0, x2=2.0, y2=-3.0,
        noon_shadow_direction="south",
    )
    assert answer["cardinal"] == "N"
    assert answer["ns_angle"] == pytest.approx(0.0)


def test_gnomon_card_equals_gnomon_shadow_and_v8_hypotenuse(client: TestClient):
    """iii.5-8 gives the library's shadow and v.8's hypotenuse.

    Expected: shadow equals ``gnomon_shadow(altitude)``; hypotenuse is the
    square root of gnomon squared plus shadow squared.
    """
    card = _cards(client)["iii.5-8"]
    expected = ch03.gnomon_shadow(card["altitude"], 12.0)
    assert card["shadow"] == pytest.approx(expected.shadow_length)
    assert card["hypotenuse"] == pytest.approx(math.hypot(12.0, expected.shadow_length))

    answer = _probe(client, card="iii.5-8", altitude=30.0)
    assert answer["shadow"] == pytest.approx(ch03.gnomon_shadow(30.0, 12.0).shadow_length)


def test_gnomon_probe_with_sun_on_the_horizon_returns_null_not_infinity(client: TestClient):
    """At altitude 0 the shadow is infinite; JSON cannot carry that.

    Expected: HTTP 200 with ``shadow`` and ``hypotenuse`` both null.
    """
    answer = _probe(client, card="iii.5-8", altitude=0.0)
    assert answer["shadow"] is None
    assert answer["hypotenuse"] is None


def test_ayana_card_equals_ayanamsha_and_conversion(client: TestClient):
    """iii.9-12 reports the SS ayanamsha and each body's tropical longitude.

    Expected: ``ayanamsha`` equals ``ch02.ayanamsha(jd)`` and every row's
    tropical longitude equals ``sidereal_to_tropical`` of its sidereal one.
    """
    body = _body(client)
    card = body["cards"]["iii.9-12"]
    assert card["ayanamsha"] == pytest.approx(ch02.ayanamsha(body["jd"]))
    assert [r["body"] for r in card["rows"]] == ch01.ALL_PLANETS
    for row in card["rows"]:
        assert row["tropical"] == pytest.approx(
            ch02.sidereal_to_tropical(row["sidereal"], body["jd"])
        )


def test_latitude_card_round_trips_the_dates_latitude(client: TestClient):
    """iii.13-17 recovers the latitude a noon shadow was cast at.

    The card's default shadow is the noon shadow at Ujjain (23.18 N) for the
    date's Sun; the library's inverse must return that latitude.
    Expected: ``latitude`` within 0.01 degree of ``latitude_true``, and both
    equal to what ``latitude_from_noon_shadow`` gives for the same inputs.
    """
    card = _cards(client)["iii.13-17"]
    assert card["latitude"] == pytest.approx(card["latitude_true"], abs=0.01)
    assert card["latitude"] == pytest.approx(
        ch03.latitude_from_noon_shadow(
            card["shadow"], card["sun_tropical"],
            shadow_direction=card["shadow_direction"],
        )
    )


def test_latitude_probe_uses_shadow_direction(client: TestClient):
    """A Sun 14 degrees north of a 10N zenith casts a southward noon shadow."""
    shadow = 12.0 * math.tan(math.radians(14.0))
    answer = _probe(
        client, card="iii.13-17", shadow=shadow,
        sun_longitude=90.0, shadow_direction="south",
    )
    assert answer["latitude"] == pytest.approx(10.0, abs=0.01)
    assert answer["shadow_direction"] == "south"


def test_equatorial_card_equals_declination_and_right_ascension(client: TestClient):
    """iii.18-20 gives declination and right ascension for every body.

    Expected: each row equals ``ch03.declination`` / ``right_ascension`` of its
    tropical longitude; the probe agrees for a free longitude.
    """
    card = _cards(client)["iii.18-20"]
    assert len(card["rows"]) == 7
    for row in card["rows"]:
        assert row["declination"] == pytest.approx(ch03.declination(row["tropical"]))
        assert row["right_ascension"] == pytest.approx(ch03.right_ascension(row["tropical"]))

    answer = _probe(client, card="iii.18-20", longitude=100.0)
    assert answer["declination"] == pytest.approx(ch03.declination(100.0))
    assert answer["right_ascension"] == pytest.approx(ch03.right_ascension(100.0))


def test_noon_shadow_card_equals_gnomon_shadow_at_the_zenith_distance(client: TestClient):
    """iii.21-23: zenith distance is |latitude - declination|; the shadow follows.

    Expected: zenith distance is that difference, altitude its complement, and
    the shadow equals ``gnomon_shadow`` at that altitude.
    """
    answer = _probe(client, card="iii.21-23", latitude=23.18, declination=10.0)
    assert answer["zenith_distance"] == pytest.approx(13.18)
    assert answer["altitude"] == pytest.approx(76.82)
    assert answer["shadow"] == pytest.approx(ch03.gnomon_shadow(76.82, 12.0).shadow_length)

    card = _cards(client)["iii.21-23"]
    assert card["zenith_distance"] == pytest.approx(abs(card["latitude"] - card["declination"]))


def test_hour_angle_card_at_noon_is_ninety_minus_the_zenith_distance(client: TestClient):
    """iii.38-41 at hour angle 0 is the meridian altitude.

    Expected: altitude 90 - |latitude - declination| = 80 for (20, 10), and
    it equals ``equatorial_to_horizontal`` for the general case.
    """
    noon = _probe(client, card="iii.38-41", latitude=20.0, declination=10.0, hour_angle=0.0)
    assert noon["altitude"] == pytest.approx(80.0)

    answer = _probe(client, card="iii.38-41", latitude=20.0, declination=10.0, hour_angle=40.0)
    azimuth, altitude = ch03.equatorial_to_horizontal(0.0, 10.0, 40.0, 20.0)
    assert answer["altitude"] == pytest.approx(altitude)
    assert answer["azimuth"] == pytest.approx(azimuth)


def test_cara_card_equals_the_library_day_and_night(client: TestClient):
    """iii.42 reports cara and the length of day and night.

    Expected: day equals ``day_length_ghatis``, night equals
    ``night_length_ghatis``, day is twice (15 + cara), and day + night = 60.
    """
    answer = _probe(client, card="iii.42", latitude=23.18, sun_longitude=100.0)
    assert answer["day_ghatis"] == pytest.approx(ch03.day_length_ghatis(23.18, 100.0))
    assert answer["night_ghatis"] == pytest.approx(ch03.night_length_ghatis(23.18, 100.0))
    assert answer["day_ghatis"] == pytest.approx(2 * (15.0 + answer["cara_ghatis"]))
    assert answer["day_ghatis"] + answer["night_ghatis"] == pytest.approx(60.0)


@pytest.mark.parametrize("latitude", [90.0, -90.0])
def test_cara_probe_is_finite_at_the_poles(client: TestClient, latitude: float):
    """The tangent of latitude blows up at the poles; the card must not.

    Expected: HTTP 200, every numeric field finite, day + night = 60.
    """
    answer = _probe(client, card="iii.42", latitude=latitude, sun_longitude=100.0)
    for key in ("cara_ghatis", "sunrise_hour_angle", "day_ghatis", "night_ghatis"):
        assert math.isfinite(answer[key]), key
    assert answer["day_ghatis"] + answer["night_ghatis"] == pytest.approx(60.0)


def test_rising_times_at_lanka_match_the_texts_figures(client: TestClient):
    """iii.43-44 gives 1670, 1795, 1935 respirations at the equator.

    Expected: at latitude 0 each sign's rising time in asus (degrees * 60)
    is within 6 of the text's figure; at any latitude the twelve times sum
    to 360 degrees and equal ``oblique_ascension``.
    """
    lanka = _probe(client, card="iii.43-44", latitude=0.0)
    assert len(lanka["rows"]) == 12
    for row in lanka["rows"]:
        assert row["asus"] == pytest.approx(row["text_asus"], abs=6.0), row["rashi"]

    here = _probe(client, card="iii.43-44", latitude=23.18)
    assert sum(r["degrees"] for r in here["rows"]) == pytest.approx(360.0, abs=1e-6)
    for row in here["rows"]:
        assert row["degrees"] == pytest.approx(ch03.oblique_ascension(row["index"], 23.18))


def test_date_independent_cards_are_identical_across_dates(client: TestClient):
    """Cards flagged as fixed must not change with the date.

    Expected: iii.1-4, iii.5-8 and iii.43-44 are equal for two far-apart dates.
    """
    a = _cards(client, 2024, 4, 9.0)
    b = _cards(client, 1500, 11, 3.0)
    for card_id in ("iii.1-4", "iii.5-8", "iii.43-44"):
        assert a[card_id]["date_dependent"] is False
        assert a[card_id] == b[card_id]


@pytest.mark.parametrize("year", [-3000, 4000])
def test_chapter_route_accepts_the_schemas_extreme_years(client: TestClient, year: int):
    """The bounds of the date schema are valid input, not errors.

    Expected: HTTP 200 and all nine cards, for both edge years.
    """
    assert len(_cards(client, year, 1, 1.0)) == 9


def test_chapter_3_route_never_imports_the_corpus(client: TestClient):
    """The calculation route must work with no corpus present.

    Expected: ``book_ch03``'s own namespace holds no corpus module.
    """
    import suryasiddhanta.api.book_ch03 as module

    _body(client)
    assert "retrieve" not in vars(module)
    assert "corpus" not in vars(module)


@pytest.mark.parametrize(
    "payload",
    [
        {"year": 5000, "month": 1, "day": 1},
        {"year": 2024, "month": 13, "day": 1},
        {"year": 2024, "month": 1, "day": 1, "latitude": 91},
    ],
)
def test_chapter_route_rejects_out_of_range_input(client: TestClient, payload: dict):
    """Out-of-range year, month or latitude is refused, not computed.

    Expected: HTTP 422 for each.
    """
    assert client.post("/book/chapter/3", json=payload).status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"card": "iii.99"},
        {"card": "iii.21-23", "latitude": 10.0},
        {"card": "iii.21-23", "latitude": 95.0, "declination": 0.0},
        {"card": "iii.5-8", "altitude": 120.0},
    ],
)
def test_probe_rejects_unknown_cards_missing_and_out_of_range_fields(
    client: TestClient, payload: dict
):
    """The probe validates its card, its required fields and their bounds.

    Expected: HTTP 422 for an unknown card, a missing required field and an
    out-of-range value.
    """
    assert client.post("/book/chapter/3/probe", json=payload).status_code == 422
