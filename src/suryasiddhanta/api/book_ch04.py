"""Verse-indexed payloads for the React "Book" page of Chapter 4.

Chapter 4 counterpart of ``book_ch02.py``: for the full moon nearest a date,
what does each computational verse of *Of Lunar Eclipses* yield? The React
page renders one card per entry of ``CARD_ORDER`` in Burgess's order.

No astronomy lives here beyond the verses' own formulas. ``_geometry``
decomposes v.10-13 (half-sum of the disks, obscuration, the two square roots
over the relative daily motion); tests pin its output to
``ch04.compute_lunar_eclipse``. Verses 8 (node correction), 15 (iteration)
and 17-26 have no library function and are not laid out.

Verse numbers follow Burgess as read from the corpus.

Reference: SS Ch.4 v.1-26; Burgess (1860) pp.130-170
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch02_true_places as ch02
from suryasiddhanta import ch04_lunar_eclipses as ch04

from .schemas import Ch04In, Ch04ProbeIn

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_4_TITLE = "Of Eclipses, and especially of Lunar Eclipses"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = ["iv.1-2", "iv.4-5", "iv.7-8", "iv.10-11", "iv.12-13"]

_MINUTES_PER_GHATI = 24.0


@dataclass
class _Ctx:
    """The date guess and everything derived once from the nearest full moon."""

    year: int
    month: int
    day: float

    @cached_property
    def full_moon_day(self) -> float:
        """The refined (fractional) day of the full moon, as ``find_full_moon`` gives it."""
        return ch04.find_full_moon(self.year, self.month, self.day)

    @cached_property
    def jd(self) -> float:
        """Julian Day of that full moon."""
        return ch01.julian_day(self.year, self.month, self.full_moon_day)

    @cached_property
    def sun(self) -> float:
        """True longitude of the Sun at the full moon."""
        return ch02.compute("Sun", self.year, self.month, self.full_moon_day).true_longitude

    @cached_property
    def moon(self) -> float:
        """True longitude of the Moon at the full moon."""
        return ch02.compute("Moon", self.year, self.month, self.full_moon_day).true_longitude

    @cached_property
    def node(self) -> float:
        """Longitude of the Moon's node at the full moon."""
        return ch01.moon_node_longitude(self.jd)


def _ghatis(minutes: Optional[float]) -> Optional[float]:
    """Minutes of time as ghatis (24 minutes each); ``None`` passes through."""
    return None if minutes is None else minutes / _MINUTES_PER_GHATI


def _geometry(moon_diameter: float, shadow_diameter: float, latitude: float) -> Dict[str, Any]:
    """The eclipse test and durations of v.10-13 for two disks and a latitude.

    All lengths are arcminutes. Half the sum of the disks less the latitude
    is the amount obscured (v.10); the eclipse is total when the latitude is
    below half their difference (v.11). The half-duration and half-totality
    are the square roots of the squares of the half-sum / half-difference less
    the square of the latitude (v.12), over the relative daily motion of Moon
    and Sun (v.13). A latitude at or beyond the half-sum is "none".
    """
    moon_r = moon_diameter / 2.0
    shadow_r = shadow_diameter / 2.0
    abs_lat = abs(latitude)
    half_sum = moon_r + shadow_r
    half_difference = shadow_r - moon_r
    speed = ch04.RELATIVE_DAILY_MOTION_DEG * 60.0 / 1440.0

    out: Dict[str, Any] = {
        "moon_diameter": moon_diameter,
        "shadow_diameter": shadow_diameter,
        "latitude": latitude,
        "half_sum": half_sum,
        "half_difference": half_difference,
        "obscured": half_sum - abs_lat,
        "speed_arcmin_per_min": speed,
        "eclipse_type": "none",
        "magnitude": 0.0,
        "root_sum": None,
        "root_difference": None,
        "half_duration_min": None,
        "half_duration_ghatis": None,
        "totality_half_min": None,
        "totality_half_ghatis": None,
    }
    if abs_lat >= half_sum:
        return out

    root_sum = math.sqrt(max(0.0, half_sum ** 2 - abs_lat ** 2))
    out["eclipse_type"] = "total" if abs_lat < half_difference else "partial"
    out["magnitude"] = (half_sum - abs_lat) / (2.0 * moon_r) if moon_r > 0 else 0.0
    out["root_sum"] = root_sum
    out["half_duration_min"] = root_sum / speed
    out["half_duration_ghatis"] = _ghatis(out["half_duration_min"])

    disc = half_difference ** 2 - abs_lat ** 2
    if out["eclipse_type"] == "total" and disc > 0:
        out["root_difference"] = math.sqrt(disc)
        out["totality_half_min"] = out["root_difference"] / speed
        out["totality_half_ghatis"] = _ghatis(out["totality_half_min"])
    return out


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_diameters(ctx: _Ctx) -> Dict[str, Any]:
    """iv.1-2: the true diameters in yojanas and the apparent ones in arcminutes."""
    moon_mean = ch04.APPARENT_DIAMETER_ARCMIN["Moon"]
    moon_now = ch04.apparent_diameter_moon(ctx.jd)
    return {
        "sun_yojana": ch04.SUN_DIAMETER_YOJANA,
        "moon_yojana": ch04.MOON_DIAMETER_YOJANA,
        "earth_yojana": ch04.EARTH_DIAMETER_YOJANA,
        "yojana_per_arcmin": ch04.YOJANA_PER_ARCMIN,
        "sun_mean_arcmin": ch04.APPARENT_DIAMETER_ARCMIN["Sun"],
        "moon_mean_arcmin": moon_mean,
        "sun_arcmin": ch04.apparent_diameter_sun(ctx.jd),
        "moon_arcmin": moon_now,
        "moon_ratio": moon_now / moon_mean,
    }


