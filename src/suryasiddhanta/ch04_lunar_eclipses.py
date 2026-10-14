"""
Chapter 4: Eclipses of the Moon (Chandragrahanadhikara)
=======================================================

Lunar eclipse prediction using the Surya Siddhanta method:
apparent diameters, Moon's latitude (viksepa), eclipse magnitude,
half-duration, and totality timing.

Algorithm (SS Ch.4 v.1-18):
  1. Find nearest Full Moon (elongation = 180 deg)
  2. Compute Moon's latitude from node distance
  3. Check eclipse condition: |lat| < shadow_r + moon_r
  4. Magnitude = (shadow_r + moon_r - |lat|) / (2 * moon_r)
  5. Half-duration via sqrt discriminant / Moon speed

Reference: SS Ch.4; Burgess (1860) pp.130-170
"""

from __future__ import annotations

import math
from typing import Tuple

from suryasiddhanta._types import LunarEclipse
from suryasiddhanta.ch01_mean_motions import (
    julian_day, moon_node_longitude,
)
from suryasiddhanta.ch02_true_places import (
    normalize, compute,
)


# ─────────────────────────────────────────────────────────────────
#  APPARENT DIAMETERS (SS Ch.4 v.1-5)
#
#  True diameters (v.1): sun 6500 yojanas, moon 480; earth 1600
#  (i.59). On the moon's mean orbit 15 yojanas = 1 arcmin (v.3).
#  Sun's mean apparent diameter: 6500 / 4,331,500 (its orbit) of
#  21600' = 32'24".8. Moon: 480/15 = 32'. Mean shadow via the suci
#  rule (v.4-5): 1600 - (6500-1600)*480/6500 = 1238.15 yojanas
#  -> 82'32.6".
# ─────────────────────────────────────────────────────────────────

SUN_DIAMETER_YOJANA = 6500.0
MOON_DIAMETER_YOJANA = 480.0
EARTH_DIAMETER_YOJANA = 1600.0
YOJANA_PER_ARCMIN = 15.0

_SHADOW_YOJANA = EARTH_DIAMETER_YOJANA - (
    (SUN_DIAMETER_YOJANA - EARTH_DIAMETER_YOJANA)
    * MOON_DIAMETER_YOJANA / SUN_DIAMETER_YOJANA
)

APPARENT_DIAMETER_ARCMIN = {
    "Sun":    SUN_DIAMETER_YOJANA * 21600.0 / 4_331_500.0,   # 32.4137
    "Moon":   MOON_DIAMETER_YOJANA / YOJANA_PER_ARCMIN,      # 32.0
    "Shadow": _SHADOW_YOJANA / YOJANA_PER_ARCMIN,            # 82.5436
}

MAX_MOON_LATITUDE_ARCMIN = 270.0

# SS mean daily motions (i.29-34): moon 790'35", sun 59'8"
MOON_DAILY_MOTION_DEG = (790 + 35 / 60) / 60   # 13.1765
SUN_DAILY_MOTION_DEG = (59 + 8 / 60) / 60      # 0.9856
# Eclipse timing uses the RELATIVE motion (SS iv.13: "divide by the
# difference of the daily motions")
RELATIVE_DAILY_MOTION_DEG = MOON_DAILY_MOTION_DEG - SUN_DAILY_MOTION_DEG


def apparent_diameter_moon(jd: float) -> float:
    """
    Moon's corrected (sphuta) apparent diameter in arcminutes (SS iv.2).

    "These diameters, each multiplied by the true motion, and divided by
    the mean motion, of its own planet, give the corrected diameters."
    The Moon moves fastest, and so looks largest, near her perigee. Both
    motions are taken over the day centred on `jd`: the true one from the
    ch02 true longitude, the mean one from the ch01 mean longitude.
    """
    from suryasiddhanta.ch01_mean_motions import mean_longitude
    from suryasiddhanta.ch02_true_places import true_longitude_full
    true_motion = normalize(true_longitude_full("Moon", jd + 0.5)["true_longitude"]
                            - true_longitude_full("Moon", jd - 0.5)["true_longitude"])
    mean_motion = normalize(mean_longitude("Moon", jd + 0.5)
                            - mean_longitude("Moon", jd - 0.5))
    return APPARENT_DIAMETER_ARCMIN["Moon"] * true_motion / mean_motion


