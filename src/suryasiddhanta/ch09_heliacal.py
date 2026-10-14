"""
Chapter 9: Heliacal Risings and Settings (Udayastadhikara)
============================================================

Heliacal phenomena: when planets first become visible after
conjunction with the Sun (heliacal rising) and when they
disappear into the Sun's glare (heliacal setting).

SS Ch.9 v.6-9 assigns minimum distances from the sun, in
time-degrees (kalamsas), for each planet's visibility:

  Mars 17 deg, Jupiter 11 deg, Saturn 15 deg;
  Mercury 12 deg retrograding / 14 deg advancing,
  Venus 8 deg retrograding / 10 deg advancing

When a planet's angular distance from the Sun exceeds its
threshold, it becomes visible to the naked eye.

Reference: SS Ch.9; Burgess (1860) pp.253-265
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from suryasiddhanta.ch01_mean_motions import julian_day, from_julian_day
from suryasiddhanta.ch02_true_places import normalize, compute


# -----------------------------------------------------------------
#  CONSTANTS -- SS Ch.9 v.6-9
#
#  Thresholds are kalamsas (time-degrees) of distance from the sun.
#  For Mercury and Venus the text distinguishes RETROGRADE vs direct
#  motion (v.7-8: Venus 8 deg "by reason of her greatness" near
#  inferior conjunction i.e. retrograde, 10 deg otherwise; Mercury
#  12 or 14 "according as he is retrograding or rapidly advancing").
#  Stored as (retrograde, direct). Applied here to ecliptic
#  elongation as an approximation of oblique-ascension kalamsas.
# -----------------------------------------------------------------

HELIACAL_PLANETS = {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}

VISIBILITY_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "Mars":    (17.0, 17.0),
    "Mercury": (12.0, 14.0),
    "Jupiter": (11.0, 11.0),
    "Venus":   (8.0,  10.0),
    "Saturn":  (15.0, 15.0),
}

_MAX_SEARCH_DAYS = 800


# -----------------------------------------------------------------
#  HELIACAL EVENT RESULT
# -----------------------------------------------------------------

@dataclass
class HeliacalEvent:
    """Result of a heliacal rising or setting computation."""
    planet: str
    event_type: str
    jd: float
    elongation: float
    direction: str

    def __str__(self) -> str:
        y, m, d, frac = from_julian_day(self.jd)
        return (
            f"Heliacal {self.event_type}: {self.planet}\n"
            f"  Date      : {y}-{m:02d}-{d:02d}\n"
            f"  Elongation: {self.elongation:.2f} deg\n"
            f"  Direction : {self.direction}\n"
        )


# -----------------------------------------------------------------
#  ELONGATION
# -----------------------------------------------------------------

def _jd_to_ymd(jd: float) -> Tuple[int, int, float]:
    y, m, d, frac = from_julian_day(jd)
    return y, m, d + frac


def sun_elongation(planet: str, jd: float) -> float:
    """
    Signed elongation of planet from Sun.

    Positive = planet east of Sun (evening star).
    Negative = planet west of Sun (morning star).

    Args:
        planet: Planet name (Mars, Mercury, Jupiter, Venus, Saturn)
        jd:     Julian Day

    Returns:
        Elongation in degrees (-180 to +180)
    """
    y, m, d_frac = _jd_to_ymd(jd)
    sun = compute("Sun", y, m, d_frac)
    pl = compute(planet, y, m, d_frac)
    diff = normalize(pl.true_longitude - sun.true_longitude)
    return diff - 360 if diff > 180 else diff


def _is_retrograde(planet: str, jd: float) -> bool:
    """True if planet's true longitude is decreasing at jd."""
    y1, m1, d1 = _jd_to_ymd(jd)
    y2, m2, d2 = _jd_to_ymd(jd + 1.0)
    lon1 = compute(planet, y1, m1, d1).true_longitude
    lon2 = compute(planet, y2, m2, d2).true_longitude
    motion = (lon2 - lon1 + 180.0) % 360.0 - 180.0
    return motion < 0


