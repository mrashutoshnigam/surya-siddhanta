"""Verse-indexed payloads for the React "Book" page of Chapter 7.

Chapter 7 counterpart of ``book_ch04.py``: for a pair of bodies and a date,
what does each computational verse of *Of Planetary Conjunctions* yield? The
React page renders one card per entry of ``CARD_ORDER`` in Burgess's order.

The hand method of v.2-6 (find which way the bodies are drawing, then correct
the time by the gap over the difference of daily motions, and repeat) is laid
out step by step and ends beside the library's bisected conjunction.

Not laid out: v.7-10 (the corrections for meridian distance and declination),
v.13-14 (the diameters of the star-planets) and v.15-18 (the gnomon
construction). The library has no calculation for them; v.13's rule for the
diameters is ambiguous without the Hindi bhashya.

Reference: SS Ch.7 v.1-24; Burgess (1860) pp.221-235
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch02_true_places as ch02
from suryasiddhanta import ch07_conjunctions as ch07

from .schemas import Ch07In

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_7_TITLE = "Of Planetary Conjunctions"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = ["vii.1", "vii.2-3", "vii.4-6", "vii.12", "vii.19-22"]

#: The repetition of v.6 stops once a step moves the time by less than this (days).
_STEP_TOLERANCE_DAYS = 1e-4
_MAX_STEPS = 8
_GHATIS_PER_DAY = 60.0


def daily_motion(planet: str, jd: float) -> float:
    """Signed daily motion of a planet's true longitude, degrees per day.

    A central difference over one day; negative while the planet is
    retrograde. The same quantity the verses call the daily motion.
    """
    return ch07.longitude_difference(
        ch07._planet_lon(planet, jd + 0.5), ch07._planet_lon(planet, jd - 0.5))


def separating(diff: float, relative_speed: float) -> bool:
    """True when the bodies are drawing apart, i.e. the conjunction is past.

    ``diff`` is the first body's longitude less the second's and
    ``relative_speed`` the first's daily motion less the second's. They
    have the same sign exactly when the gap is widening. v.2 and v.3 are
    this rule for two direct bodies and for a direct and a retrograde one.
    """
    return diff * relative_speed > 0.0


def correction_steps(planet1: str, planet2: str, jd0: float) -> List[Dict[str, Any]]:
    """The repeated correction of v.4-6, one dict per step.

    Each step finds the signed longitude gap, divides it by the difference
    of the daily motions, and moves the time by that many days: subtracted
    when the conjunction is past, added when it is to come (v.5). The next
    step starts from the moved time (v.6).
    """
    steps: List[Dict[str, Any]] = []
    jd = jd0
    for _ in range(_MAX_STEPS):
        diff = ch07.longitude_difference(
            ch07._planet_lon(planet1, jd), ch07._planet_lon(planet2, jd))
        rel = daily_motion(planet1, jd) - daily_motion(planet2, jd)
        if abs(rel) < 1e-9:
            break
        move = -diff / rel
        steps.append({
            "jd": jd,
            "gap_arcmin": diff * 60.0,
            "relative_speed": rel,
            "move_days": move,
            "move_ghatis": move * _GHATIS_PER_DAY,
            "rule": "subtract" if move < 0 else "add",
        })
        jd += move
        if abs(move) < _STEP_TOLERANCE_DAYS:
            break
    return steps


@dataclass
class _Ctx:
    """The pair, the date, and the conjunction nearest it."""

    planet1: str
    planet2: str
    year: int
    month: int
    day: float
    search_days: float

    @cached_property
    def jd(self) -> float:
        """Julian Day of the date asked for."""
        return ch01.julian_day(self.year, self.month, self.day)

    @cached_property
    def conjunction(self) -> Optional[ch07.Conjunction]:
        """The library's conjunction nearest the date, or ``None`` in the window."""
        return ch07.nearest_conjunction(
            self.planet1, self.planet2, self.jd, self.search_days)


def _date_of(jd: float) -> Dict[str, Any]:
    """Year, month and fractional day of a Julian Day."""
    year, month, day, frac = ch01.from_julian_day(jd)
    return {"year": year, "month": month, "day": day + frac}


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_who(ctx: _Ctx) -> Dict[str, Any]:
    """vii.1: which bodies can fight, which only meet, and which are lost in the Sun."""
    one, two = ctx.planet1, ctx.planet2
    both = one in ch07.TARAGRAHA and two in ch07.TARAGRAHA
    if both:
        relation = "Two star-planets: encounter (yuddha) or conjunction (samagama)."
    elif "Sun" in (one, two):
        relation = "A planet with the Sun: the planet is set; there is no encounter."
    elif "Moon" in (one, two):
        relation = "A planet with the Moon: conjunction (samagama) only."
    else:
        relation = "Not a distinct pair."
    return {
        "planet1": one, "planet2": two,
        "planet1_taragraha": one in ch07.TARAGRAHA,
        "planet2_taragraha": two in ch07.TARAGRAHA,
        "both_taragraha": both,
        "relation": relation,
    }


