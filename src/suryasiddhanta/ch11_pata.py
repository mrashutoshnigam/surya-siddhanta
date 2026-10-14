"""
Chapter 11: The Patas (Patadhikara)
====================================

Two malignant aspects of Sun and Moon, both defined by their
declinations becoming equal in amount:

  - **Vyatipata**: tropical longitudes sum to 180 deg; the declinations
    are then equal and in the same direction.
  - **Vaidhrita**: tropical longitudes sum to 360 deg; the declinations
    are equal and in opposite directions.

NOT the same as the nitya-yoga also called Vyatipata (number 17 of 27,
in ch01_mean_motions). That yoga is a fixed 13 deg 20' span of the
longitude sum; the pata of this chapter additionally requires the
declination condition and lasts only a few hours.

The chapter's substance is not the longitude rule, which is only the
trigger, but two things the longitude rule alone cannot give:

  1. the Moon's declination corrected for its celestial latitude,
     resolved onto the declination circle through the ayana valana
     (SS xi.6-11);
  2. the true instant of the pata, where the two declinations are equal,
     and its beginning and end from the half-sum of the discs over the
     difference of the daily motions (SS xi.12-15).

Reference: SS Ch.11; Burgess (1860) pp.281-292
"""

from __future__ import annotations

import math
from typing import Iterator, List, Optional, Tuple

from suryasiddhanta._types import PataEvent
from suryasiddhanta.ch01_mean_motions import (
    from_julian_day, moon_node_longitude,
)
from suryasiddhanta.ch02_true_places import (
    OBLIQUITY_DEGREES, compute, normalize,
)
from suryasiddhanta.ch03_direction_place_time import (
    declination, ecliptic_to_equatorial,
)
from suryasiddhanta.ch04_lunar_eclipses import (
    APPARENT_DIAMETER_ARCMIN, moon_latitude,
)


# ─────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────

VYATIPATA_SUM = 180.0
VAIDHRITA_SUM = 360.0
PATA_KINDS: Tuple[str, str] = ("Vyatipata", "Vaidhrita")

_SUM_TARGETS = {"Vyatipata": VYATIPATA_SUM, "Vaidhrita": VAIDHRITA_SUM}

# SS Ch.4 apparent diameters. A pata is reckoned to last while the two
# discs' combined semi-diameters are traversed at the difference of the
# Sun's and Moon's daily motions (SS xi.14-15).
_SEMI_SUM_ARCMIN = (APPARENT_DIAMETER_ARCMIN["Sun"]
                    + APPARENT_DIAMETER_ARCMIN["Moon"]) / 2.0

_SCAN_STEP = 0.5          # days — coarse scan of the longitude sum
_REFINE_WINDOW = 2.5      # days each side of a crossing
_REFINE_STEP = 0.25       # days — sub-scan for the declination sign change
_BISECT_STEPS = 40
_DERIV_H = 0.05           # days — central difference for declination rate
_MIN_RATE = 1.0           # arcmin/day floor, guards the duration divide
_MAX_HALF_DAYS = 0.5      # clamp on the half-duration


# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────

def _tropical_longitude(body: str, jd: float) -> float:
    """
    Tropical longitude of the Sun or Moon at a Julian Day, in degrees.

    The pata rules are stated in tropical longitudes because they are
    really statements about declination, which depends on the distance
    from the equinox, not from the fixed stars.
    """
    year, month, day, frac = from_julian_day(jd)
    pos = compute(body, year, month, day + frac)
    return normalize(pos.tropical_longitude)


def _sidereal_moon_longitude(jd: float) -> float:
    """Moon's sidereal true longitude — needed for its distance from the node."""
    year, month, day, frac = from_julian_day(jd)
    return compute("Moon", year, month, day + frac).true_longitude


# ─────────────────────────────────────────────────────────────────
#  DECLINATIONS — SS Ch.11 v.4-11
# ─────────────────────────────────────────────────────────────────

