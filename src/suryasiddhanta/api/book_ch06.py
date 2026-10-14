"""Verse-indexed payloads for the React "Book" page of Chapter 6.

Chapter 6 counterpart of ``book_ch05.py``: for the full moon (lunar) or new
moon (solar) nearest a date, seen from one place, what does each step of the
projection in *Of the Projection of Eclipses* give? One card per entry of
``CARD_ORDER`` in Burgess's order.

Frame. All coordinates are arcminutes ("digits": the verses lay minutes off
as digits) measured from the centre of the eclipsed body, ``x`` along the
ecliptic, ``y`` across it. The React diagram rotates that frame by the valana
(v.2: the ecliptic runs through the centre and the end of the deflection).

Signs follow the verses: v.8 draws the latitude in its own direction in a
solar eclipse and *opposite* in a lunar one, while v.4 puts the contact on
the east in a lunar eclipse and on the west in a solar one. The library's
diagram follows the same convention.

Verses 3, 16 and 24 have no card: 3 and 16 are absent from the corpus
export and 24 is a closing admonition.

Reference: SS Ch.6 v.1-24; Burgess (1860) pp.200-215; valana is SS Ch.4 v.24-25
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
from suryasiddhanta import ch05_solar_eclipses as ch05
from suryasiddhanta import ch06_eclipse_projection as ch06

from .schemas import Ch06In, Ch06ProbeIn

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_6_TITLE = "Of the Projection of Eclipses"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = [
    "vi.2", "vi.4-9", "vi.10-11", "vi.13", "vi.14-16", "vi.17-19", "vi.20-22", "vi.23",
]

#: v.2: the deflection circle has a radius of forty-nine digits.
VALANA_CIRCLE_DIGITS = 49.0
#: v.13: the Sun's disk cannot be seen to be eclipsed below three minutes.
SUN_VISIBLE_MINUTES = 3.0
#: v.13: the Moon shows an eclipse down to a twelfth part of her disk.
MOON_VISIBLE_FRACTION = 1.0 / 12.0


def contact_sign(kind: str) -> int:
    """+1 when first contact has the eclipser on the east of the eclipsed body.

    A lunar eclipse begins on the east of the Moon (the shadow comes up from
    the east); a solar one on the west of the Sun (v.4).
    """
    return 1 if kind == "lunar" else -1


def path_point(kind: str, latitude: float, x_abs: float, at_contact: bool) -> Tuple[float, float]:
    """Centre of the eclipser, ecliptic frame, at one end of a chord.

    ``x_abs`` is its distance along the ecliptic from the eclipsed centre.
    Latitude is laid off in its own direction for a solar eclipse and
    reversed for a lunar one (v.8).
    """
    x = contact_sign(kind) * x_abs * (1.0 if at_contact else -1.0)
    y = latitude if kind == "solar" else -latitude
    return x, y


@dataclass
class _Ctx:
    """Kind of eclipse, the date guess and the place, and the geometry derived once."""

    kind: str
    year: int
    month: int
    day: float
    latitude: float
    longitude: float

    @cached_property
    def _eclipse(self) -> Tuple[Any, float, float, float]:
        """(library eclipse, eclipsed radius, eclipser radius, path latitude), arcminutes."""
        if self.kind == "lunar":
            ecl = ch04.compute_lunar_eclipse(self.year, self.month, self.day)
            er, rr, lat, _ = ch06._eclipse_radii(ecl)
            return ecl, er, rr, lat
        day = ch05.find_new_moon(self.year, self.month, self.day)
        ecl = ch05.compute_solar_eclipse_topocentric(
            self.year, self.month, day, self.latitude, self.longitude)
        er, rr, lat, _ = ch06._eclipse_radii(ecl)
        return ecl, er, rr, lat

    @property
    def eclipse(self) -> Any:
        """The library eclipse result the construction is drawn for."""
        return self._eclipse[0]

    @property
    def eclipsed_r(self) -> float:
        """Radius of the eclipsed body (chhadya), arcminutes."""
        return self._eclipse[1]

    @property
    def eclipser_r(self) -> float:
        """Radius of the eclipsing body (chhadaka), arcminutes."""
        return self._eclipse[2]

    @property
    def path_latitude(self) -> float:
        """Latitude of the path: the Moon's, parallax-corrected for a solar eclipse."""
        return self._eclipse[3]

    @cached_property
    def valana(self) -> Tuple[float, float, float]:
        """(total, ayana, aksha) valana of the eclipsed body, degrees, north positive."""
        body = "Moon" if self.kind == "lunar" else "Sun"
        return ch06._valana_at_eclipse(self.eclipse.jd, self.latitude, self.longitude, body)

    @cached_property
    def geometry(self) -> Dict[str, Any]:
        """The disks, the verdict, and the chord of the path (ecliptic frame)."""
        return _geometry(self.kind, self.eclipsed_r, self.eclipser_r, self.path_latitude)


