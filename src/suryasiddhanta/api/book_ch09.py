"""Verse-indexed payloads for the React "Book" page of Chapter 9.

Chapter 9 counterpart of ``book_ch07.py``: for one planet and a date, what
does each computational verse of *Of Heliacal Risings and Settings* yield?

The chapter works in "degrees of time" (kalamsas), the distance from the Sun
measured in oblique ascension. The library applies the same thresholds to the
plain ecliptic elongation instead, a documented deviation, so every
card that uses a threshold says so. The hand method of v.4-5 and v.11 (the
ascensional equivalents of the interval) is therefore not laid out; v.10 is
laid out with the elongation standing in for the kalamsas.

Place plays no part: the library ignores the observer for heliacal events.

Reference: SS Ch.9 v.1-18; Burgess (1860) pp.253-265
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch09_heliacal as ch09

from .book_ch07 import daily_motion
from .schemas import Ch09In

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_9_TITLE = "Of Heliacal Risings and Settings"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = ["ix.2-3", "ix.6-9", "ix.10-11", "ix.6-11", "ix.12-18"]

#: The planets whose motion is slow, so they always follow the first rule of v.2.
_SLOW = {"Mars", "Jupiter", "Saturn"}

#: v.12-15: the stars' distances from the Sun, in degrees of time, by group.
STAR_GROUPS: List[Tuple[int, str, List[str]]] = [
    (13, "12", ["Svati", "Agastya", "Mrigavyadha", "Chitra", "Jyeshtha", "Punarvasu",
                "Abhijit", "Brahmahridaya"]),
    (14, "13", ["Hasta", "Shravana", "Purva Phalguni", "Uttara Phalguni", "Dhanishta",
                "Rohini", "Magha", "Vishakha", "Ashvini"]),
    (15, "14", ["Krittika", "Anuradha", "Mula", "Ashlesha", "Ardra", "Purva Ashadha",
                "Uttara Ashadha"]),
    (21, "15", ["Bharani", "Pushya", "Mrigashira"]),
    (17, "15", ["the remaining asterisms"]),
]

#: v.18: the stars that the Sun's rays never swallow, from their northern situation.
CIRCUMPOLAR_STARS: List[str] = [
    "Abhijit", "Brahmahridaya", "Svati", "Shravana", "Dhanishta", "Uttara Bhadrapada",
]


@dataclass
class _Ctx:
    """The planet, the date, and how far ahead events are searched."""

    planet: str
    year: int
    month: int
    day: float
    months: int

    @cached_property
    def jd(self) -> float:
        """Julian Day of the date asked for."""
        return ch01.julian_day(self.year, self.month, self.day)

    @cached_property
    def elongation(self) -> float:
        """Signed elongation from the Sun in degrees (east positive)."""
        return ch09.sun_elongation(self.planet, self.jd)

    @cached_property
    def retrograde(self) -> bool:
        """Whether the planet's true longitude is decreasing on the date."""
        return ch09._is_retrograde(self.planet, self.jd)

    @cached_property
    def threshold(self) -> float:
        """The visibility threshold that applies on the date (v.6-9)."""
        return ch09._get_threshold(self.planet, self.jd)


def _date_of(jd: float) -> Dict[str, Any]:
    """Year, month and fractional day of a Julian Day."""
    year, month, day, frac = ch01.from_julian_day(jd)
    return {"year": year, "month": month, "day": day + frac}


def _event(ev: ch09.HeliacalEvent) -> Dict[str, Any]:
    """A heliacal event as a payload dict."""
    return {
        "type": ev.event_type, "jd": ev.jd, "date": _date_of(ev.jd),
        "elongation": ev.elongation, "direction": ev.direction,
    }


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_direction(ctx: _Ctx) -> Dict[str, Any]:
    """ix.2-3: whether the planet is heading for a setting or a rising, and on which horizon.

    The slow planets (and Mercury or Venus when retrograding) set in the west
    while their longitude exceeds the Sun's and rise in the east while it is
    less; the swift ones (the direct Mercury and Venus) do the reverse.
    """
    slow = ctx.planet in _SLOW or ctx.retrograde
    east_of_sun = ctx.elongation > 0
    if slow:
        event, horizon = ("setting", "west") if east_of_sun else ("rising", "east")
    else:
        event, horizon = ("rising", "west") if east_of_sun else ("setting", "east")
    return {
        "planet": ctx.planet,
        "elongation": ctx.elongation,
        "greater_than_sun": east_of_sun,
        "retrograde": ctx.retrograde,
        "visible": abs(ctx.elongation) >= ctx.threshold,
        "rule": "slow" if slow else "swift",
        "event": event,
        "horizon": horizon,
    }


