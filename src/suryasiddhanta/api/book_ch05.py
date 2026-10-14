"""Verse-indexed payloads for the React "Book" page of Chapter 5.

Chapter 5 counterpart of ``book_ch04.py``: for the new moon nearest a date,
seen from one place, what does each computational verse of *Of Parallax in a
Solar Eclipse* yield? The React page renders one card per entry of
``CARD_ORDER`` in Burgess's order.

The verses give a hand method; ``ch05_solar_eclipses`` evaluates the same
quantities in closed form. Where the two differ the card shows both and says
why: the verse takes the interval from the *meridian* ecliptic-point
(madhyalagna) and treats the ecliptic zenith-distance by a plane triangle,
the library measures from the *nonagesimal* and is exact. Tests pin every
figure to ``ch05``.

Verses 2, 14 and the commentary-only verse 18 have no card: 2 and 14 are
absent from the corpus export, 18 only closes the chapter.

Reference: SS Ch.5 v.1-18; Burgess (1860) pp.170-200;
Srivastava Hindi Vigyan Bhashya (derivation of v.3-8)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch02_true_places as ch02
from suryasiddhanta import ch03_direction_place_time as ch03
from suryasiddhanta import ch04_lunar_eclipses as ch04
from suryasiddhanta import ch05_solar_eclipses as ch05

from .schemas import Ch05In, Ch05ProbeIn

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_5_TITLE = "Of Parallax in a Solar Eclipse"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = [
    "v.1", "v.3-4", "v.5-7", "v.8-9", "v.10-12", "v.13", "v.15-17",
]

_MINUTES_PER_DAY = 1440.0
#: Relative motion of Moon over Sun, arcminutes per ghati (60 ghatis a day).
_ARCMIN_PER_GHATI = ch04.RELATIVE_DAILY_MOTION_DEG * 60.0 / 60.0
#: v.11: the parallax in latitude is the drkksepa sine times 49' (49/R).
_NATI_VERSE_ARCMIN = 49.0


def _signed_degrees(angle: float) -> float:
    """Wrap an angle to (-180, 180]."""
    wrapped = ch02.normalize(angle)
    return wrapped - 360.0 if wrapped > 180.0 else wrapped


def madhyalagna(lst_deg: float) -> float:
    """Tropical longitude of the meridian ecliptic-point (madhyalagna).

    The ecliptic point whose right ascension equals the local sidereal time:
    ``tan(lon) = tan(RA) / cos(obliquity)`` in the quadrant of the RA.
    """
    eps = math.radians(ch02.OBLIQUITY_DEGREES)
    ra = math.radians(lst_deg)
    return math.degrees(math.atan2(math.sin(ra), math.cos(ra) * math.cos(eps))) % 360.0


def lambana_verse(interval_deg: float, drkksepa_deg: float) -> float:
    """Lambana in ghatis by v.8, signed as it is applied: -4 x drggati x sin(interval).

    v.9 subtracts it from the end of the lunar day when the Sun is past the
    meridian ecliptic-point (positive interval) and adds it otherwise, so the
    applied value is negative for a positive interval. ``drggati`` is the sine of the ecliptic altitude, ``cos(drkksepa)``; the
    divisor of the verse (the "chheda") is ``9 / (4 x drggati)`` with radius 1.
    """
    return -4.0 * ch05.lambana_factor(drkksepa_deg, interval_deg)


def nati_verse(drkksepa_deg: float) -> float:
    """Magnitude of the parallax in latitude by v.11, arcminutes: 49 x sin(drkksepa)."""
    return _NATI_VERSE_ARCMIN * abs(math.sin(math.radians(drkksepa_deg)))


@dataclass
class _Ctx:
    """The date guess, the place, and everything derived once from the new moon."""

    year: int
    month: int
    day: float
    latitude: float
    longitude: float

    @cached_property
    def new_moon_day(self) -> float:
        """Refined (fractional) day of the new moon, as ``find_new_moon`` gives it."""
        return ch05.find_new_moon(self.year, self.month, self.day)

    @cached_property
    def jd(self) -> float:
        """Julian Day of that new moon."""
        return ch01.julian_day(self.year, self.month, self.new_moon_day)

    @cached_property
    def lst(self) -> float:
        """Local sidereal time at the place, degrees."""
        return ch03.local_sidereal_time(self.jd, self.longitude)

    @cached_property
    def sun(self) -> float:
        """Tropical longitude of the Sun at the new moon."""
        sidereal = ch02.compute("Sun", self.year, self.month, self.new_moon_day).true_longitude
        return ch02.sidereal_to_tropical(sidereal, self.jd)

    @cached_property
    def moon(self) -> float:
        """Tropical longitude of the Moon at the new moon."""
        sidereal = ch02.compute("Moon", self.year, self.month, self.new_moon_day).true_longitude
        return ch02.sidereal_to_tropical(sidereal, self.jd)

    @cached_property
    def madhya(self) -> float:
        """Tropical longitude of the meridian ecliptic-point."""
        return madhyalagna(self.lst)

    @cached_property
    def madhya_declination(self) -> float:
        """Declination of the meridian ecliptic-point, north positive."""
        return ch03.declination(self.madhya)

    @cached_property
    def lagna(self) -> float:
        """Tropical longitude of the orient ecliptic-point (lagna)."""
        return ch05._lagna_longitude(self.lst, self.latitude)

    @cached_property
    def nonagesimal(self) -> Tuple[float, float]:
        """The library's (vitribha longitude, signed drkksepa)."""
        return ch05.nonagesimal(self.lst, self.latitude)

    @cached_property
    def moon_latitude(self) -> float:
        """The Moon's geocentric latitude at the new moon, arcminutes."""
        node = ch01.moon_node_longitude(self.jd)
        sidereal = ch02.compute("Moon", self.year, self.month, self.new_moon_day).true_longitude
        return ch04.moon_latitude(sidereal, node)

    @cached_property
    def eclipse(self) -> Any:
        """The library's topocentric solar eclipse for this new moon and place."""
        return ch05.compute_solar_eclipse_topocentric(
            self.year, self.month, self.new_moon_day, self.latitude, self.longitude)


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_no_parallax(ctx: _Ctx) -> Dict[str, Any]:
    """v.1: no longitude parallax at the meridian point, none in latitude at the zenith."""
    interval = _signed_degrees(ctx.sun - ctx.madhya)
    return {
        "latitude": ctx.latitude,
        "sun": ctx.sun,
        "madhyalagna": ctx.madhya,
        "interval": interval,
        "madhya_declination": ctx.madhya_declination,
        "latitude_gap": ctx.latitude - ctx.madhya_declination,
        "lambana_vanishes": abs(interval) < 1.0,
        "nati_vanishes": abs(ctx.latitude - ctx.madhya_declination) < 1.0,
    }


