"""
Chapter 10: Moon's Risings and Lunar Horns (Chandrashrngonnatidhikara)
======================================================================

Lunar phase, moonrise/moonset, and crescent geometry.

  - **Phase**: elongation from the Sun determines the illuminated
    fraction (0 at new moon, 1 at full moon).
  - **Moonrise/set**: the Moon rises ~50 minutes later each day
    due to its ~13 deg/day eastward motion.
  - **Crescent horns**: the bright limb faces the Sun; the horn
    tips point away. Their apparent tilt depends on the ecliptic's
    angle to the observer's horizon.

SS Ch.10 v.1-5: illuminated fraction from elongation.
SS Ch.10 v.6-10: crescent geometry and horn direction. The position-angle
functions below are a modern equatorial-coordinate overlay, not Burgess's
graphical construction of the horns.

Reference: SS Ch.10; Burgess (1860) pp.266-280
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from suryasiddhanta.ch01_mean_motions import (
    julian_day, from_julian_day, moon_node_longitude,
)
from suryasiddhanta.ch02_true_places import (
    normalize, compute, ayanamsha, OBLIQUITY_DEGREES,
)
from suryasiddhanta.ch03_direction_place_time import (
    ecliptic_to_equatorial, equatorial_to_horizontal,
    local_sidereal_time,
)
from suryasiddhanta.ch04_lunar_eclipses import moon_latitude


# -----------------------------------------------------------------
#  CONSTANTS
# -----------------------------------------------------------------

MOON_APPARENT_RADIUS = 15.75

PHASE_NAMES = [
    (0.0,   "New Moon"),
    (22.5,  "Waxing Crescent"),
    (67.5,  "First Quarter"),
    (112.5, "Waxing Gibbous"),
    (157.5, "Full Moon"),
    (202.5, "Waning Gibbous"),
    (247.5, "Third Quarter"),
    (292.5, "Waning Crescent"),
    (337.5, "New Moon"),
]

_SCAN_STEP = 0.02
_SCAN_RANGE = 100


# -----------------------------------------------------------------
#  HELPERS
# -----------------------------------------------------------------

def _jd_to_ymd(jd: float) -> Tuple[int, int, float]:
    y, m, d, frac = from_julian_day(jd)
    return y, m, d + frac


def _moon_equatorial(jd: float) -> Tuple[float, float]:
    """Moon's equatorial (RA, dec) at given JD."""
    y, m, d_frac = _jd_to_ymd(jd)
    moon = compute("Moon", y, m, d_frac)
    ayan = ayanamsha(jd)
    trop_lon = normalize(moon.true_longitude + ayan)
    node_lon = moon_node_longitude(jd)
    lat_arcmin = moon_latitude(moon.true_longitude, node_lon)
    lat_deg = lat_arcmin / 60.0
    return ecliptic_to_equatorial(trop_lon, lat_deg)


def _sun_equatorial(jd: float) -> Tuple[float, float]:
    """Sun's equatorial (RA, dec) at given JD."""
    y, m, d_frac = _jd_to_ymd(jd)
    sun = compute("Sun", y, m, d_frac)
    ayan = ayanamsha(jd)
    trop_lon = normalize(sun.true_longitude + ayan)
    return ecliptic_to_equatorial(trop_lon, 0.0)


def _moon_altitude(jd: float, lat_deg: float, lon_deg: float) -> float:
    """Moon's altitude above horizon in degrees."""
    ra, dec = _moon_equatorial(jd)
    lst = local_sidereal_time(jd, lon_deg)
    _, alt = equatorial_to_horizontal(ra, dec, lst, lat_deg)
    return alt


# -----------------------------------------------------------------
#  LUNAR PHASE -- SS Ch.10 v.1-5
# -----------------------------------------------------------------

def moon_elongation(jd: float) -> float:
    """
    Moon's elongation from Sun in degrees (0 to 360).

    0 = new moon, 90 = first quarter, 180 = full moon,
    270 = third quarter.
    """
    y, m, d_frac = _jd_to_ymd(jd)
    sun = compute("Sun", y, m, d_frac)
    moon = compute("Moon", y, m, d_frac)
    return normalize(moon.true_longitude - sun.true_longitude)


def illuminated_fraction(jd: float) -> float:
    """
    Fraction of the Moon's disc that is illuminated (0 to 1).

    SS Ch.10 v.9: the illuminated part (sita), in digits of a
    12-digit disc, is the moon-sun elongation in minutes divided
    by 900 — i.e. LINEAR in elongation (10800' : 12 digits ::
    elongation : sita). For elongation past 180 deg the rule is
    applied to 360 - elongation (v.16). Burgess notes the Hindus
    knowingly ignored the versed-sine refinement.

    Returns:
        0.0 at new moon, 0.5 at quarters, 1.0 at full moon
    """
    elong = moon_elongation(jd)
    if elong > 180.0:
        elong = 360.0 - elong
    return round(elong / 180.0, 6)


def phase_name(jd: float) -> str:
    """
    Name of the current lunar phase (one of 8 phases).

    New Moon, Waxing Crescent, First Quarter, Waxing Gibbous,
    Full Moon, Waning Gibbous, Third Quarter, Waning Crescent.
    """
    elong = moon_elongation(jd)
    for i in range(len(PHASE_NAMES) - 1, -1, -1):
        if elong >= PHASE_NAMES[i][0]:
            return PHASE_NAMES[i][1]
    return "New Moon"


def is_waxing(jd: float) -> bool:
    """True if Moon is waxing (elongation 0-180)."""
    return moon_elongation(jd) < 180.0


