"""Verse-indexed payloads for the React "Book" page of Chapter 11.

Chapter 11 counterpart of ``book_ch10.py``: for a date and a search window, what
does each computational verse of *Of Certain Malignant Aspects of the Sun and
Moon* yield?

Two patas, Vyatipata (longitude sum 180 deg) and Vaidhrita (sum 360 deg), both
really statements about declination: the sum rule of v.2-3 is only the trigger,
not the substance. Not the nitya-yoga also called Vyatipata (number 17 of 27, in
ch01_mean_motions) -- that yoga is a fixed 13 deg 20' span of the longitude sum
with no declination condition at all, and lasts far longer than the few hours
of a Ch.11 pata.

Laid out: the sum rule (v.2-3), the Moon's declination corrected by her
latitude through the ayana valana and the gata/eshya (already-past or
still-to-come) test it enables (v.7-11), the true instant from equal declinations and
the duration from the difference of the daily motions (v.12-14), and the near-equator case where a
pata can recur or fail to occur, shown through the `refined` flag over the
search window (v.19).

Not laid out: v.4-5 and v.16-18 (poetic description of the pata's character and
effects, nothing to compute), v.11's own equation applied to the Moon's node,
and v.20-23 (a third yoga counted by asterism-portion and the asterism-junction
points to avoid) -- nakshatra matters the library has no function for here.

The library ignores the observer's place for a pata, so none is taken, as in
Chapter 9.

Reference: SS Ch.11 v.2-23; Burgess (1860) pp.281-292
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch11_pata as ch11
from suryasiddhanta._types import PataEvent
from suryasiddhanta.ch03_direction_place_time import declination

from .schemas import Ch11In

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_11_TITLE = "Of certain malignant Aspects of the Sun and Moon"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = ["xi.2-3", "xi.4-11", "xi.12-14", "xi.19"]


@dataclass
class _Ctx:
    """The date and how far ahead the pata search looks."""

    year: int
    month: int
    day: float
    days: int

    @cached_property
    def jd(self) -> float:
        """Julian Day of the date asked for."""
        return ch01.julian_day(self.year, self.month, self.day)

    @cached_property
    def nearest(self) -> Optional[PataEvent]:
        """The next pata at or after the date, within the search window."""
        return ch11.find_next_pata(self.jd, max_days=float(self.days))

    @cached_property
    def events(self) -> List[PataEvent]:
        """Every pata in the search window from the date."""
        return ch11.find_patas(self.jd, self.jd + self.days)


def _date_of(jd: float) -> Dict[str, Any]:
    """Year, month and fractional day of a Julian Day."""
    year, month, day, frac = ch01.from_julian_day(jd)
    return {"year": year, "month": month, "day": day + frac}


def _event(ev: PataEvent) -> Dict[str, Any]:
    """A pata event as a payload dict."""
    return {
        "kind": ev.kind,
        "begin": _date_of(ev.jd_begin),
        "middle": _date_of(ev.jd_middle),
        "end": _date_of(ev.jd_end),
        "duration_ghatis": ev.duration_ghatis,
        "duration_hours": ev.duration_hours,
        "sun_declination": ev.sun_declination,
        "moon_declination": ev.moon_declination,
        "refined": ev.refined,
    }


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_sum_rule(ctx: _Ctx) -> Dict[str, Any]:
    """xi.2-3: the longitude-sum trigger -- 180 deg for Vyatipata, 360 for Vaidhrita."""
    total = ch11.longitude_sum(ctx.jd)
    to_vyatipata = (ch11.VYATIPATA_SUM - total) % 360.0
    to_vaidhrita = (ch11.VAIDHRITA_SUM - total) % 360.0
    return {
        "longitude_sum": total,
        "vyatipata_sum": ch11.VYATIPATA_SUM,
        "vaidhrita_sum": ch11.VAIDHRITA_SUM,
        "degrees_to_vyatipata": to_vyatipata,
        "degrees_to_vaidhrita": to_vaidhrita,
        "next_by_sum_rule": "Vyatipata" if to_vyatipata <= to_vaidhrita else "Vaidhrita",
    }


def _card_declination(ctx: _Ctx) -> Dict[str, Any]:
    """xi.4-11: the Moon's corrected declination, and whether the nearest pata is past or to come.

    v.7-8's gata/eshya rule compares the corrected declinations directly; here
    it is read off ``is_past`` on the nearest event the search already found.
    """
    moon_lon = ch11._tropical_longitude("Moon", ctx.jd)  # noqa: SLF001
    valana = ch11.ayana_valana(moon_lon)
    nearest = ctx.nearest
    return {
        "sun_declination": ch11.sun_declination(ctx.jd),
        "moon_declination": ch11.moon_declination(ctx.jd),
        "moon_declination_plain": declination(moon_lon),
        "moon_latitude_arcmin": ch11.moon_latitude_deg(ctx.jd) * 60.0,
        "ayana_valana": valana,
        "nearest_kind": nearest.kind if nearest else None,
        "is_past": nearest.is_past if nearest else None,
    }


def _card_timing(ctx: _Ctx) -> Dict[str, Any]:
    """xi.12-14: the true instant from equality of declinations, and its half-duration.

    The library's half-duration divides the combined semi-diameters by the
    difference of the Sun's and Moon's daily motions, as v.14 states.
    """
    ev = ctx.nearest
    if ev is None:
        return {"found": False}
    return {"found": True, **_event(ev)}


def _card_events(ctx: _Ctx) -> Dict[str, Any]:
    """xi.19: patas over the window, with the near-equator recur-or-fail case shown by ``refined``."""
    events = [_event(ev) for ev in ctx.events]
    return {
        "days": ctx.days,
        "events": events,
        "unrefined_count": sum(1 for ev in ctx.events if not ev.refined),
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "xi.2-3": (
        "2-3", "The longitude-sum rule",
        "Vyatipata falls where the tropical longitudes sum to 180 degrees, Vaidhrita where they sum to 360.",
        True, _card_sum_rule,
    ),
    "xi.4-11": (
        "4-11", "The Moon's corrected declination",
        "Her declination is corrected by her latitude, resolved along the declination circle through the ayana valana.",
        True, _card_declination,
    ),
    "xi.12-14": (
        "12-14", "The true instant and its duration",
        "The true pata falls where the corrected declinations are equal; its half-duration is the combined semi-diameters over the difference of the daily motions.",
        True, _card_timing,
    ),
    "xi.19": (
        "19", "Twice, or not at all",
        "Near the equator a pata can recur within the same crossing; away from it, the declination condition can fail to be met at all.",
        True, _card_events,
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


@router.post("/chapter/11")
def chapter_11(body: Ch11In) -> Dict[str, Any]:
    """Every computational verse of Chapter 11, for a date and a search window."""
    ctx = _Ctx(year=body.year, month=body.month, day=float(body.day), days=body.days)
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 11,
        "title": CHAPTER_11_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "days": body.days,
        "order": CARD_ORDER,
        "cards": cards,
    }