def _geometry(kind: str, eclipsed_r: float, eclipser_r: float, latitude: float) -> Dict[str, Any]:
    """The aggregate and difference circles, the verdict, and the path chord.

    The aggregate circle has the half-sum of the disks for radius (v.2); the
    eclipser's centre runs along the chord of it at the latitude (v.14-16).
    All lengths arcminutes.
    """
    half_sum = eclipsed_r + eclipser_r
    half_diff = abs(eclipser_r - eclipsed_r)
    abs_lat = abs(latitude)
    out: Dict[str, Any] = {
        "kind": kind,
        "eclipsed_radius": eclipsed_r,
        "eclipser_radius": eclipser_r,
        "half_sum": half_sum,
        "half_difference": half_diff,
        "latitude": latitude,
        "is_eclipse": abs_lat < half_sum,
        "eclipse_type": "none",
        "obscured": 0.0,
        "magnitude": 0.0,
        "chord_half": None,
        "contact": None,
        "middle": (0.0, latitude if kind == "solar" else -latitude),
        "separation": None,
    }
    if abs_lat >= half_sum:
        return out
    chord = math.sqrt(half_sum ** 2 - abs_lat ** 2)
    if abs_lat < half_diff:
        out["eclipse_type"] = (
            "total" if (eclipser_r > eclipsed_r) else "annular" if kind == "solar" else "total")
    else:
        out["eclipse_type"] = "partial"
    out["obscured"] = half_sum - abs_lat
    out["magnitude"] = out["obscured"] / (2.0 * eclipsed_r)
    out["chord_half"] = chord
    out["contact"] = path_point(kind, latitude, chord, True)
    out["separation"] = path_point(kind, latitude, chord, False)
    return out


def _direction(value: float) -> str:
    """North/south word for a north-positive signed angle."""
    return "north" if value >= 0 else "south"


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_circles(ctx: _Ctx) -> Dict[str, Any]:
    """vi.2: the deflection circle of 49 digits, the aggregate circle, and the two bodies."""
    g = ctx.geometry
    return {
        "valana_circle": VALANA_CIRCLE_DIGITS,
        "aggregate_radius": g["half_sum"],
        "eclipsed_radius": g["eclipsed_radius"],
        "eclipser_radius": g["eclipser_radius"],
        "half_difference": g["half_difference"],
        "eclipsed_body": "Moon" if ctx.kind == "lunar" else "Sun",
        "eclipser_body": "Earth's shadow" if ctx.kind == "lunar" else "Moon",
    }


