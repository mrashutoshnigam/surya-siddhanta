"""Verse-indexed payloads for the React "Book" page of Chapter 3.

Chapter 3 counterpart of ``book_ch02.py``: for one date (and a latitude), what
does each computational verse of *Of Direction, Place and Time* yield? The
React page renders one card per entry of ``CARD_ORDER`` in Burgess's order.

No astronomy lives here. Builders call ``ch01``/``ch02``/``ch03`` and shape
the result; tests pin every card to the library's figures. Lagna (v.46-51)
is available in ``ch03.lagna`` but has no verse card here.

Verse numbers follow Burgess as read from the corpus, not the module
docstring of ``ch03_direction_place_time.py``.

Reference: SS Ch.3 v.1-44; Burgess (1860) pp.100-140
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch02_true_places as ch02
from suryasiddhanta import ch03_direction_place_time as ch03

from .schemas import Ch03In, Ch03ProbeIn

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_3_TITLE = "Of Direction, Place and Time"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = [
    "iii.1-4",
    "iii.5-8",
    "iii.9-12",
    "iii.13-17",
    "iii.18-20",
    "iii.21-23",
    "iii.38-41",
    "iii.42",
    "iii.43-44",
]

_GNOMON = 12.0

#: Rising times at Lanka in respirations (asus), verse 44: Aries, Taurus and
#: Gemini, then the same three in reverse, the whole run repeated for the
#: southern six signs.
_TEXT_RISING_ASUS: List[int] = [1670, 1795, 1935, 1935, 1795, 1670] * 2


@dataclass
class _Ctx:
    """What a card builder may depend on: the date and the observer's latitude.

    ``sun_tropical`` and ``positions`` are computed lazily, once per request,
    so cards that need neither never pay for the true-longitude pipeline.
    """

    jd: float
    latitude: float

    @cached_property
    def sun_tropical(self) -> float:
        """The date's true Sun, converted from sidereal to tropical longitude."""
        sun = ch02.true_longitude_full("Sun", self.jd)["true_longitude"]
        return ch02.sidereal_to_tropical(sun, self.jd)

    @cached_property
    def positions(self) -> Dict[str, Dict[str, Any]]:
        """``ch02.true_longitude_full`` for every body on this date."""
        return {b: ch02.true_longitude_full(b, self.jd) for b in ch01.ALL_PLANETS}


def _rashi(longitude: float) -> str:
    """Format a longitude as its sign and the degrees elapsed within it."""
    _, name, deg_in = ch01.rashi_from_longitude(longitude)
    return f"{name} {deg_in:.2f}°"


# ─────────────────────────────  pure helpers  ─────────────────────────────

def _direction(x1: float, y1: float, x2: float, y2: float,
               noon_shadow_direction: str) -> Dict[str, Any]:
    """The north-south line from two shadow-tip points (v.1-4), as the library gives it."""
    try:
        angle, cardinal = ch03.dik_from_gnomon(
            x1, y1, x2, y2, noon_shadow_direction=noon_shadow_direction,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "tip1": [x1, y1],
        "tip2": [x2, y2],
        "midpoint": [(x1 + x2) / 2.0, (y1 + y2) / 2.0],
        "noon_shadow_direction": noon_shadow_direction,
        "ns_angle": angle,
        "cardinal": cardinal,
    }


def _shadow(altitude: float, gnomon: float = _GNOMON) -> Dict[str, Any]:
    """Shadow and hypotenuse of a gnomon at a solar altitude (v.5-8).

    The hypotenuse is v.8's own rule, the square root of gnomon squared plus
    shadow squared. With the Sun on or below the horizon the library returns
    an infinite shadow; JSON cannot carry that, so both figures are ``None``.
    """
    result = ch03.gnomon_shadow(altitude, gnomon)
    if not math.isfinite(result.shadow_length):
        return {"gnomon": gnomon, "shadow": None, "hypotenuse": None,
                "direction": result.direction}
    return {
        "gnomon": gnomon,
        "shadow": result.shadow_length,
        "hypotenuse": math.hypot(gnomon, result.shadow_length),
        "direction": result.direction,
    }


def _gnomon(altitude: float) -> Dict[str, Any]:
    """The iii.5-8 card body: the altitude and its shadow."""
    return {"altitude": altitude, **_shadow(altitude)}


def _latitude_from_shadow(shadow: float, sun_tropical: float,
                          shadow_direction: str) -> Dict[str, Any]:
    """Latitude from a noon shadow and the Sun's longitude (v.13-17)."""
    return {
        "shadow": shadow,
        "sun_tropical": sun_tropical,
        "declination": ch03.declination(sun_tropical),
        "altitude": ch03.solar_altitude_from_shadow(shadow, _GNOMON),
        "shadow_direction": shadow_direction,
        "latitude": ch03.latitude_from_noon_shadow(
            shadow, sun_tropical, _GNOMON, shadow_direction=shadow_direction,
        ),
    }