def _card_thresholds(ctx: _Ctx) -> Dict[str, Any]:
    """ix.6-9: the threshold table, and whether the planet is visible on the date."""
    rows = [
        {"planet": p, "retrograde": r, "direct": d, "selected": p == ctx.planet}
        for p, (r, d) in ch09.VISIBILITY_THRESHOLDS.items()
    ]
    return {
        "rows": rows,
        "planet": ctx.planet,
        "elongation": ctx.elongation,
        "threshold": ctx.threshold,
        "retrograde": ctx.retrograde,
        "margin": abs(ctx.elongation) - ctx.threshold,
        "visible": ch09.is_planet_visible(ctx.planet, ctx.jd),
    }


def _card_next_event(ctx: _Ctx) -> Dict[str, Any]:
    """ix.10-11: the days to the next event, by the gap over the rate of closing, beside the library's.

    v.10 divides the shortfall from the threshold by the difference of daily
    motions (their sum when retrograding). Here the shortfall is in degrees
    of ecliptic elongation and the rate is the measured daily change of that
    elongation, which is the same difference or sum of motions with the sign
    taken care of. One step only; the library scans and bisects.
    """
    visible = abs(ctx.elongation) >= ctx.threshold
    wanted = "setting" if visible else "rising"
    rate = daily_motion(ctx.planet, ctx.jd) - daily_motion("Sun", ctx.jd)
    # d|elongation|/dt: the elongation's own sign decides which way it grows.
    closing = rate if ctx.elongation >= 0 else -rate
    shortfall = abs(ctx.elongation) - ctx.threshold
    hand_days: Optional[float] = None
    if visible and closing < 0:
        hand_days = shortfall / -closing
    elif not visible and closing > 0:
        hand_days = -shortfall / closing
    library = ch09.next_heliacal(ctx.planet, ctx.jd, wanted)
    return {
        "event": wanted,
        "elongation": ctx.elongation,
        "threshold": ctx.threshold,
        "shortfall_arcmin": shortfall * 60.0,
        "planet_motion": daily_motion(ctx.planet, ctx.jd),
        "sun_motion": daily_motion("Sun", ctx.jd),
        "closing_rate": closing,
        "hand_days": hand_days,
        "hand_date": _date_of(ctx.jd + hand_days) if hand_days is not None else None,
        "library": _event(library) if library else None,
        "days_apart": (
            abs(hand_days - (library.jd - ctx.jd))
            if hand_days is not None and library else None
        ),
    }


def _card_events(ctx: _Ctx) -> Dict[str, Any]:
    """ix.6-11: every rising and setting in the months from the date, from the library."""
    jd_year = ch01.julian_day(ctx.year, 1, 1.0)
    # visibility_events counts months from 1 January; widen to reach the date's own.
    offset_months = int((ctx.jd - jd_year) / 30.44) + 1
    events = ch09.visibility_events(ctx.planet, ctx.year, offset_months + ctx.months)
    return {
        "planet": ctx.planet,
        "months": ctx.months,
        "events": [_event(e) for e in events if e.jd >= ctx.jd],
    }


def _card_stars(_ctx: _Ctx) -> Dict[str, Any]:
    """ix.12-18: the fixed stars' limits of visibility and the ones never extinguished."""
    return {
        "groups": [
            {"degrees": deg, "verse": verse, "stars": stars}
            for deg, verse, stars in STAR_GROUPS
        ],
        "circumpolar": CIRCUMPOLAR_STARS,
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "ix.2-3": (
        "2-3", "Which way the planet is heading",
        "Whether it is about to set or rise, and in the west or the east, from where it stands against the Sun.",
        True, _card_direction,
    ),
    "ix.6-9": (
        "6-9", "The limits of visibility",
        "Each planet is lost when nearer the Sun than its limit, and seen again beyond it.",
        True, _card_thresholds,
    ),
    "ix.10-11": (
        "10-11", "The time to the next event",
        "The shortfall from the limit over the daily motions gives the days to the setting or rising.",
        True, _card_next_event,
    ),
    "ix.6-11": (
        "6-11", "Risings and settings ahead",
        "Every rising and setting the library finds in the months after the date.",
        True, _card_events,
    ),
    "ix.12-18": (
        "12-18", "The fixed stars",
        "The stars' own limits of visibility, and the stars the Sun's rays never reach.",
        False, _card_stars,
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


@router.post("/chapter/9")
def chapter_9(body: Ch09In) -> Dict[str, Any]:
    """Every computational verse of Chapter 9, for one planet and a date."""
    ctx = _Ctx(planet=body.planet, year=body.year, month=body.month,
               day=float(body.day), months=body.months)
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 9,
        "title": CHAPTER_9_TITLE,
        "jd": jd,
        "planet": body.planet,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "order": CARD_ORDER,
        "cards": cards,
    }