def apparent_diameter_sun(jd: float) -> float:
    """Sun's apparent diameter in arcminutes (constant at mean distance)."""
    return APPARENT_DIAMETER_ARCMIN["Sun"]


def earth_shadow_diameter(jd: float) -> float:
    """Earth's umbral shadow diameter at Moon's distance (arcminutes)."""
    return APPARENT_DIAMETER_ARCMIN["Shadow"]


# ─────────────────────────────────────────────────────────────────
#  MOON'S LATITUDE (VIKSEPA) — SS Ch.2 v.57 (Ch.4 v.6-8 give the node limits)
#
#  lat = 270 * sin(moon_lon - node_lon) arcminutes
#  Max latitude ~4.5 deg = 270 arcmin
# ─────────────────────────────────────────────────────────────────

def moon_latitude(moon_lon: float, node_lon: float) -> float:
    """
    Moon's celestial latitude in arcminutes.

    Args:
        moon_lon: Moon's true longitude (degrees)
        node_lon: Moon's ascending node longitude (degrees)

    Returns:
        Latitude in arcminutes (+ north, - south)
    """
    angle = normalize(moon_lon - node_lon)
    if angle > 180:
        angle -= 360
    return MAX_MOON_LATITUDE_ARCMIN * math.sin(math.radians(angle))


# ─────────────────────────────────────────────────────────────────
#  ECLIPSE CONDITIONS
# ─────────────────────────────────────────────────────────────────

def is_near_node(moon_lon: float, node_lon: float, tolerance_deg: float = 12.0) -> bool:
    """Check if Moon is near a node (eclipse possible)."""
    diff = abs(normalize(moon_lon - node_lon))
    if diff > 180:
        diff = 360 - diff
    return diff <= tolerance_deg or (180 - tolerance_deg) <= diff <= 180


def check_lunar_eclipse_condition(jd: float) -> Tuple[bool, float]:
    """
    Check if lunar eclipse possible at JD (should be near Full Moon).
    Returns (is_possible, moon_latitude_arcmin).
    """
    moon_pos = compute("Moon", *_jd_to_ymd(jd))
    node_lon = moon_node_longitude(jd)
    lat_arcmin = moon_latitude(moon_pos.true_longitude, node_lon)

    moon_r = apparent_diameter_moon(jd) / 2
    shadow_r = earth_shadow_diameter(jd) / 2
    limit = moon_r + shadow_r

    return abs(lat_arcmin) < limit, round(lat_arcmin, 2)


# ─────────────────────────────────────────────────────────────────
#  FULL MOON FINDER
# ─────────────────────────────────────────────────────────────────

def _jd_to_ymd(jd: float) -> Tuple[int, int, float]:
    """Convert JD back to (year, month, day) for compute()."""
    from suryasiddhanta.ch01_mean_motions import from_julian_day
    y, m, d, frac = from_julian_day(jd)
    return y, m, d + frac


def _full_moon_candidates(year: int, month: int, day: float) -> Tuple[float, float]:
    """Refine the adjacent full moons on either side of an input date."""
    sun_pos = compute("Sun", year, month, day)
    moon_pos = compute("Moon", year, month, day)
    elongation = normalize(moon_pos.true_longitude - sun_pos.true_longitude)
    forward = (180.0 - elongation) % 360.0 / RELATIVE_DAILY_MOTION_DEG
    backward = -((elongation - 180.0) % 360.0) / RELATIVE_DAILY_MOTION_DEG

    def refine(guess: float) -> float:
        for _ in range(15):
            sun = compute("Sun", year, month, guess)
            moon = compute("Moon", year, month, guess)
            diff = (normalize(moon.true_longitude - sun.true_longitude) - 180.0 + 180.0) % 360.0 - 180.0
            if abs(diff) < 0.01:
                break
            guess -= diff / RELATIVE_DAILY_MOTION_DEG
        return guess

    return refine(day + backward), refine(day + forward)