def ayana_valana(trop_lon_deg: float,
                 obliquity: float = OBLIQUITY_DEGREES) -> float:
    """
    Ayana valana: the angle between the ecliptic and the declination
    circle at a point (SS xi.4-5; the same angle as Ch.4 v.25).

        sin(valana) = sin(obliquity) * cos(tropical longitude)

    It is largest, and equal to the obliquity, at the equinoxes, and
    vanishes at the solstices where ecliptic and equator run parallel.

    Args:
        trop_lon_deg: Tropical longitude of the point (degrees)
        obliquity:    Obliquity of the ecliptic (degrees; SS uses 24)

    Returns:
        Valana in degrees, signed.
    """
    sin_v = (math.sin(math.radians(obliquity))
             * math.cos(math.radians(trop_lon_deg)))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_v))))


def sun_declination(jd: float) -> float:
    """
    Sun's declination in degrees, north positive.

    The Sun has no latitude by definition, so this is the plain
    declination of its tropical longitude.
    """
    return declination(_tropical_longitude("Sun", jd))


def moon_latitude_deg(jd: float) -> float:
    """
    Moon's celestial latitude in degrees, north positive.

    Wraps ch04's arcminute-valued viksepa, whose SS maximum is 270'
    (4.5 degrees).
    """
    node = moon_node_longitude(jd)
    return moon_latitude(_sidereal_moon_longitude(jd), node) / 60.0


def moon_declination(jd: float) -> float:
    """
    Moon's declination by the Surya Siddhanta's own rule (SS xi.6-11).

    The declination of the Moon's longitude is corrected by its latitude
    resolved along the declination circle:

        dec = dec(longitude) + latitude * cos(ayana valana)

    This is a first-order treatment. Against the rigorous spherical value
    (moon_declination_exact) it deviates by at most 0.023 degrees over all
    longitudes and the SS maximum latitude of 4.5 degrees — the error
    coming partly from the O(latitude^2) truncation and partly because
    cos(valana) only approximates cos(obliquity)/cos(dec), differing from
    it by up to 0.0039 near longitude 314 degrees.

    This is the value the pata search uses; the rigorous one exists for
    comparison only.

    Returns:
        Declination in degrees, north positive.
    """
    lon = _tropical_longitude("Moon", jd)
    beta = moon_latitude_deg(jd)
    valana = ayana_valana(lon)
    return declination(lon) + beta * math.cos(math.radians(valana))


def moon_declination_exact(jd: float) -> float:
    """
    Moon's declination by rigorous spherical trigonometry.

    Provided so the approximation in moon_declination can be measured
    rather than assumed. Not used by the pata search — the point of this
    library is to compute what the text computes.

    Returns:
        Declination in degrees, north positive.
    """
    lon = _tropical_longitude("Moon", jd)
    _, dec = ecliptic_to_equatorial(lon, moon_latitude_deg(jd))
    return dec


def longitude_sum(jd: float) -> float:
    """
    Sum of the tropical longitudes of Sun and Moon, in [0, 360).

    The pata trigger: 180 deg for a Vyatipata, 360 (that is, 0) for a
    Vaidhrita. It advances about 14.2 deg per day, so one or the other
    target is reached roughly every 12.7 days.
    """
    return normalize(_tropical_longitude("Sun", jd)
                     + _tropical_longitude("Moon", jd))


# ─────────────────────────────────────────────────────────────────
#  ROOT FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def _declination_root(kind: str, jd: float) -> float:
    """
    The function whose zero marks the true pata of a given kind.

    Vyatipata wants the declinations equal and of the same direction, so
    the root is their difference; Vaidhrita wants them equal and opposite,
    so the root is their sum.
    """
    dm = moon_declination(jd)
    ds = sun_declination(jd)
    return dm - ds if kind == "Vyatipata" else dm + ds


def _sum_offset(kind: str, jd: float) -> float:
    """
    Signed distance of the longitude sum from a kind's target, wrapped
    into [-180, 180) so that it crosses zero cleanly once per pata.
    """
    diff = normalize(longitude_sum(jd) - _SUM_TARGETS[kind])
    return diff - 360.0 if diff >= 180.0 else diff