def _equatorial(tropical: float) -> Dict[str, Any]:
    """Right ascension and declination of a point on the ecliptic (v.18-20)."""
    ra, dec = ch03.ecliptic_to_equatorial(tropical)
    return {
        "tropical": tropical,
        "right_ascension": ra,
        "declination": dec,
        "direction": "north" if dec >= 0 else "south",
    }


def _noon_shadow(latitude: float, declination: float) -> Dict[str, Any]:
    """Noon zenith distance, altitude and shadow from latitude and declination (v.21-23)."""
    zenith = abs(latitude - declination)
    altitude = 90.0 - zenith
    return {
        "latitude": latitude,
        "declination": declination,
        "zenith_distance": zenith,
        "altitude": altitude,
        **_shadow(altitude),
    }


def _hour_angle(latitude: float, declination: float, hour_angle: float) -> Dict[str, Any]:
    """Altitude, azimuth and shadow at an hour angle from the meridian (v.38-41)."""
    azimuth, altitude = ch03.equatorial_to_horizontal(
        0.0, declination, hour_angle % 360.0, latitude
    )
    return {
        "latitude": latitude,
        "declination": declination,
        "hour_angle": hour_angle,
        "azimuth": azimuth,
        "altitude": altitude,
        **_shadow(altitude),
    }


def _cara(latitude: float, sun_tropical: float) -> Dict[str, Any]:
    """Cara, the sunrise hour angle, and the lengths of day and night (v.42)."""
    dec = ch03.declination(sun_tropical)
    cara = ch03.cara(latitude, dec)
    return {
        "latitude": latitude,
        "sun_tropical": sun_tropical,
        "declination": dec,
        "cara_ghatis": cara,
        "half_day_ghatis": 15.0 + cara,
        "sunrise_hour_angle": ch03.sunrise_hour_angle(latitude, dec),
        "sunrise_offset_hours": ch03.sunrise_sunset_offset(latitude, dec),
        "day_ghatis": ch03.day_length_ghatis(latitude, sun_tropical),
        "night_ghatis": ch03.night_length_ghatis(latitude, sun_tropical),
    }


def _rising(latitude: float) -> Dict[str, Any]:
    """The twelve signs' rising times at a latitude, beside Lanka's and the text's (v.43-44)."""
    rows = []
    for i in range(12):
        degrees = ch03.oblique_ascension(i, latitude)
        rows.append({
            "index": i,
            "rashi": ch01.RASHIS[i],
            "degrees": degrees,
            "asus": degrees * 60.0,
            "lanka_asus": ch03.oblique_ascension(i, 0.0) * 60.0,
            "text_asus": _TEXT_RISING_ASUS[i],
        })
    return {"latitude": latitude, "rows": rows}


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_direction(_ctx: _Ctx) -> Dict[str, Any]:
    """iii.1-4: a morning and an afternoon shadow tip, and the line they fix."""
    return _direction(-9.0, 5.0, 8.0, 5.0, "north")


def _card_gnomon(_ctx: _Ctx) -> Dict[str, Any]:
    """iii.5-8: the 12-digit gnomon's shadow and hypotenuse at 45 degrees."""
    return _gnomon(45.0)


def _card_ayana(ctx: _Ctx) -> Dict[str, Any]:
    """iii.9-12: the ayanamsha and each body's sidereal and tropical place."""
    rows = []
    for body in ch01.ALL_PLANETS:
        sidereal = ctx.positions[body]["true_longitude"]
        rows.append({
            "body": body,
            "sidereal": sidereal,
            "tropical": ch02.sidereal_to_tropical(sidereal, ctx.jd),
            "rashi": _rashi(sidereal),
        })
    return {
        "ayanamsha": ch02.ayanamsha(ctx.jd),
        "kali_years": ch02.kali_years_elapsed(ctx.jd),
        "period_years": ch02.AYANAMSHA_PERIOD,
        "rows": rows,
    }


def _card_latitude(ctx: _Ctx) -> Dict[str, Any]:
    """iii.13-17: the noon shadow at the page latitude, and the latitude it gives back."""
    declination = ch03.declination(ctx.sun_tropical)
    shadow = ch03.gnomon_shadow(90.0 - abs(ctx.latitude - declination), _GNOMON).shadow_length
    shadow_direction = "north" if ctx.latitude >= declination else "south"
    return {
        **_latitude_from_shadow(shadow, ctx.sun_tropical, shadow_direction),
        "latitude_true": ctx.latitude,
    }


def _card_equatorial(ctx: _Ctx) -> Dict[str, Any]:
    """iii.18-20: declination and right ascension of every body, tropically."""
    rows = []
    for body in ch01.ALL_PLANETS:
        tropical = ch02.sidereal_to_tropical(ctx.positions[body]["true_longitude"], ctx.jd)
        rows.append({"body": body, **_equatorial(tropical)})
    return {"rows": rows}


def _card_noon_shadow(ctx: _Ctx) -> Dict[str, Any]:
    """iii.21-23: the noon shadow for the date's Sun at the page latitude."""
    return _noon_shadow(ctx.latitude, ch03.declination(ctx.sun_tropical))