def find_full_moon(year: int, month: int, day: float = 15.0) -> float:
    """Return the full moon nearest the input date, as a fractional day."""
    return min(_full_moon_candidates(year, month, day), key=lambda candidate: abs(candidate - day))


# ─────────────────────────────────────────────────────────────────
#  LUNAR ECLIPSE COMPUTATION (SS Ch.4 v.1-18)
# ─────────────────────────────────────────────────────────────────

def compute_lunar_eclipse(year: int, month: int, day: float = 15.0) -> LunarEclipse:
    """
    Compute lunar eclipse parameters for a given Full Moon date.

    Args:
        year:  CE year
        month: Month containing Full Moon
        day:   Approximate day of Full Moon (default 15)

    Returns:
        LunarEclipse with type, magnitude, duration
    """
    candidates = _full_moon_candidates(year, month, day)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    month_length = julian_day(next_year, next_month, 1.0) - julian_day(year, month, 1.0)
    in_month = [candidate for candidate in candidates if 1.0 <= candidate < month_length + 1.0]
    if not in_month:
        raise ValueError("requested month has no full moon")
    day = min(in_month, key=lambda candidate: abs(candidate - day))
    jd = julian_day(year, month, day)

    moon_d = apparent_diameter_moon(jd)
    shad_d = earth_shadow_diameter(jd)
    node_lon = moon_node_longitude(jd)
    moon_pos = compute("Moon", year, month, day)
    moon_lon = moon_pos.true_longitude

    lat_arcmin = moon_latitude(moon_lon, node_lon)

    moon_r = moon_d / 2
    shad_r = shad_d / 2
    abs_lat = abs(lat_arcmin)

    if abs_lat >= moon_r + shad_r:
        return LunarEclipse(
            jd=round(jd, 2), is_eclipse=False, eclipse_type="none",
            moon_latitude=round(lat_arcmin, 2),
            moon_diameter=round(moon_d, 2),
            shadow_diameter=round(shad_d, 2),
            magnitude=0.0,
            half_duration=None, totality_half=None,
            notes="No eclipse: Moon outside shadow zone",
        )

    magnitude = (moon_r + shad_r - abs_lat) / (2 * moon_r)

    if abs_lat < shad_r - moon_r:
        eclipse_type = "total"
    else:
        eclipse_type = "partial"

    # arcmin per minute of the moon's approach to the shadow (SS iv.13:
    # difference of daily motions, since the shadow moves with the sun)
    moon_speed = RELATIVE_DAILY_MOTION_DEG * 60 / 1440.0

    discriminant = (moon_r + shad_r) ** 2 - abs_lat ** 2
    half_dur = math.sqrt(max(0, discriminant)) / moon_speed if moon_speed > 0 else 0.0

    disc_tot = (shad_r - moon_r) ** 2 - abs_lat ** 2
    if disc_tot > 0 and eclipse_type == "total":
        tot_half = math.sqrt(disc_tot) / moon_speed
    else:
        tot_half = None

    return LunarEclipse(
        jd=round(jd, 2), is_eclipse=True, eclipse_type=eclipse_type,
        moon_latitude=round(lat_arcmin, 2),
        moon_diameter=round(moon_d, 2),
        shadow_diameter=round(shad_d, 2),
        magnitude=round(magnitude, 4),
        half_duration=round(half_dur, 2),
        totality_half=round(tot_half, 2) if tot_half else None,
        notes=f"Moon latitude = {abs_lat:.1f}', limit = {moon_r + shad_r:.1f}'",
    )