def _card_directions(ctx: _Ctx) -> Dict[str, Any]:
    """vi.4-9: where contact falls, and the deflection laid off at contact and separation."""
    total, ayana, aksha = ctx.valana
    lunar = ctx.kind == "lunar"
    # v.5: the contact valana is laid in its own direction in a lunar eclipse,
    # reversed in a solar one; the separation takes the other.
    contact_valana = total if lunar else -total
    latitude = ctx.path_latitude
    same = total * latitude > 0
    # v.9: lunar - east when valana and latitude agree, else west; solar contrary.
    east = same if lunar else not same
    return {
        "contact_limb": "east" if lunar else "west",
        "separation_limb": "west" if lunar else "east",
        "valana": total,
        "ayana_valana": ayana,
        "aksha_valana": aksha,
        "valana_direction": _direction(total),
        "contact_valana": contact_valana,
        "separation_valana": -contact_valana,
        "latitude": latitude,
        "latitude_direction": _direction(latitude),
        "same_direction": same,
        "deflection_laid": "east" if east else "west",
        "latitude_drawn": "in its own direction" if not lunar else "reversed",
    }


def _card_obscuration(ctx: _Ctx) -> Dict[str, Any]:
    """vi.10-11: the middle latitude, the circle on it, and the part of the disk it covers."""
    g = ctx.geometry
    return {
        **g,
        "valana": ctx.valana[0],
        "middle_latitude": g["middle"][1],
        "circle_radius": g["eclipser_radius"],
    }


def _card_visibility(ctx: _Ctx) -> Dict[str, Any]:
    """vi.13: the least eclipse the eye can see: a twelfth of the Moon, three minutes of the Sun."""
    g = ctx.geometry
    if ctx.kind == "lunar":
        threshold = 2.0 * ctx.eclipsed_r * MOON_VISIBLE_FRACTION
    else:
        threshold = SUN_VISIBLE_MINUTES
    return {
        "kind": ctx.kind,
        "threshold": threshold,
        "obscured": g["obscured"],
        "visible": g["obscured"] >= threshold,
        "is_eclipse": g["is_eclipse"],
    }


def _card_path(ctx: _Ctx) -> Dict[str, Any]:
    """vi.14-16: the path of the eclipser, a chord of the aggregate circle at the latitude."""
    g = ctx.geometry
    library = None
    if ctx.eclipse.is_eclipse:
        path = ch06.project_eclipse_path(ctx.eclipse)
        if path:
            library = abs(path[-1][0])
    return {
        **g,
        "valana": ctx.valana[0],
        "chord_length": None if g["chord_half"] is None else 2.0 * g["chord_half"],
        "library_chord_half": library,
    }


def _stick_card(ctx: _Ctx, stick: float) -> Dict[str, Any]:
    """The eclipser's centre where a stick of this length from the middle meets the path."""
    g = ctx.geometry
    abs_lat = abs(g["latitude"])
    out: Dict[str, Any] = {**g, "valana": ctx.valana[0], "stick": stick, "reaches_path": stick >= abs_lat}
    if stick >= abs_lat:
        x_abs = math.sqrt(stick ** 2 - abs_lat ** 2)
        out["contact_point"] = path_point(ctx.kind, g["latitude"], x_abs, True)
        out["separation_point"] = path_point(ctx.kind, g["latitude"], x_abs, False)
    else:
        out["contact_point"] = out["separation_point"] = None
    return out


def _card_stick(ctx: _Ctx) -> Dict[str, Any]:
    """vi.17-19: half the sum less the amount obscured, laid to the path (default: half way in)."""
    g = ctx.geometry
    if not g["is_eclipse"]:
        return {**g, "valana": ctx.valana[0], "stick": None, "reaches_path": False,
                "contact_point": None, "separation_point": None, "default_obscured": 0.0}
    default = g["obscured"] / 2.0
    return {**_stick_card(ctx, g["half_sum"] - default), "default_obscured": default}


def _card_immersion(ctx: _Ctx) -> Dict[str, Any]:
    """vi.20-22: the stick of immersion, half the difference of the measures."""
    g = ctx.geometry
    card = _stick_card(ctx, g["half_difference"])
    card["has_immersion"] = g["is_eclipse"] and g["eclipse_type"] in ("total", "annular")
    return card