def _card_lagna(ctx: _Ctx) -> Dict[str, Any]:
    """v.3-4: the lagna, its udaya, the madhyalagna and the meridian zenith-distance."""
    eps = math.radians(ch02.OBLIQUITY_DEGREES)
    udaya = (math.sin(eps) * math.sin(math.radians(ctx.lagna))
             / math.cos(math.radians(ctx.latitude)))
    natamsa = abs(ctx.latitude - ctx.madhya_declination)
    return {
        "local_sidereal_time": ctx.lst,
        "lagna": ctx.lagna,
        "greatest_declination": ch02.OBLIQUITY_DEGREES,
        "colatitude_sine": math.cos(math.radians(ctx.latitude)),
        "udaya": udaya,
        "madhyalagna": ctx.madhya,
        "madhya_declination": ctx.madhya_declination,
        "latitude": ctx.latitude,
        "natamsa": natamsa,
        "direction": "north" if ctx.madhya_declination >= 0 else "south",
    }


def _card_drkksepa(ctx: _Ctx) -> Dict[str, Any]:
    """v.5-7: the meridian-sine, the drkksepa by the verse and by the library, the drggati."""
    lagna = _card_lagna(ctx)
    natamsa = lagna["natamsa"]
    udaya = lagna["udaya"]
    madhyajya = math.sin(math.radians(natamsa))
    sin_drk = math.sqrt(max(0.0, madhyajya ** 2 - (madhyajya * udaya) ** 2))
    drk_verse = math.degrees(math.asin(min(1.0, sin_drk)))
    vitribha, drk_library = ctx.nonagesimal
    return {
        "natamsa": natamsa,
        "madhyajya": madhyajya,
        "udaya": udaya,
        "drkksepa_verse": drk_verse,
        "drkksepa_library": drk_library,
        "drkksepa_gap": abs(drk_library) - drk_verse,
        "drggati": math.cos(math.radians(drk_library)),
        "approx_drkksepa": natamsa,
        "approx_drggati": math.cos(math.radians(natamsa)),
        "vitribha": vitribha,
    }