def _get_threshold(planet: str, jd: float) -> float:
    """Visibility threshold; retrograde vs direct (SS ix.7-8)."""
    retro, direct = VISIBILITY_THRESHOLDS[planet]
    if retro == direct:
        return direct
    return retro if _is_retrograde(planet, jd) else direct


# -----------------------------------------------------------------
#  VISIBILITY CHECK -- SS Ch.9 v.5-8
# -----------------------------------------------------------------

def is_planet_visible(planet: str, jd: float,
                      lat_deg: float = 0.0,
                      lon_deg: float = 0.0) -> bool:
    """
    Check if planet is visible (not lost in Sun's glare).

    Uses SS elongation thresholds. Planet is visible when its
    angular distance from the Sun exceeds the planet-specific
    minimum.

    Args:
        planet:  Planet name (one of HELIACAL_PLANETS)
        jd:      Julian Day
        lat_deg: Observer latitude (reserved for future refinement)
        lon_deg: Observer longitude (reserved for future refinement)

    Returns:
        True if planet is above visibility threshold

    Raises:
        ValueError: if planet not in HELIACAL_PLANETS
    """
    _validate_planet(planet)
    elong = sun_elongation(planet, jd)
    threshold = _get_threshold(planet, jd)
    return abs(elong) >= threshold


def _validate_planet(planet: str) -> None:
    if planet not in HELIACAL_PLANETS:
        raise ValueError(
            f"'{planet}' has no heliacal events. "
            f"Valid: {', '.join(sorted(HELIACAL_PLANETS))}")


# -----------------------------------------------------------------
#  HELIACAL RISING -- SS Ch.9 v.4-11
# -----------------------------------------------------------------

def heliacal_rising(planet: str, year: int,
                    lat_deg: float = 0.0,
                    start_month: int = 1) -> Optional[HeliacalEvent]:
    """
    Find next heliacal rising (planet becomes visible).

    Scans forward from the given date to find the first
    transition from invisible to visible.

    Args:
        planet:      Planet name
        year:        CE year to start search
        lat_deg:     Observer latitude (degrees)
        start_month: Starting month (default 1)

    Returns:
        HeliacalEvent or None if not found within search window
    """
    _validate_planet(planet)
    jd = julian_day(year, start_month, 1.0)
    was_visible = is_planet_visible(planet, jd, lat_deg)

    for _ in range(_MAX_SEARCH_DAYS):
        jd += 1.0
        now_visible = is_planet_visible(planet, jd, lat_deg)

        if not was_visible and now_visible:
            rising_jd = _bisect_transition(planet, jd - 1.0, jd, True)
            elong = sun_elongation(planet, rising_jd)
            return HeliacalEvent(
                planet=planet,
                event_type="rising",
                jd=round(rising_jd, 4),
                elongation=round(elong, 4),
                direction="morning" if elong < 0 else "evening",
            )

        was_visible = now_visible

    return None


# -----------------------------------------------------------------
#  HELIACAL SETTING -- SS Ch.9 v.9-11, v.17
# -----------------------------------------------------------------

def heliacal_setting(planet: str, year: int,
                     lat_deg: float = 0.0,
                     start_month: int = 1) -> Optional[HeliacalEvent]:
    """
    Find next heliacal setting (planet becomes invisible).

    Scans forward from the given date to find the first
    transition from visible to invisible.

    Args:
        planet:      Planet name
        year:        CE year to start search
        lat_deg:     Observer latitude (degrees)
        start_month: Starting month (default 1)

    Returns:
        HeliacalEvent or None if not found within search window
    """
    _validate_planet(planet)
    jd = julian_day(year, start_month, 1.0)
    was_visible = is_planet_visible(planet, jd, lat_deg)

    for _ in range(_MAX_SEARCH_DAYS):
        jd += 1.0
        now_visible = is_planet_visible(planet, jd, lat_deg)

        if was_visible and not now_visible:
            setting_jd = _bisect_transition(planet, jd - 1.0, jd, False)
            elong = sun_elongation(planet, setting_jd)
            return HeliacalEvent(
                planet=planet,
                event_type="setting",
                jd=round(setting_jd, 4),
                elongation=round(elong, 4),
                direction="morning" if elong < 0 else "evening",
            )

        was_visible = now_visible

    return None


