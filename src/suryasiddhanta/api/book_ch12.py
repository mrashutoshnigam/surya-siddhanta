"""Verse-indexed payloads for the React "Book" page of Chapter 12.

Chapter 12 counterpart of ``book_ch11.py``: for a date and a place, what does
each computational verse of *Cosmogony, Geography, and Dimensions of the
Creation* yield?

Unlike Chapters 1-11 this chapter states fixed dimensions, so most cards do not
move with the date. Only the regents (v.78-79) and the position in Brahma's day
(v.74) depend on it, and only the sphere's aspect (v.42-44) and the earth card
(v.59-61, resting on i.59-61) depend on the place. Each card says which.

Laid out, as compound cards that gather a verse range: the sphere's aspect at a
latitude, the earth's circumference with the polar-day limit and the desantara
of the place, the invisibility parallels and the overhead band, the cities'
clock, the days of the gods, manes and Brahma, the regents, and the table of
orbits. Orbits are reckoned per kalpa, not per mahayuga.

Not laid out: the creation narrative, the elements, the patalas and Maya's nine
questions (descriptive, nothing to compute; they live in
``data/cosmography_catalog.json``), and v.91 onward, which describe rather than
measure.

Reference: SS Ch.12 v.42-90, i.59-61; Burgess (1860) pp.293-332
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch12_cosmography as ch12

from .schemas import Ch12In

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_12_TITLE = "Cosmogony, Geography, and Dimensions of the Creation"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER = [
    "xii.42-44", "xii.59-61", "xii.63-68", "xii.70-71", "xii.74", "xii.78-79", "xii.80-90",
]

#: The place whose local noon the cities' clock is read from.
CLOCK_ANCHOR = "Ujjayini"


@dataclass
class _Ctx:
    """The date and the place asked for."""

    year: int
    month: int
    day: float
    latitude: float
    longitude: float

    @cached_property
    def jd(self) -> float:
        """Julian Day of the date asked for."""
        return ch01.julian_day(self.year, self.month, self.day)


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_sphere(ctx: _Ctx) -> Dict[str, Any]:
    """xii.42-44: how the sphere of the asterisms turns at the place's latitude."""
    return ch12.sphere_aspect(ctx.latitude)


def _card_earth(ctx: _Ctx) -> Dict[str, Any]:
    """xii.59-61: circumference, declination in yojanas, polar-day limit and desantara.

    The corrected circumference and the desantara are SS i.60-61, which Ch.12
    v.59-69 cannot work without. The desantara is measured from the meridian of
    Lanka (longitude zero in the library), and the correction is shown for the
    Moon's daily motion.
    """
    return {
        "latitude": ctx.latitude,
        "longitude": ctx.longitude,
        "circumference": ch12.earth_circumference(),
        "obliquity": ch12.OBLIQUITY_DEGREES,
        "obliquity_yojanas": ch12.yojanas_from_declination(ch12.OBLIQUITY_DEGREES),
        "polar_day_limit": ch12.polar_day_limit(),
        "corrected_circumference": ch12.corrected_circumference(ctx.latitude),
        "desantara_yojanas": ch12.desantara_yojanas(ctx.latitude, ctx.longitude),
        "moon_daily_arcmin": ch12.daily_motion_arcmin("Moon"),
        "moon_correction_arcmin": ch12.desantara_correction(
            ch12.daily_motion_arcmin("Moon"), ctx.latitude, ctx.longitude
        ),
    }


def _card_limits(ctx: _Ctx) -> Dict[str, Any]:
    """xii.63-68: the parallels beyond which the Sun is lost for signs, and the overhead band."""
    return {
        "limits": ch12.invisibility_limits(),
        "overhead_band": ch12.solar_overhead_band(),
    }