def _card_lambana(ctx: _Ctx) -> Dict[str, Any]:
    """v.8-9: the parallax in longitude, by the verse and by the library."""
    vitribha, drk = ctx.nonagesimal
    interval = _signed_degrees(ctx.sun - ctx.madhya)
    verse_ghatis = lambana_verse(interval, drk)
    library_arcmin = ch05.lambana_correction(ctx.jd, ctx.latitude, ctx.longitude)
    return {
        "drkksepa": drk,
        "drggati": math.cos(math.radians(drk)),
        "interval": interval,
        "moon_from_vitribha": _signed_degrees(ctx.moon - vitribha),
        "verse_ghatis": verse_ghatis,
        "verse_arcmin": verse_ghatis * _ARCMIN_PER_GHATI,
        "library_arcmin": library_arcmin,
        "library_ghatis": library_arcmin / _ARCMIN_PER_GHATI,
        "arcmin_per_ghati": _ARCMIN_PER_GHATI,
        "rule": "subtract" if interval > 0 else "add",
    }


def _card_nati(ctx: _Ctx) -> Dict[str, Any]:
    """v.10-12: the parallax in latitude, and its combination with the Moon's latitude."""
    _, drk = ctx.nonagesimal
    nati_library = ch05.nati_correction(ctx.jd, ctx.latitude, ctx.longitude)
    return {
        "drkksepa": drk,
        "verse_arcmin": nati_verse(drk),
        "shortcut_arcmin": math.sin(math.radians(drk)) * 3438.0 / 70.0,
        "library_arcmin": nati_library,
        "meridian_direction": "north" if ctx.madhya_declination > ctx.latitude else "south",
        "moon_latitude": ctx.moon_latitude,
        "corrected_latitude": ctx.eclipse.moon_latitude,
        "same_direction": ctx.moon_latitude * nati_library > 0,
    }


def _card_result(ctx: _Ctx) -> Dict[str, Any]:
    """v.13: the half-duration, obscuration and type for the corrected geometry."""
    eclipse = ctx.eclipse
    geocentric = ch05.compute_solar_eclipse(ctx.year, ctx.month, ctx.new_moon_day)
    return {
        "day": ctx.new_moon_day,
        "is_eclipse": eclipse.is_eclipse,
        "locally_visible": eclipse.locally_visible,
        "sun_altitude_deg": eclipse.sun_altitude_deg,
        "eclipse_type": eclipse.eclipse_type,
        "magnitude": eclipse.magnitude,
        "half_duration_min": eclipse.half_duration,
        "sun_diameter": eclipse.sun_diameter,
        "moon_diameter": eclipse.moon_diameter,
        "lambana": eclipse.lambana,
        "nati": eclipse.nati,
        "geocentric_type": geocentric.eclipse_type,
        "geocentric_magnitude": geocentric.magnitude,
        "geocentric_latitude": ctx.moon_latitude,
    }