def _card_colours(ctx: _Ctx) -> Dict[str, Any]:
    """vi.23: the colour of the eclipsed disk, by the part covered and the phase."""
    g = ctx.geometry
    if not g["is_eclipse"]:
        now = None
    elif g["eclipse_type"] in ("total", "annular"):
        now = "tawny (kapila)" if ctx.kind == "lunar" else "total / ring"
    elif g["magnitude"] < 0.5:
        now = "dusky (sadhumra)"
    else:
        now = "black"
    return {
        "kind": ctx.kind,
        "magnitude": g["magnitude"],
        "eclipse_type": g["eclipse_type"],
        "at_maximum": now,
        "scheme": [
            {"phase": "less than half obscured", "colour": "dusky (sadhumra)"},
            {"phase": "more than half obscured", "colour": "black"},
            {"phase": "emerging", "colour": "dark copper (krishnatamra)"},
            {"phase": "total obscuration", "colour": "tawny (kapila)"},
        ],
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "vi.2": (
        "1-2", "The circles of the figure",
        "A deflection circle of 49 digits, the aggregate circle of half the sum, and the two bodies.",
        True, _card_circles,
    ),
    "vi.4-9": (
        "4-9", "Contact, separation and the deflection",
        "Which limb the eclipse begins on, and the valana laid off at contact and separation.",
        True, _card_directions,
    ),
    "vi.10-11": (
        "10-11", "The latitude and what it covers",
        "The latitude laid off from the middle, and the part of the disk inside the eclipser's circle.",
        True, _card_obscuration,
    ),
    "vi.13": (
        "13", "What can be seen",
        "A twelfth of the Moon is seen eclipsed; three minutes of the Sun are not.",
        True, _card_visibility,
    ),
    "vi.14-16": (
        "14-16", "The path of the eclipser",
        "The arc through contact, middle and separation. The library draws it as a straight chord.",
        True, _card_path,
    ),
    "vi.17-19": (
        "17-19", "The stick for a given time",
        "Half the sum less the amount obscured, laid from the centre to the path.",
        True, _card_stick,
    ),
    "vi.20-22": (
        "20-22", "Immersion and emergence",
        "A stick of half the difference of the measures, laid toward contact and separation.",
        True, _card_immersion,
    ),
    "vi.23": (
        "23", "The colours",
        "The eclipsed disk is dusky, black, dark copper or tawny by the phase.",
        True, _card_colours,
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


@router.post("/chapter/6")
def chapter_6(body: Ch06In) -> Dict[str, Any]:
    """Every step of the Chapter 6 projection, for the eclipse nearest one date and place."""
    ctx = _Ctx(kind=body.kind, year=body.year, month=body.month, day=float(body.day),
               latitude=body.latitude, longitude=body.longitude)
    try:
        jd = ctx.eclipse.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 6,
        "title": CHAPTER_6_TITLE,
        "kind": body.kind,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "place": {"latitude": body.latitude, "longitude": body.longitude},
        "order": CARD_ORDER,
        "cards": cards,
    }


@router.post("/chapter/6/probe")
def chapter_6_probe(body: Ch06ProbeIn) -> Dict[str, Any]:
    """Lay a stick to the path for any two disks and latitude.

    ``vi.17-19`` uses half the sum less ``obscured``; ``vi.20-22`` uses half
    the difference. The point is the eclipser's centre on the chosen side.
    """
    half_sum = body.eclipsed_radius + body.eclipser_radius
    half_diff = abs(body.eclipser_radius - body.eclipsed_radius)
    abs_lat = abs(body.latitude_arcmin)
    stick = half_sum - body.obscured if body.card == "vi.17-19" else half_diff
    out: Dict[str, Any] = {
        "half_sum": half_sum, "half_difference": half_diff, "stick": stick,
        "max_obscured": max(0.0, half_sum - abs_lat),
        "reaches_path": 0.0 <= stick and stick >= abs_lat and abs_lat < half_sum,
        "point": None,
    }
    if out["reaches_path"]:
        x_abs = math.sqrt(stick ** 2 - abs_lat ** 2)
        out["point"] = path_point(
            body.kind, body.latitude_arcmin, x_abs, body.side == "contact")
    return out