def _card_clock(ctx: _Ctx) -> Dict[str, Any]:
    """xii.70-71: the local hour at each reference place when it is noon at Ujjayini."""
    hours = ch12.cities_clock(CLOCK_ANCHOR, 12.0)
    places = {p.name: p for p in ch12.reference_places()}
    return {
        "anchor": CLOCK_ANCHOR,
        "anchor_hour": 12.0,
        "hours": [
            {"name": name, "iast": places[name].iast, "longitude": places[name].longitude, "hour": hour}
            for name, hour in hours.items()
        ],
    }


def _card_days(ctx: _Ctx) -> Dict[str, Any]:
    """xii.74: the day of the gods, of the manes and of Brahma, and where the date falls in Brahma's."""
    return {
        "day_of_the_gods": ch12.day_of_the_gods(),
        "day_of_the_manes": ch12.day_of_the_manes(),
        "day_of_brahma": ch12.day_of_brahma(),
        "brahma": ch12.brahma_day_elapsed(ctx.jd),
    }


def _card_regents(ctx: _Ctx) -> Dict[str, Any]:
    """xii.78-79: regents of the day, month and year, and the lords of the day's twenty-four horas."""
    return {
        "day": ch12.regent_of_day(ctx.jd),
        "month": ch12.regent_of_month(ctx.jd),
        "year": ch12.regent_of_year(ctx.jd),
        "horas": [ch12.hora_lord(ctx.jd, h) for h in range(ch12.HORAS_PER_DAY)],
        "order": ch12.REGENT_ORDER,
    }


def _card_orbits(ctx: _Ctx) -> Dict[str, Any]:
    """xii.80-90: every planet covers the same distance in a kalpa, so orbits scale with period."""
    return {
        "daily_linear_motion": ch12.daily_linear_motion(),
        "ether_orbit": ch12.ETHER_ORBIT_YOJANAS,
        "orbits": [
            {**info.to_dict(), "stated_difference": info.stated_difference}
            for info in ch12.all_orbits()
        ],
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "xii.42-44": (
        "42-44", "How the sphere turns at a latitude",
        "The pole stands above the horizon by the latitude; at the equator the asterisms pass overhead, at a pole they circle the horizon.",
        False, _card_sphere,
    ),
    "xii.59-61": (
        "59-61", "The earth, its parallel and the polar day",
        "The circumference is the diameter times the root of ten; the declination in yojanas, taken from a quarter of it, gives the parallel of the sixty-nadi day. Desantara is the place's distance from Lanka's meridian.",
        False, _card_earth,
    ),
    "xii.63-68": (
        "63-68", "Where the Sun is lost, and where he is overhead",
        "The same subtraction at one and two signs of longitude gives the parallels beyond which the Sun is unseen for whole signs; a fifteenth of the circumference is the band he crosses overhead.",
        False, _card_limits,
    ),
    "xii.70-71": (
        "70-71", "The cities' clock",
        "The four cities stand a quadrant apart on the equator: when the Sun is overhead at one he is rising at the next, at midnight at the third.",
        False, _card_clock,
    ),
    "xii.74": (
        "74", "The days of the gods, the manes and Brahma",
        "The gods' day and night are a year, the manes' a lunar month, and Brahma's an aeon of 4,320,000,000 years.",
        True, _card_days,
    ),
    "xii.78-79": (
        "78-79", "The regents of day, month and year",
        "Counting downward from Saturn: the fourth is the day's regent, the third the year's, and from the Moon upward the month's.",
        True, _card_regents,
    ),
    "xii.80-90": (
        "80-90", "The orbits of the planets",
        "Every planet covers the same distance in a kalpa, so each orbit is proportional to its period; the Moon's 324,000 yojanas fixes the scale.",
        False, _card_orbits,
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


@router.post("/chapter/12")
def chapter_12(body: Ch12In) -> Dict[str, Any]:
    """Every computational verse of Chapter 12, for a date and a place."""
    ctx = _Ctx(
        year=body.year, month=body.month, day=float(body.day),
        latitude=body.latitude, longitude=body.longitude,
    )
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 12,
        "title": CHAPTER_12_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "latitude": body.latitude,
        "longitude": body.longitude,
        "order": CARD_ORDER,
        "cards": cards,
    }
