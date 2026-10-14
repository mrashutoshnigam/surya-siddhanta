"""Verse-indexed payloads for the React "Book" page of Chapter 13.

Chapter 13 counterpart of ``book_ch12.py``: for a date, a place and a gnomon
reading, what does each computational verse of *Of the Armillary Sphere and
other Instruments* yield?

This is geometry, not ephemeris: the hoops and signs are fixed by the text (the
stellar hoops' declinations drift with the date, but this card reports only how
many there are), and only the lagnas (v.13-14), the Sun's sines (v.14-15) and the time-finding card
(v.20-24) move with the moment. The 3D sphere itself lives on the Instruments
page; the cards here give the numbers behind it.

Laid out: the hoops (v.4-9), the equinoxes, solstices and sign points with the
chord of thirty (v.10-11), the three lagnas and the Sun (v.13-14), the sines
and the pole's raising (v.14-15), and the instruments for time with the
clepsydra (v.20-24). The time card feeds one moment to all four instruments so
they can be seen to agree. Only the gnomon is the text's own; the wheel, arc and
staff come from Burgess's notes (``source`` says which), and so does the
clepsydra's dimension.

Not laid out: v.1-3, 16-19 and 21-22 (the building and care of the sphere, the
seven sages), nothing to compute.

Reference: SS Ch.13 v.4-24; Burgess (1860) pp.297-310
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch13_instruments as ch13

from .schemas import Ch13In

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_13_TITLE = "Of the Armillary Sphere and other Instruments"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER = ["xiii.4-9", "xiii.10-11", "xiii.13-14", "xiii.14-15", "xiii.20-24"]


@dataclass
class _Ctx:
    """The date, the place and the gnomon reading."""

    year: int
    month: int
    day: float
    latitude: float
    longitude: float
    shadow: float
    forenoon: bool

    @cached_property
    def jd(self) -> float:
        """Julian Day of the date asked for."""
        return ch01.julian_day(self.year, self.month, self.day)

    @cached_property
    def sphere(self) -> Any:
        """The armillary sphere for the moment and place."""
        return ch13.armillary_sphere(self.jd, self.latitude, self.longitude)


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_hoops(ctx: _Ctx) -> Dict[str, Any]:
    """xiii.4-9: the great circles, the Sun's six diurnal hoops and the stellar hoops."""
    hoops = ch13.great_hoops() + ch13.solar_diurnal_hoops() + ch13.star_diurnal_hoops(ctx.jd)
    stars: Dict[str, int] = {}
    for h in hoops:
        if h.kind == "star_diurnal":
            stars[h.group] = stars.get(h.group, 0) + 1
    return {
        "great": [
            {"key": h.key, "name": h.name, "verse": h.verse, "note": h.note}
            for h in hoops if h.kind == "great"
        ],
        "solar": [
            {"key": h.key, "name": h.name, "declination": h.declination, "day_radius": h.day_radius}
            for h in hoops if h.kind == "solar_diurnal"
        ],
        "stars": stars,
    }


def _card_points(ctx: _Ctx) -> Dict[str, Any]:
    """xiii.10-11: the equinoxes, solstices and twelve sign points, and the chord of thirty."""
    return {
        "cardinal": [p.to_dict() for p in ch13.cardinal_points()],
        "signs": [p.to_dict() for p in ch13.ecliptic_sign_points()],
        "chord_of_thirty": ch13.chord_of_thirty(),
    }


def _card_lagnas(ctx: _Ctx) -> Dict[str, Any]:
    """xiii.13-14: the orient, occident and meridian ecliptic points, and the Sun."""
    return {
        "lst_deg": ctx.sphere.lst_deg,
        "ayanamsha": ctx.sphere.ayanamsha,
        "points": [p.to_dict() for p in ctx.sphere.points],
    }


def _card_sines(ctx: _Ctx) -> Dict[str, Any]:
    """xiii.14-15: the sines for the Sun's declination, and the pole raised by the latitude."""
    return {
        "sun_declination": ch13.sun_declination(ctx.jd),
        "sines": ctx.sphere.sines,
        "pole_altitude": ctx.sphere.pole_altitude,
    }


def _card_time(ctx: _Ctx) -> Dict[str, Any]:
    """xiii.20-24: the four instruments read at one moment, and the clepsydra's day.

    The gnomon's shadow fixes the moment. The wheel and arc are read at the
    altitude it implies, and the staff is shown the chord that time would
    give. An impossible reading (a shadow shorter than the Sun's noon shadow,
    or a Sun that does not rise and set) is reported as ``found: False``.
    """
    clepsydra = ch13.clepsydra_day(ctx.jd, ctx.latitude)
    try:
        nara = ch13.nara_yantra_time(ctx.shadow, ctx.jd, ctx.latitude, forenoon=ctx.forenoon)
        altitude = nara.sun_altitude_deg
        span = nara.ghatis_since_sunrise if ctx.forenoon else nara.ghatis_to_sunset
        chord = ch13.yashti_chord(span, ctx.jd, ctx.latitude)
        times = [
            nara,
            ch13.cakra_time(altitude, ctx.jd, ctx.latitude, ctx.forenoon),
            ch13.dhanus_time(altitude, ctx.jd, ctx.latitude, ctx.forenoon),
            ch13.yashti_time(chord, ctx.jd, ctx.latitude, ctx.forenoon),
        ]
    except ValueError as exc:
        return {"found": False, "reason": str(exc), "clepsydra": clepsydra}
    return {
        "found": True,
        "shadow": ctx.shadow,
        "forenoon": ctx.forenoon,
        "instruments": [t.to_dict() for t in times],
        "clepsydra": clepsydra,
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "xiii.4-9": (
        "4-9", "The hoops of the sphere",
        "Equator, ecliptic and colures are great hoops; the Sun has a diurnal hoop at each sign boundary, and the stars one each.",
        False, _card_hoops,
    ),
    "xiii.10-11": (
        "10-11", "Equinoxes, solstices and the signs",
        "The equinoxes lie where the equator meets the equinoctial colure, the solstices 24 degrees off it; the chord of thirty degrees divides the ecliptic into signs.",
        False, _card_points,
    ),
    "xiii.13-14": (
        "13-14", "The three lagnas",
        "The orient point is the ecliptic point on the eastern horizon, the occident point on the western, and the meridian point at mid-heaven.",
        True, _card_lagnas,
    ),
    "xiii.14-15": (
        "14-15", "The sines and the raised pole",
        "The earth-sine, day-radius and ascensional-difference sine follow from the Sun's declination; the pole stands above the horizon by the latitude.",
        True, _card_sines,
    ),
    "xiii.20-24": (
        "20-24", "Time from the instruments",
        "The gnomon's shadow gives the Sun's altitude and so the time; the wheel, arc and staff of the commentary give the same time by their own measures. The clepsydra sinks sixty times a day.",
        True, _card_time,
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


@router.post("/chapter/13")
def chapter_13(body: Ch13In) -> Dict[str, Any]:
    """Every computational verse of Chapter 13, for a date, a place and a gnomon reading."""
    ctx = _Ctx(
        year=body.year, month=body.month, day=float(body.day),
        latitude=body.latitude, longitude=body.longitude,
        shadow=body.shadow, forenoon=body.forenoon,
    )
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 13,
        "title": CHAPTER_13_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "latitude": body.latitude,
        "longitude": body.longitude,
        "shadow": body.shadow,
        "forenoon": body.forenoon,
        "order": CARD_ORDER,
        "cards": cards,
    }
