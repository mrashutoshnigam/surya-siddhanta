"""Verse-indexed payloads for the React "Book" page of Chapter 8.

Chapter 8 counterpart of ``book_ch04.py``: what does each computational verse
of *Of the Stars* yield, and where does one chosen yogatara stand on a date?

The first card derives every polar longitude (dhruvaka) from the verses' own
figures. v.1 says to multiply each asterism's *share* by ten and add the
minutes of the bhogas that went before; v.2-5 give the shares. Each bhoga is
13 deg 20 min (800 minutes), so ``dhruvaka = share x 10 + 800 x (n - 1)``
minutes. Four asterisms are placed by position instead (v.4), and Abhijit
too. The result is checked against the library's catalog.

The corpus export numbers Ch.8 out of step with the verses (its ids after 8.5
carry commentary), so each card says which corpus records hold its text, or
none.

Reference: SS Ch.8 v.1-28; Burgess (1860) pp.236-252
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch07_conjunctions as ch07
from suryasiddhanta import ch08_stars as ch08

from .schemas import Ch08In

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_8_TITLE = "Of the Stars"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = ["viii.1-4", "viii.5-9", "viii.1-9", "viii.14-15"]

#: v.1: one bhoga is 13 deg 20 min, in minutes of arc.
BHOGA_MINUTES = 800

#: The shares (v.2-4 and v.5) of the asterisms that have one, in tens of minutes.
#: Keyed by the asterism's number in the 27-fold division.
SHARES: Dict[int, int] = {
    1: 48, 2: 40, 3: 65, 4: 57, 5: 58, 6: 4, 7: 78, 8: 76, 9: 14,          # v.2
    10: 54, 11: 64, 12: 50, 13: 60, 14: 40, 15: 74, 16: 78, 17: 64,         # v.3
    18: 14, 19: 6, 20: 4,                                                   # v.4
    24: 80, 25: 36, 26: 22, 27: 79,                                         # v.5
}

#: Asterisms placed by position rather than by share (v.4), as (rule, minutes).
#: Minutes are measured from the start of the zodiac.
_POSITIONED: Dict[int, Tuple[str, float]] = {
    21: ("middle of the bhoga of Purva-Ashadha", 19 * BHOGA_MINUTES + BHOGA_MINUTES / 2),
    22: ("end of the bhoga of Uttara-Ashadha", 21 * BHOGA_MINUTES),
    23: ("junction of the third and fourth quarters of Shravana's bhoga",
         21 * BHOGA_MINUTES + 0.75 * BHOGA_MINUTES),
}

#: Abhijit stands at the end of Purva-Ashadha's bhoga (v.4); the library keeps it apart.
ABHIJIT_MINUTES = 20 * BHOGA_MINUTES


def dhruvaka_minutes(number: int) -> Tuple[float, str]:
    """Polar longitude of the asterism with this number, in minutes, and how it is found.

    By v.1 for those with a share; by the position the verse names for the
    four that have none. Raises ``KeyError`` for a number outside 1-27.
    """
    if number in SHARES:
        return SHARES[number] * 10 + BHOGA_MINUTES * (number - 1), "share"
    rule, minutes = _POSITIONED[number]
    return minutes, rule


def _direction(latitude: float) -> str:
    """North/south word for a signed latitude; nothing at zero."""
    return "north" if latitude > 0 else "south" if latitude < 0 else "on the ecliptic"


@dataclass
class _Ctx:
    """The star, the date, the place and the conjunction search."""

    star: str
    planet: str
    year: int
    month: int
    day: float
    months: int
    latitude: float
    longitude: float

    @cached_property
    def jd(self) -> float:
        """Julian Day of the date asked for."""
        return ch01.julian_day(self.year, self.month, self.day)


def _date_of(jd: float) -> Dict[str, Any]:
    """Year, month and fractional day of a Julian Day."""
    year, month, day, frac = ch01.from_julian_day(jd)
    return {"year": year, "month": month, "day": day + frac}


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_longitudes(ctx: _Ctx) -> Dict[str, Any]:
    """viii.1-4: the polar longitudes, derived from the shares and checked against the catalog."""
    rows: List[Dict[str, Any]] = []
    for nak in ch08.NAKSHATRA_DATA:
        minutes, how = dhruvaka_minutes(nak.number)
        share = SHARES.get(nak.number)
        rows.append({
            "number": nak.number,
            "name": nak.name,
            "star": nak.star,
            "share": share,
            "preceding_minutes": BHOGA_MINUTES * (nak.number - 1) if share is not None else None,
            "rule": how,
            "minutes": minutes,
            "degrees": minutes / 60.0,
            "library_degrees": nak.longitude,
            "matches": abs(minutes / 60.0 - nak.longitude) < 0.01,
            "selected": nak.name == ctx.star,
        })
    return {
        "rows": rows,
        "bhoga_minutes": BHOGA_MINUTES,
        "abhijit_degrees": ABHIJIT_MINUTES / 60.0,
        "abhijit_library_degrees": ch08.ABHIJIT.longitude,
    }


def _card_latitudes(ctx: _Ctx) -> Dict[str, Any]:
    """viii.5-9: the latitudes (viksepa), reckoned from each star's point of declination."""
    rows = [{
        "number": nak.number,
        "name": nak.name,
        "star": nak.star,
        "latitude": nak.latitude,
        "direction": _direction(nak.latitude),
        "selected": nak.name == ctx.star,
    } for nak in ch08.NAKSHATRA_DATA]
    rows.append({
        "number": ch08.ABHIJIT.number,
        "name": ch08.ABHIJIT.name,
        "star": ch08.ABHIJIT.star,
        "latitude": ch08.ABHIJIT.latitude,
        "direction": _direction(ch08.ABHIJIT.latitude),
        "selected": False,
    })
    return {"rows": rows}


