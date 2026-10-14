"""Verse-indexed payloads for the React "Book" page of Chapter 10.

Chapter 10 counterpart of ``book_ch09.py``: for a date and a place, what does
each computational verse of *Of the Moon's Rising and Setting, and of her
Cusps* yield?

Laid out: the Moon's limit of visibility (v.1), her rising and setting from
the library, the illuminated part (v.9 and v.16, linear in the elongation as
the verse states it, beside the versine width of the bhashya), and the figure
of v.10-14 as the library's bright-limb and horn angles.

Not laid out: v.2-5 (the moon's setting after the sun, by repeated
respirations) and v.6-8 (the elevation of the cusps from the declinations and
the shadow). The library has no function for them.

Reference: SS Ch.10 v.1-16; Burgess (1860) pp.266-280
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch10_lunar_horns as ch10

from .schemas import Ch10In

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_10_TITLE = "Of the Moon's Rising and Setting, and of her Cusps"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = ["x.1", "x.2-5", "x.9", "x.10-14"]

#: v.1: the Moon is seen at this distance from the Sun, in degrees of time.
VISIBILITY_LIMIT_DEGREES = 12.0

#: How many days the figure card shows, counting the date itself.
_STRIP_DAYS = 8


@dataclass
class _Ctx:
    """The date and the observer."""

    year: int
    month: int
    day: float
    latitude: float
    longitude: float

    @cached_property
    def jd(self) -> float:
        """Julian Day of the date asked for."""
        return ch01.julian_day(self.year, self.month, self.day)

    @cached_property
    def elongation(self) -> float:
        """The Moon's elongation from the Sun, 0 to 360 degrees."""
        return ch10.moon_elongation(self.jd)


def _date_of(jd: float) -> Dict[str, Any]:
    """Year, month and fractional day of a Julian Day."""
    year, month, day, frac = ch01.from_julian_day(jd)
    return {"year": year, "month": month, "day": day + frac}


def _crescent(jd: float, latitude: float, longitude: float) -> Dict[str, Any]:
    """The figure's inputs for one instant.

    ``sun_angle`` is the direction of the Sun from the Moon as the observer
    sees it, measured from the top of the view round to the right: the
    library's horn axis is perpendicular to the bright limb, so the bright
    limb lies at ``horn_angle - 90``.
    """
    elongation = ch10.moon_elongation(jd)
    horn = ch10.horn_angle(jd, latitude, longitude)
    return {
        "jd": jd,
        "date": _date_of(jd),
        "elongation": elongation,
        "waxing": elongation < 180.0,
        "phase": ch10.phase_name(jd),
        "fraction": ch10.illuminated_fraction(jd),
        "width_arcmin": ch10.crescent_width(jd),
        "bright_limb_angle": ch10.bright_limb_angle(jd),
        "horn_angle": horn,
        "sun_angle": (horn - 90.0) % 360.0,
    }


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_visibility(ctx: _Ctx) -> Dict[str, Any]:
    """x.1: the Moon is seen beyond twelve degrees of time from the Sun."""
    distance = min(ctx.elongation, 360.0 - ctx.elongation)
    waxing = ctx.elongation < 180.0
    return {
        "elongation": ctx.elongation,
        "distance": distance,
        "limit": VISIBILITY_LIMIT_DEGREES,
        "visible": distance >= VISIBILITY_LIMIT_DEGREES,
        "waxing": waxing,
        "horizon": "west, after sunset" if waxing else "east, before sunrise",
    }


def _card_rise_set(ctx: _Ctx) -> Dict[str, Any]:
    """x.2-5: the library's next moonrise and moonset at the place."""
    rise = ch10.moonrise(ctx.jd, ctx.latitude, ctx.longitude)
    set_ = ch10.moonset(ctx.jd, ctx.latitude, ctx.longitude)
    return {
        "latitude": ctx.latitude,
        "longitude": ctx.longitude,
        "rise": _date_of(rise) if rise is not None else None,
        "set": _date_of(set_) if set_ is not None else None,
    }


def _card_illumination(ctx: _Ctx) -> Dict[str, Any]:
    """x.9: the illuminated part, in digits of the twelve-digit disc.

    The elongation in minutes divided by 900 gives the lit digits when the
    Moon is under half a revolution from the Sun; past that v.16 applies the
    rule to the elongation's complement of a full circle. The verse is
    linear, so the lit fraction is the library's; the versine width of the
    bhashya is the width of the crescent along the Moon's axis.
    """
    reflected = ctx.elongation if ctx.elongation <= 180.0 else 360.0 - ctx.elongation
    minutes = reflected * 60.0
    digits = minutes / 900.0
    return {
        "elongation": ctx.elongation,
        "paksha": "light half (shukla)" if ctx.elongation < 180.0 else "dark half (krishna)",
        "reflected_elongation": reflected,
        "minutes": minutes,
        "lit_digits": digits,
        "fraction": digits / 12.0,
        "library_fraction": ch10.illuminated_fraction(ctx.jd),
        "phase": ch10.phase_name(ctx.jd),
        "width_arcmin": ch10.crescent_width(ctx.jd),
        "moon_radius_arcmin": ch10.MOON_APPARENT_RADIUS,
    }


def _card_figure(ctx: _Ctx) -> Dict[str, Any]:
    """x.10-14: the Moon as drawn, for the date and for the week after it."""
    return {
        "latitude": ctx.latitude,
        "longitude": ctx.longitude,
        "now": _crescent(ctx.jd, ctx.latitude, ctx.longitude),
        "strip": [
            _crescent(ctx.jd + k, ctx.latitude, ctx.longitude) for k in range(_STRIP_DAYS)
        ],
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "x.1": (
        "1", "When the Moon is seen",
        "She is seen in the west, or lost in the east, at twelve degrees of time from the Sun.",
        True, _card_visibility,
    ),
    "x.2-5": (
        "2-5", "Moonrise and moonset",
        "When the Moon next rises and sets at the place, from the library.",
        True, _card_rise_set,
    ),
    "x.9": (
        "9", "The illuminated part",
        "The elongation in minutes over nine hundred gives the lit digits of the twelve-digit disc.",
        True, _card_illumination,
    ),
    "x.10-14": (
        "10-14", "The figure of the Moon",
        "The lit part of the disc and the tilt of the cusps, as the observer would see them.",
        True, _card_figure,
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


@router.post("/chapter/10")
def chapter_10(body: Ch10In) -> Dict[str, Any]:
    """Every computational verse of Chapter 10, for a date and a place."""
    ctx = _Ctx(year=body.year, month=body.month, day=float(body.day),
               latitude=body.latitude, longitude=body.longitude)
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 10,
        "title": CHAPTER_10_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "order": CARD_ORDER,
        "cards": cards,
    }