def _bisect(fn, lo: float, hi: float) -> float:
    """Bisect a sign-changing function of Julian Day between two bounds."""
    f_lo = fn(lo)
    for _ in range(_BISECT_STEPS):
        mid = (lo + hi) / 2.0
        f_mid = fn(mid)
        if (f_lo < 0.0) == (f_mid < 0.0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ─────────────────────────────────────────────────────────────────
#  EVENT CONSTRUCTION — SS Ch.11 v.12-23
# ─────────────────────────────────────────────────────────────────

def _declination_rate(kind: str, jd: float) -> float:
    """
    Rate of change of a kind's root function, in arcminutes per day.

    Central difference over 0.05 day. Near a pata this runs about
    250-320 arcmin/day, dominated by the Moon's motion.
    """
    ahead = _declination_root(kind, jd + _DERIV_H)
    behind = _declination_root(kind, jd - _DERIV_H)
    return abs(ahead - behind) * 60.0 / (2.0 * _DERIV_H)


def _motion_difference(jd: float) -> float:
    """
    Difference of the Moon's and Sun's true daily motions, in arcminutes
    per day, over the day centred on `jd` (SS xi.14's divisor).

    Runs about 660-900 arcmin/day: the Moon's 11.8-15.4 deg less the Sun's
    roughly 1 deg.
    """
    def motion(body: str) -> float:
        return normalize(_tropical_longitude(body, jd + 0.5)
                         - _tropical_longitude(body, jd - 0.5))
    return (motion("Moon") - motion("Sun")) * 60.0


def _refine_middle(kind: str, jd_crossing: float) -> Tuple[float, bool]:
    """
    Find the true pata instant nearest a longitude-sum crossing.

    The Moon's latitude displaces its declination by up to 4.5 degrees, so
    the declination condition is generally met a few hours — and near a
    solstice as much as two days — away from the crossing. The root is
    also not monotonic there: the difference of declinations can turn
    without ever reaching zero, or reach it twice. So the window is
    sub-scanned for sign changes and the one nearest the crossing is
    bisected.

    Returns:
        (instant, refined). refined is False when the declination
        condition is not met anywhere in the window — SS xi.19's case
        of a pata that does not actually fall — and the caller then keeps
        the nominal crossing.
    """
    root = lambda t: _declination_root(kind, t)   # noqa: E731
    steps = int(2.0 * _REFINE_WINDOW / _REFINE_STEP)
    lo = jd_crossing - _REFINE_WINDOW

    best: Optional[Tuple[float, float]] = None   # (distance, instant)
    prev_t = lo
    prev_f = root(prev_t)
    for i in range(1, steps + 1):
        t = lo + i * _REFINE_STEP
        f = root(t)
        if (prev_f < 0.0) != (f < 0.0):
            hit = _bisect(root, prev_t, t)
            dist = abs(hit - jd_crossing)
            if best is None or dist < best[0]:
                best = (dist, hit)
        prev_t, prev_f = t, f

    return (jd_crossing, False) if best is None else (best[1], True)


def _build_event(kind: str, jd_crossing: float) -> PataEvent:
    """
    Refine one longitude-sum crossing into a complete PataEvent.

    Half-duration follows SS xi.14-15: "Multiply the half-sum of the
    dimensions of the sun and moon by sixty, and divide by the difference
    of their daily motions: the result is half the duration, in nadis."
    The declination rate is still measured, but only to flag a root that
    is a tangency rather than a crossing.
    """
    jd_middle, refined = _refine_middle(kind, jd_crossing)

    if _declination_rate(kind, jd_middle) <= _MIN_RATE:
        refined = False
    half = min(_SEMI_SUM_ARCMIN / _motion_difference(jd_middle), _MAX_HALF_DAYS)

    return PataEvent(
        kind=kind,
        jd_sum_crossing=round(jd_crossing, 6),
        jd_middle=round(jd_middle, 6),
        jd_begin=round(jd_middle - half, 6),
        jd_end=round(jd_middle + half, 6),
        duration_ghatis=round(2.0 * half * 60.0, 4),   # 1 ghati = 1/60 day
        sun_declination=round(sun_declination(jd_middle), 4),
        moon_declination=round(moon_declination(jd_middle), 4),
        moon_latitude=round(moon_latitude_deg(jd_middle) * 60.0, 2),
        longitude_sum=round(longitude_sum(jd_middle), 4),
        refined=refined,
    )


def _scan_crossings(jd_start: float,
                    jd_end: float) -> Iterator[Tuple[str, float]]:
    """
    Yield (kind, crossing JD) for every longitude-sum crossing in a range.

    Scans in half-day steps — the sum moves about 7 deg per step, far less
    than the 180 deg between targets, so no crossing is skipped — and
    bisects each sign change of the offset from that kind's target.
    """
    for kind in PATA_KINDS:
        t = jd_start
        prev = _sum_offset(kind, t)
        while t < jd_end:
            nxt = min(t + _SCAN_STEP, jd_end)
            cur = _sum_offset(kind, nxt)
            if prev < 0.0 <= cur:
                yield kind, _bisect(
                    lambda x, k=kind: _sum_offset(k, x), t, nxt)
            prev = cur
            t = nxt


# ─────────────────────────────────────────────────────────────────
#  PUBLIC SEARCH API
# ─────────────────────────────────────────────────────────────────

def find_patas(jd_start: float, jd_end: float) -> List[PataEvent]:
    """
    Every pata whose true instant falls between two Julian Days.

    Args:
        jd_start: Start of the search window (Julian Day)
        jd_end:   End of the search window (Julian Day)

    Returns:
        Events ordered by their true instant. `is_past` is left None —
        a range has no single instant to be past or future relative to.

    Raises:
        ValueError: if the window is empty or reversed.
    """
    if jd_end <= jd_start:
        raise ValueError("jd_end must be after jd_start")

    # Scan wider than the window: refining can move a pata's true instant by
    # up to _REFINE_WINDOW days, so a crossing just outside the range may
    # still have its middle inside it.
    events = [_build_event(kind, jd)
              for kind, jd in _scan_crossings(jd_start - _REFINE_WINDOW,
                                              jd_end + _REFINE_WINDOW)]
    events = [ev for ev in events if jd_start <= ev.jd_middle <= jd_end]
    events.sort(key=lambda ev: ev.jd_middle)
    return events


def find_next_pata(jd: float, kind: Optional[str] = None,
                   max_days: float = 60.0) -> Optional[PataEvent]:
    """
    The first pata at or after a given Julian Day.

    Args:
        jd:       Julian Day to search from
        kind:     "Vyatipata", "Vaidhrita", or None for whichever comes first
        max_days: How far ahead to look

    Returns:
        The next PataEvent with `is_past` set relative to `jd`, or None if
        none falls within `max_days`.

    Raises:
        ValueError: if `kind` is not a pata the Surya Siddhanta recognises.
    """
    if kind is not None and kind not in PATA_KINDS:
        raise ValueError(
            f"Unknown pata kind: {kind}. Expected one of {PATA_KINDS}.")

    for ev in find_patas(jd, jd + max_days):
        if kind is None or ev.kind == kind:
            ev.is_past = ev.jd_end < jd
            return ev
    return None


def active_pata(jd: float) -> Optional[PataEvent]:
    """
    The pata in progress at a given Julian Day, if any.

    Searches far enough either side to cover the refinement shift of the
    true instant plus the half-duration clamp of half a day.

    Returns:
        The PataEvent spanning `jd`, with `is_past` False, or None.
    """
    reach = _REFINE_WINDOW + _MAX_HALF_DAYS
    for ev in find_patas(jd - reach, jd + reach):
        if ev.jd_begin <= jd <= ev.jd_end:
            ev.is_past = False
            return ev
    return None