def _card_contacts(ctx: _Ctx) -> Dict[str, Any]:
    """v.15-17: the half-duration corrected for the parallax at contact and separation.

    Lambana is evaluated at the contact, the middle and the separation. With
    the signed library value (positive when the conjunction comes later) an
    event at ``t`` is seen at ``t + lambana(t) / speed``, so the half-duration
    on the separation side grows by ``lambana(sep) - lambana(mid)`` and on the
    contact side by ``lambana(mid) - lambana(contact)``. That one signed
    formula covers all three cases of the verses (same hemisphere, either
    order, and the two hemispheres).
    """
    eclipse = ctx.eclipse
    if not eclipse.is_eclipse or not eclipse.half_duration:
        return {"is_eclipse": False}
    jd_mid = eclipse.jd
    half_days = eclipse.half_duration / _MINUTES_PER_DAY
    speed = ch04.RELATIVE_DAILY_MOTION_DEG * 60.0 / _MINUTES_PER_DAY  # arcmin/min

    def lam(jd: float) -> float:
        return ch05.lambana_correction(jd, ctx.latitude, ctx.longitude)

    at_contact = lam(jd_mid - half_days)
    at_middle = lam(jd_mid)
    at_separation = lam(jd_mid + half_days)
    contact_adjust = (at_middle - at_contact) / speed
    separation_adjust = (at_separation - at_middle) / speed
    ra = ch03.right_ascension(ctx.sun)
    hour_angle = _signed_degrees(ctx.lst - ra)
    return {
        "is_eclipse": True,
        "half_duration_min": eclipse.half_duration,
        "hemisphere": "western" if hour_angle > 0 else "eastern",
        "hour_angle": hour_angle,
        "lambana_contact": at_contact,
        "lambana_middle": at_middle,
        "lambana_separation": at_separation,
        "contact_adjust_min": contact_adjust,
        "separation_adjust_min": separation_adjust,
        "contact_half_min": eclipse.half_duration + contact_adjust,
        "separation_half_min": eclipse.half_duration + separation_adjust,
        "speed_arcmin_per_min": speed,
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "v.1": (
        "1", "Where there is no parallax",
        "None in longitude when the Sun is at the meridian ecliptic-point; none in latitude when latitude equals its declination.",
        True, _card_no_parallax,
    ),
    "v.3-4": (
        "3-4", "The lagna and the meridian point",
        "The orient ecliptic-point and its udaya, the meridian ecliptic-point, and the meridian zenith-distance.",
        True, _card_lagna,
    ),
    "v.5-7": (
        "5-7", "The ecliptic zenith-distance",
        "The drkksepa and drggati from the meridian-sine and the udaya, against the library's exact nonagesimal.",
        True, _card_drkksepa,
    ),
    "v.8-9": (
        "8-9", "Parallax in longitude (lambana)",
        "The sine of the interval over the divisor: lambana in nadis, with the rule for applying it.",
        True, _card_lambana,
    ),
    "v.10-12": (
        "10-12", "Parallax in latitude (nati)",
        "The drkksepa sine times 49', its direction, and its sum or difference with the Moon's latitude.",
        True, _card_nati,
    ),
    "v.13": (
        "13", "The eclipse as seen from here",
        "Half-duration, amount obscured and type, recomputed with both parallaxes.",
        True, _card_result,
    ),
    "v.15-17": (
        "15-17", "The parallax at contact and separation",
        "How the parallax changes between middle and ends alters each half-duration.",
        True, _card_contacts,
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


@router.post("/chapter/5")
def chapter_5(body: Ch05In) -> Dict[str, Any]:
    """Every computational verse of Chapter 5, for the new moon nearest one date and place."""
    ctx = _Ctx(year=body.year, month=body.month, day=float(body.day),
               latitude=body.latitude, longitude=body.longitude)
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 5,
        "title": CHAPTER_5_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "place": {"latitude": body.latitude, "longitude": body.longitude},
        "order": CARD_ORDER,
        "cards": cards,
    }


@router.post("/chapter/5/probe")
def chapter_5_probe(body: Ch05ProbeIn) -> Dict[str, Any]:
    """Evaluate one parallax formula for a slider's worth of input.

    ``v.8-9`` needs ``interval`` and ``drkksepa``; ``v.10-12`` needs only
    ``drkksepa``. A card's missing input is a 422.
    """
    if body.drkksepa is None:
        raise HTTPException(status_code=422, detail="drkksepa is required")
    if body.card == "v.8-9":
        if body.interval is None:
            raise HTTPException(status_code=422, detail="interval is required for v.8-9")
        ghatis = lambana_verse(body.interval, body.drkksepa)
        return {
            "drggati": math.cos(math.radians(body.drkksepa)),
            "verse_ghatis": ghatis,
            "verse_arcmin": ghatis * _ARCMIN_PER_GHATI,
        }
    return {
        "verse_arcmin": nati_verse(body.drkksepa),
        "shortcut_arcmin": math.sin(math.radians(body.drkksepa)) * 3438.0 / 70.0,
        "library_arcmin": -ch05.PARALLAX_DIFF_ARCMIN * math.sin(math.radians(body.drkksepa)),
    }