def _card_position(ctx: _Ctx) -> Dict[str, Any]:
    """viii.1-9 applied: the chosen star's place on the date, and its rising and setting here."""
    pos = ch08.star_position(ctx.star, ctx.jd)
    nak = ch08.get_nakshatra(ctx.star)
    housing = ch08.nakshatra_of(pos.sidereal_lon)
    rs = ch08.star_rise_set(ctx.star, ctx.jd, ctx.latitude, ctx.longitude)
    return {
        "star": nak.star,
        "name": nak.name,
        "deity": nak.deity,
        "sidereal_lon": pos.sidereal_lon,
        "sidereal_lat": pos.sidereal_lat,
        "ayanamsha": pos.ayanamsha_val,
        "tropical_lon": pos.tropical_lon,
        "right_ascension": pos.right_ascension,
        "declination": pos.declination_val,
        "bhoga_of": housing.name,
        "circumpolar": rs.is_circumpolar,
        "never_visible": rs.is_never_visible,
        "rise": _date_of(rs.rise_jd) if rs.rise_jd is not None else None,
        "set": _date_of(rs.set_jd) if rs.set_jd is not None else None,
        "hour_angle": rs.hour_angle_deg,
    }


def _card_conjunctions(ctx: _Ctx) -> Dict[str, Any]:
    """viii.14-15: the Ch.7 method applied to a star: when the planet reaches its longitude."""
    found = ch07.planet_star_conjunction(ctx.planet, ctx.star, ctx.year, ctx.months)
    nak = ch08.get_nakshatra(ctx.star)
    return {
        "planet": ctx.planet,
        "star": ctx.star,
        "star_longitude": nak.longitude,
        "star_latitude": nak.latitude,
        "year": ctx.year,
        "months": ctx.months,
        "conjunctions": [{
            "jd": c.jd,
            "date": _date_of(c.jd),
            "separation_deg": c.separation_deg,
        } for c in found],
    }


#: card id -> (verses, title, does, date_dependent, corpus records holding its text, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Optional[str], Callable[[_Ctx], Dict[str, Any]]]] = {
    "viii.1-4": (
        "1-4", "The polar longitudes (dhruva)",
        "Each asterism's share times ten, plus the minutes of the bhogas before it; four are placed by position.",
        False, "1-4", _card_longitudes,
    ),
    "viii.5-9": (
        "5-9", "The latitudes (viksepa)",
        "The latitude of each junction-star, north or south of its point of declination.",
        False, "5-5", _card_latitudes,
    ),
    "viii.1-9": (
        "1-9", "Where the star stands",
        "The chosen star's sidereal and tropical place, its equatorial coordinates, and its rising and setting.",
        True, None, _card_position,
    ),
    "viii.14-15": (
        "14-15", "A planet meets a star",
        "The method of conjunction taught in Chapter 7, applied to a planet and a junction-star.",
        True, None, _card_conjunctions,
    ),
}


def _build_card(card_id: str, ctx: _Ctx) -> Dict[str, Any]:
    """Build one card's full payload, chrome fields included."""
    verses, title, does, date_dependent, text_verses, builder = _CARDS[card_id]
    return {
        "id": card_id,
        "verses": verses,
        "title": title,
        "does": does,
        "date_dependent": date_dependent,
        "text_verses": text_verses,
        **builder(ctx),
    }


@router.post("/chapter/8")
def chapter_8(body: Ch08In) -> Dict[str, Any]:
    """Every computational verse of Chapter 8, with one star placed on one date."""
    ctx = _Ctx(star=body.star, planet=body.planet, year=body.year, month=body.month,
               day=float(body.day), months=body.months,
               latitude=body.latitude, longitude=body.longitude)
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 8,
        "title": CHAPTER_8_TITLE,
        "jd": jd,
        "star": body.star,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "order": CARD_ORDER,
        "cards": cards,
    }