def _bisect_transition(planet: str, lo: float, hi: float,
                       finding_rising: bool) -> float:
    """Bisect to refine visibility transition."""
    for _ in range(20):
        mid = (lo + hi) / 2
        vis = is_planet_visible(planet, mid)
        if finding_rising:
            if vis:
                hi = mid
            else:
                lo = mid
        else:
            if vis:
                lo = mid
            else:
                hi = mid
    return (lo + hi) / 2


# -----------------------------------------------------------------
#  ALL VISIBILITY EVENTS
# -----------------------------------------------------------------

def visibility_events(planet: str, year: int,
                      months: int = 12) -> List[HeliacalEvent]:
    """
    Find all heliacal risings and settings in the given period.

    Args:
        planet: Planet name
        year:   CE year
        months: Search span in months (default 12)

    Returns:
        Chronological list of HeliacalEvent (risings and settings)
    """
    _validate_planet(planet)
    jd_start = julian_day(year, 1, 1.0)
    jd_end = jd_start + months * 30.44

    events = []
    jd = jd_start
    was_visible = is_planet_visible(planet, jd)

    while jd + 1.0 <= jd_end:
        jd += 1.0
        now_visible = is_planet_visible(planet, jd)

        if not was_visible and now_visible:
            ev_jd = _bisect_transition(planet, jd - 1.0, jd, True)
            elong = sun_elongation(planet, ev_jd)
            events.append(HeliacalEvent(
                planet=planet, event_type="rising",
                jd=round(ev_jd, 4),
                elongation=round(elong, 4),
                direction="morning" if elong < 0 else "evening",
            ))

        elif was_visible and not now_visible:
            ev_jd = _bisect_transition(planet, jd - 1.0, jd, False)
            elong = sun_elongation(planet, ev_jd)
            events.append(HeliacalEvent(
                planet=planet, event_type="setting",
                jd=round(ev_jd, 4),
                elongation=round(elong, 4),
                direction="morning" if elong < 0 else "evening",
            ))

        was_visible = now_visible

    return events


# -----------------------------------------------------------------
#  NEXT HELIACAL EVENT FROM JD
# -----------------------------------------------------------------

def next_heliacal(planet: str, jd: float,
                  event_type: str = "rising") -> Optional[HeliacalEvent]:
    """
    Find the next heliacal event after a given JD.

    Args:
        planet:     Planet name
        jd:         Starting Julian Day
        event_type: "rising" or "setting"

    Returns:
        HeliacalEvent or None
    """
    _validate_planet(planet)
    if event_type not in ("rising", "setting"):
        raise ValueError(f"event_type must be 'rising' or 'setting'")

    was_visible = is_planet_visible(planet, jd)
    current_jd = jd

    for _ in range(_MAX_SEARCH_DAYS):
        current_jd += 1.0
        now_visible = is_planet_visible(planet, current_jd)

        found = False
        if event_type == "rising" and not was_visible and now_visible:
            found = True
            ev_jd = _bisect_transition(planet, current_jd - 1.0,
                                       current_jd, True)
        elif event_type == "setting" and was_visible and not now_visible:
            found = True
            ev_jd = _bisect_transition(planet, current_jd - 1.0,
                                       current_jd, False)

        if found:
            elong = sun_elongation(planet, ev_jd)
            return HeliacalEvent(
                planet=planet, event_type=event_type,
                jd=round(ev_jd, 4),
                elongation=round(elong, 4),
                direction="morning" if elong < 0 else "evening",
            )

        was_visible = now_visible

    return None