# -----------------------------------------------------------------
#  MOONRISE / MOONSET
#
#  Scans altitude in 0.02-day (~29 min) steps and bisects
#  the sign change. Moon's fast motion (~13 deg/day) requires
#  this iterative approach over the hour-angle shortcut.
# -----------------------------------------------------------------

def moonrise(jd: float, lat_deg: float, lon_deg: float) -> Optional[float]:
    """
    Find next moonrise after the given JD.

    Scans Moon altitude in ~29 minute steps and bisects when
    the altitude crosses from negative to positive.

    Args:
        jd:      Starting Julian Day
        lat_deg: Observer latitude (degrees)
        lon_deg: Observer longitude (degrees, east positive)

    Returns:
        JD of next moonrise, or None if Moon is circumpolar
    """
    prev_alt = _moon_altitude(jd, lat_deg, lon_deg)
    t = jd

    for _ in range(_SCAN_RANGE):
        t += _SCAN_STEP
        alt = _moon_altitude(t, lat_deg, lon_deg)

        if prev_alt < 0 and alt >= 0:
            lo, hi = t - _SCAN_STEP, t
            for _ in range(20):
                mid = (lo + hi) / 2
                if _moon_altitude(mid, lat_deg, lon_deg) < 0:
                    lo = mid
                else:
                    hi = mid
            return round((lo + hi) / 2, 4)

        prev_alt = alt

    return None


def moonset(jd: float, lat_deg: float, lon_deg: float) -> Optional[float]:
    """
    Find next moonset after the given JD.

    Args:
        jd:      Starting Julian Day
        lat_deg: Observer latitude (degrees)
        lon_deg: Observer longitude (degrees, east positive)

    Returns:
        JD of next moonset, or None if Moon is circumpolar
    """
    prev_alt = _moon_altitude(jd, lat_deg, lon_deg)
    t = jd

    for _ in range(_SCAN_RANGE):
        t += _SCAN_STEP
        alt = _moon_altitude(t, lat_deg, lon_deg)

        if prev_alt >= 0 and alt < 0:
            lo, hi = t - _SCAN_STEP, t
            for _ in range(20):
                mid = (lo + hi) / 2
                if _moon_altitude(mid, lat_deg, lon_deg) >= 0:
                    lo = mid
                else:
                    hi = mid
            return round((lo + hi) / 2, 4)

        prev_alt = alt

    return None


# -----------------------------------------------------------------
#  CRESCENT GEOMETRY -- SS Ch.10 v.6-10
# -----------------------------------------------------------------

def crescent_width(jd: float) -> float:
    """
    Width (bahu) of the illuminated crescent in arcminutes.

    The lit width along the Moon's axis is R * versine(elongation)
    = R * (1 - cos(elongation)) (SS Ch.10 bhashya on v.9, the utkrama-jya
    rule), where R is the Moon's apparent radius.

    Returns:
        Lit width in arcminutes: 0 at new moon, R at the quarters and the
        full disc diameter 2R at full moon.
    """
    elong = moon_elongation(jd)
    return round(MOON_APPARENT_RADIUS * (1.0 - math.cos(math.radians(elong))), 4)


def bright_limb_angle(jd: float) -> float:
    """
    Position angle of the Moon's bright limb.

    Measured from celestial north, through east (0-360 deg).
    The bright limb faces the Sun; the horns point opposite.

    SS Ch.10 v.7-8: direction of illumination from Moon to Sun.
    """
    sun_ra, sun_dec = _sun_equatorial(jd)
    moon_ra, moon_dec = _moon_equatorial(jd)

    dra_r = math.radians(sun_ra - moon_ra)
    dec_m_r = math.radians(moon_dec)
    dec_s_r = math.radians(sun_dec)

    num = math.cos(dec_s_r) * math.sin(dra_r)
    den = (math.sin(dec_s_r) * math.cos(dec_m_r)
           - math.cos(dec_s_r) * math.sin(dec_m_r) * math.cos(dra_r))

    return normalize(math.degrees(math.atan2(num, den)))


def _parallactic_angle(ra: float, dec: float,
                       lat_deg: float, lon_deg: float,
                       jd: float) -> float:
    """Full-quadrant parallactic angle at a celestial position (degrees)."""
    lst = local_sidereal_time(jd, lon_deg)
    ha = normalize(lst - ra)
    if ha > 180:
        ha -= 360

    lat_r = math.radians(lat_deg)
    dec_r = math.radians(dec)
    ha_r = math.radians(ha)
    y = math.cos(lat_r) * math.sin(ha_r)
    x = (math.sin(lat_r) * math.cos(dec_r)
         - math.cos(lat_r) * math.sin(dec_r) * math.cos(ha_r))
    return math.degrees(math.atan2(y, x))


def horn_angle(jd: float, lat_deg: float, lon_deg: float) -> float:
    """
    Apparent tilt of the crescent horn axis.

    Combines the bright limb position angle with the parallactic
    angle at the Moon's position to give the orientation of the
    horns as seen by the observer.

    Modern position-angle overlay illustrating the valana (deflection)
    of SS Ch.10 v.9-10; not the text's graphical horn construction.

    Returns:
        Angle in degrees. 0 = horns aligned north-south,
        90 = horns aligned east-west.
    """
    bla = bright_limb_angle(jd)
    moon_ra, moon_dec = _moon_equatorial(jd)
    q = _parallactic_angle(moon_ra, moon_dec, lat_deg, lon_deg, jd)
    horn_axis = normalize(bla + 90.0 - q)
    return round(horn_axis, 4)