def _card_hour_angle(ctx: _Ctx) -> Dict[str, Any]:
    """iii.38-41: the Sun two hours (30 degrees) from the meridian."""
    return _hour_angle(ctx.latitude, ch03.declination(ctx.sun_tropical), 30.0)


def _card_cara(ctx: _Ctx) -> Dict[str, Any]:
    """iii.42: cara and day length for the date's Sun at the page latitude."""
    return _cara(ctx.latitude, ctx.sun_tropical)


def _card_rising(ctx: _Ctx) -> Dict[str, Any]:
    """iii.43-44: the rising times at the page latitude."""
    return _rising(ctx.latitude)


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "iii.1-4": (
        "1-4", "The north-south line",
        "Two shadow tips at equal altitudes fix the east-west line; its bisector is the meridian.",
        False, _card_direction,
    ),
    "iii.5-8": (
        "5-8", "The gnomon, its shadow and hypotenuse",
        "A twelve-digit gnomon at a given altitude: the shadow, and the hypotenuse as root of the two squares.",
        False, _card_gnomon,
    ),
    "iii.9-12": (
        "9-12", "The precession of the equinoxes",
        "The ayana degrees, and what they do to each planet's place.",
        True, _card_ayana,
    ),
    "iii.13-17": (
        "13-17", "The latitude from the noon shadow",
        "The noon shadow and the Sun's declination give the latitude of the place.",
        True, _card_latitude,
    ),
    "iii.18-20": (
        "18-20", "Declination and right ascension",
        "The Sun's or a planet's ecliptic longitude carried to the equator.",
        True, _card_equatorial,
    ),
    "iii.21-23": (
        "21-23", "The noon shadow from the declination",
        "Zenith distance is latitude less declination; from it, the noon shadow and hypotenuse.",
        True, _card_noon_shadow,
    ),
    "iii.38-41": (
        "38-41", "Altitude at an hour angle",
        "The Sun's altitude, azimuth and shadow at any distance in time from noon.",
        True, _card_hour_angle,
    ),
    "iii.42": (
        "42", "The cara and the length of the day",
        "The ascensional difference, and how it lengthens or shortens the day at a latitude.",
        True, _card_cara,
    ),
    "iii.43-44": (
        "43-44", "The rising times of the signs",
        "Each sign's rising time in respirations, at Lanka and at your latitude.",
        False, _card_rising,
    ),
}


def _build_card(card_id: str, ctx: _Ctx) -> Dict[str, Any]:
    """Build one card's full payload, chrome fields included."""
    verses, title, does, date_dependent, builder = _CARDS[card_id]
    return {
        "id": card_id,
        "verses": verses,
        "title": title,
        "does": does,
        "date_dependent": date_dependent,
        **builder(ctx),
    }


@router.post("/chapter/3")
def chapter_3(body: Ch03In) -> Dict[str, Any]:
    """Every computational verse of Chapter 3, evaluated for one date."""
    try:
        jd = ch01.julian_day(body.year, body.month, float(body.day))
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    ctx = _Ctx(jd=jd, latitude=body.latitude)
    return {
        "chapter": 3,
        "title": CHAPTER_3_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "latitude": body.latitude,
        "order": CARD_ORDER,
        "cards": {c: _build_card(c, ctx) for c in CARD_ORDER},
    }


def _need(value: Any, name: str, card: str) -> Any:
    """Return ``value`` or raise 422 naming the field ``card`` requires."""
    if value is None:
        raise HTTPException(status_code=422, detail=f"{card} needs '{name}'")
    return value


@router.post("/chapter/3/probe")
def chapter_3_probe(body: Ch03ProbeIn) -> Dict[str, Any]:
    """Evaluate one card's slider input against the library.

    Returns the same shape the card ships for its default case, so the React
    card can swap the probe's answer in without reshaping it.
    """
    card = body.card
    if card == "iii.1-4":
        return _direction(
            _need(body.x1, "x1", card), _need(body.y1, "y1", card),
            _need(body.x2, "x2", card), _need(body.y2, "y2", card),
            _need(body.noon_shadow_direction, "noon_shadow_direction", card),
        )
    if card == "iii.5-8":
        return _gnomon(_need(body.altitude, "altitude", card))
    if card == "iii.13-17":
        return _latitude_from_shadow(
            _need(body.shadow, "shadow", card),
            _need(body.sun_longitude, "sun_longitude", card),
            _need(body.shadow_direction, "shadow_direction", card),
        )
    if card == "iii.18-20":
        return _equatorial(_need(body.longitude, "longitude", card))
    if card == "iii.21-23":
        return _noon_shadow(
            _need(body.latitude, "latitude", card), _need(body.declination, "declination", card)
        )
    if card == "iii.38-41":
        return _hour_angle(
            _need(body.latitude, "latitude", card),
            _need(body.declination, "declination", card),
            _need(body.hour_angle, "hour_angle", card),
        )
    if card == "iii.42":
        return _cara(
            _need(body.latitude, "latitude", card), _need(body.sun_longitude, "sun_longitude", card)
        )
    if card == "iii.43-44":
        return _rising(_need(body.latitude, "latitude", card))
    raise HTTPException(status_code=422, detail=f"No probe for card '{card}'")