def _card_direction(ctx: _Ctx) -> Dict[str, Any]:
    """vii.2-3: is the conjunction past or to come, from the longitudes and the motions."""
    one, two = ctx.planet1, ctx.planet2
    lon1, lon2 = ch07._planet_lon(one, ctx.jd), ch07._planet_lon(two, ctx.jd)
    v1, v2 = daily_motion(one, ctx.jd), daily_motion(two, ctx.jd)
    diff = ch07.longitude_difference(lon1, lon2)
    rel = v1 - v2
    past = separating(diff, rel)
    return {
        "planet1": one, "planet2": two,
        "longitude1": lon1, "longitude2": lon2,
        "gap": diff,
        "motion1": v1, "motion2": v2,
        "retrograde1": v1 < 0, "retrograde2": v2 < 0,
        "relative_speed": rel,
        "swifter": one if abs(v1) > abs(v2) else two,
        "status": "past" if past else "to come",
        "rule": "v.3" if (v1 < 0 or v2 < 0) else "v.2",
    }


def _card_correction(ctx: _Ctx) -> Dict[str, Any]:
    """vii.4-6: the gap over the difference of daily motions, repeated, then the library's answer."""
    steps = correction_steps(ctx.planet1, ctx.planet2, ctx.jd)
    conj = ctx.conjunction
    last = steps[-1] if steps else None
    final_jd = last["jd"] + last["move_days"] if last else None
    return {
        "steps": steps,
        "settled": bool(last) and abs(last["move_days"]) < _STEP_TOLERANCE_DAYS * 10,
        "final_jd": final_jd,
        "final_date": _date_of(final_jd) if final_jd is not None else None,
        "library_jd": conj.jd if conj else None,
        "library_date": _date_of(conj.jd) if conj else None,
        "agrees": bool(conj and final_jd is not None and abs(final_jd - conj.jd) < 0.05),
    }


def _card_latitudes(ctx: _Ctx) -> Dict[str, Any]:
    """vii.12: the two latitudes at the conjunction and the gap between the bodies."""
    conj = ctx.conjunction
    if conj is None:
        return {"found": False}
    lat1 = ch02.planet_latitude(ctx.planet1, conj.jd)
    lat2 = ch02.planet_latitude(ctx.planet2, conj.jd)
    same = lat1 * lat2 > 0
    return {
        "found": True,
        "jd": conj.jd,
        "date": _date_of(conj.jd),
        "latitude1": lat1, "latitude2": lat2,
        "same_direction": same,
        "verse_gap": abs(abs(lat1) - abs(lat2)) if same else abs(lat1) + abs(lat2),
        "library_separation_arcmin": conj.separation_deg * 60.0,
    }


def _card_classification(ctx: _Ctx) -> Dict[str, Any]:
    """vii.19-22: yuddha or samagama by the interval, and the planet that wins."""
    conj = ctx.conjunction
    if conj is None:
        return {"found": False}
    lat1 = ch02.planet_latitude(ctx.planet1, conj.jd)
    lat2 = ch02.planet_latitude(ctx.planet2, conj.jd)
    winner = None
    if conj.conjunction_type == "yuddha":
        winner = ctx.planet1 if lat1 > lat2 else ctx.planet2
    return {
        "found": True,
        "jd": conj.jd,
        "date": _date_of(conj.jd),
        "longitude": conj.longitude,
        "separation_deg": conj.separation_deg,
        "type": conj.conjunction_type,
        "limit_deg": 1.0,
        "winner": winner,
        "north_planet": ctx.planet1 if lat1 > lat2 else ctx.planet2,
        "latitude1": lat1, "latitude2": lat2,
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "vii.1": (
        "1", "Who meets whom",
        "Star-planets may fight or meet each other; with the Moon they meet; with the Sun they are lost.",
        False, _card_who,
    ),
    "vii.2-3": (
        "2-3", "Is the conjunction past or to come",
        "From the longitudes and the direction of motion of the two bodies.",
        True, _card_direction,
    ),
    "vii.4-6": (
        "4-6", "Fixing the time of the conjunction",
        "The gap over the difference of daily motions, subtracted or added, repeated until the bodies are equal.",
        True, _card_correction,
    ),
    "vii.12": (
        "12", "The latitudes at the conjunction",
        "The two latitudes: their difference when alike in direction, their sum when not.",
        True, _card_latitudes,
    ),
    "vii.19-22": (
        "19-22", "Encounter or conjunction",
        "Within a degree the star-planets are in encounter; the northern one is the victor.",
        True, _card_classification,
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


@router.post("/chapter/7")
def chapter_7(body: Ch07In) -> Dict[str, Any]:
    """Every computational verse of Chapter 7, for a pair of bodies near one date."""
    if body.planet1 == body.planet2:
        raise HTTPException(status_code=400, detail="Choose two different bodies.")
    ctx = _Ctx(planet1=body.planet1, planet2=body.planet2, year=body.year,
               month=body.month, day=float(body.day), search_days=body.search_days)
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 7,
        "title": CHAPTER_7_TITLE,
        "jd": jd,
        "pair": [body.planet1, body.planet2],
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "order": CARD_ORDER,
        "cards": cards,
    }