def _card_shadow(ctx: _Ctx) -> Dict[str, Any]:
    """iv.4-5: the earth's shadow at the Moon's distance, by the suci rule."""
    earth = ch04.EARTH_DIAMETER_YOJANA
    sun = ch04.SUN_DIAMETER_YOJANA
    moon = ch04.MOON_DIAMETER_YOJANA
    difference = sun - earth
    correction = difference * moon / sun
    shadow_yojana = earth - correction
    return {
        "earth_yojana": earth,
        "sun_yojana": sun,
        "moon_yojana": moon,
        "difference": difference,
        "correction": correction,
        "shadow_yojana": shadow_yojana,
        "shadow_arcmin": shadow_yojana / ch04.YOJANA_PER_ARCMIN,
        "library_arcmin": ch04.earth_shadow_diameter(ctx.jd),
    }


def _card_opposition(ctx: _Ctx) -> Dict[str, Any]:
    """iv.7-8: the moment the Moon stands opposite the Sun, and the node's place."""
    _, sign, deg_in = ch01.rashi_from_longitude(ctx.moon)
    return {
        "day": ctx.full_moon_day,
        "sun": ctx.sun,
        "moon": ctx.moon,
        "moon_rashi": f"{sign} {deg_in:.2f}°",
        "elongation": (ctx.moon - ctx.sun) % 360.0,
        "node": ctx.node,
        "moon_minus_node": (ctx.moon - ctx.node) % 360.0,
    }


def _card_obscuration(ctx: _Ctx) -> Dict[str, Any]:
    """iv.10-11: the Moon's latitude, the half-sum of the disks, and the verdict."""
    latitude = ch04.moon_latitude(ctx.moon, ctx.node)
    return {
        "moon_longitude": ctx.moon,
        "node_longitude": ctx.node,
        **_geometry(ch04.apparent_diameter_moon(ctx.jd),
                    ch04.earth_shadow_diameter(ctx.jd), latitude),
    }


def _card_duration(ctx: _Ctx) -> Dict[str, Any]:
    """iv.12-13: the two square roots, and the half-duration and half-totality."""
    latitude = ch04.moon_latitude(ctx.moon, ctx.node)
    return _geometry(ch04.apparent_diameter_moon(ctx.jd),
                     ch04.earth_shadow_diameter(ctx.jd), latitude)


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "iv.1-2": (
        "1-2", "The diameters of the Sun and Moon",
        "The true diameters in yojanas, and the apparent ones, the Moon's corrected for her distance.",
        True, _card_diameters,
    ),
    "iv.4-5": (
        "4-5", "The earth's shadow",
        "The earth's diameter less the part lost to the Sun's size, in arcminutes at the Moon.",
        True, _card_shadow,
    ),
    "iv.7-8": (
        "7-8", "The moment of opposition",
        "The full moon nearest the date: the Sun and Moon opposite, and where the node stands.",
        True, _card_opposition,
    ),
    "iv.10-11": (
        "10-11", "The amount obscured",
        "Half the sum of the disks, less the Moon's latitude: total, partial, or no eclipse.",
        True, _card_obscuration,
    ),
    "iv.12-13": (
        "12-13", "The half-duration and half-totality",
        "The square roots of the half-sum and half-difference squared, less latitude squared, over the daily motion.",
        True, _card_duration,
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


@router.post("/chapter/4")
def chapter_4(body: Ch04In) -> Dict[str, Any]:
    """Every computational verse of Chapter 4, for the full moon nearest one date."""
    ctx = _Ctx(year=body.year, month=body.month, day=float(body.day))
    try:
        jd = ctx.jd
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 4,
        "title": CHAPTER_4_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "order": CARD_ORDER,
        "cards": {c: _build_card(c, ctx) for c in CARD_ORDER},
    }


@router.post("/chapter/4/probe")
def chapter_4_probe(body: Ch04ProbeIn) -> Dict[str, Any]:
    """Evaluate the eclipse geometry for any two disks and a latitude.

    Both eclipse cards read the same answer, so the card id only selects
    which slice the React card displays; the schema has already validated it.
    """
    return _geometry(body.moon_diameter, body.shadow_diameter, body.latitude_arcmin)
