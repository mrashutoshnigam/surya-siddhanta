"""
Chapter 5: Eclipses of the Sun (Suryagrahanadhikara)
=====================================================

Solar eclipse prediction with topocentric parallax corrections.

The SS method (Ch.5 v.1-17) adds two observer-dependent corrections
that the lunar eclipse (Ch.4) does not need:

  - **Lambana** (longitude parallax): shifts the apparent conjunction
    time by projecting the Moon's horizontal parallax along the ecliptic.
  - **Nati** (latitude parallax): shifts the Moon's apparent latitude
    by projecting the parallax perpendicular to the ecliptic.

Both corrections use the *nonagesimal* (vitribha-lagna) — the highest
point of the ecliptic above the observer's horizon.

Reference: SS Ch.5; Burgess (1860) pp.170-200
"""

from __future__ import annotations

import math
from typing import Tuple

from suryasiddhanta._types import SolarEclipse
from suryasiddhanta.ch01_mean_motions import (
    julian_day, from_julian_day, moon_node_longitude,
)
from suryasiddhanta.ch02_true_places import (
    normalize, compute, OBLIQUITY_DEGREES, sidereal_to_tropical,
)
from suryasiddhanta.ch03_direction_place_time import (
    local_sidereal_time, declination, right_ascension,
)
from suryasiddhanta.ch04_lunar_eclipses import (
    APPARENT_DIAMETER_ARCMIN, MOON_DAILY_MOTION_DEG, SUN_DAILY_MOTION_DEG,
    RELATIVE_DAILY_MOTION_DEG,
    apparent_diameter_moon, moon_latitude,
)


# ─────────────────────────────────────────────────────────────────
#  CONSTANTS — SS parallax
#
#  SS treats horizontal parallax as 1/15 of the mean daily motion
#  ("the mean motion during 4 nadis", Burgess comm. under iv.1-3):
#  moon 790'35"/15 = 52.7', sun 59'8"/15 = 3.9'. The eclipse
#  parallax corrections use the DIFFERENCE of the two.
# ─────────────────────────────────────────────────────────────────

MOON_HP_ARCMIN = MOON_DAILY_MOTION_DEG * 60 / 15.0   # 52.71
SUN_HP_ARCMIN = SUN_DAILY_MOTION_DEG * 60 / 15.0     # 3.94
PARALLAX_DIFF_ARCMIN = MOON_HP_ARCMIN - SUN_HP_ARCMIN  # 48.76


# ─────────────────────────────────────────────────────────────────
#  NONAGESIMAL (VITRIBHA-LAGNA) — SS Ch.5 v.1-3
#
#  The nonagesimal is the ecliptic point with maximum altitude,
#  located 90 deg west of the ascendant along the ecliptic.
#  Its zenith distance (drk-ksepa) controls the parallax split.
# ─────────────────────────────────────────────────────────────────

def _lagna_longitude(lst_deg: float, lat_deg: float,
                     obliquity: float = OBLIQUITY_DEGREES) -> float:
    """Ecliptic longitude of the ascendant (lagna)."""
    eps_r = math.radians(obliquity)
    lst_r = math.radians(lst_deg)
    lat_r = math.radians(lat_deg)
    num = math.cos(lst_r)
    den = -(math.sin(eps_r) * math.tan(lat_r)
            + math.cos(eps_r) * math.sin(lst_r))
    result = math.degrees(math.atan2(num, den)) % 360.0
    if result == 360.0:
        result = 0.0
    return result


def nonagesimal(lst_deg: float, lat_deg: float,
                obliquity: float = OBLIQUITY_DEGREES) -> Tuple[float, float]:
    """
    Compute the nonagesimal (vitribha-lagna) and its drkksepa.

    The nonagesimal is the ecliptic point nearest the zenith, so the
    drkksepa (its zenith distance) equals the ecliptic latitude of the
    zenith, which is what the sine formula below returns directly.
    SS tracks that latitude's *direction* as well as its size, because
    the nati is applied toward or away from the north pole of the
    ecliptic accordingly — hence the signed return.

    Args:
        lst_deg:   Local sidereal time in degrees
        lat_deg:   Observer's geographic latitude
        obliquity: Obliquity of ecliptic (default SS 24 deg)

    Returns:
        (vitribha_longitude, drkksepa) in degrees. Vitribha is [0, 360);
        drkksepa is signed, positive when the zenith lies north of the
        ecliptic (nonagesimal south of the zenith).
    """
    lagna = _lagna_longitude(lst_deg, lat_deg, obliquity)
    vitribha = (lagna - 90.0) % 360.0

    eps_r = math.radians(obliquity)
    lst_r = math.radians(lst_deg)
    lat_r = math.radians(lat_deg)

    sin_drk = (math.sin(lat_r) * math.cos(eps_r)
               - math.cos(lat_r) * math.sin(eps_r) * math.sin(lst_r))
    drkksepa = math.degrees(math.asin(max(-1.0, min(1.0, sin_drk))))

    return vitribha, drkksepa


# ─────────────────────────────────────────────────────────────────
#  PARALLAX CORRECTIONS — SS Ch.5 v.4-18
# ─────────────────────────────────────────────────────────────────

def lambana_factor(drkksepa_deg: float, delta_deg: float) -> float:
    """
    Dimensionless lambana factor cos(drkksepa) * sin(delta) (SS Ch.5 v.6-8).

    Lambana in ghatis is 4 * this factor, where drkksepa is the zenith
    distance of the nonagesimal and delta the Moon's distance from it.
    """
    return math.cos(math.radians(drkksepa_deg)) * math.sin(math.radians(delta_deg))


def lambana_correction(jd: float, lat_deg: float, lon_deg: float) -> float:
    """
    Longitude parallax (lambana) — SS Ch.5 v.2-9.

    Shifts Moon's apparent ecliptic longitude, changing when the
    apparent conjunction occurs.  Depends on the Moon's angular
    distance from the nonagesimal along the ecliptic.

    Args:
        jd:      Julian Day Number
        lat_deg: Observer latitude (degrees)
        lon_deg: Observer longitude (degrees, east positive)

    Returns:
        Shift of the apparent conjunction in arcminutes of relative
        motion (+ = conjunction later, Moon still to reach the Sun).
    """
    lst = local_sidereal_time(jd, lon_deg)
    vitribha_lon, drkksepa = nonagesimal(lst, lat_deg)

    y, m, d_frac = _jd_to_ymd(jd)
    moon_pos = compute("Moon", y, m, d_frac)
    # The nonagesimal comes from sidereal time, a tropical frame, so the
    # Moon's sidereal longitude must be converted before differencing
    # (the book works throughout in sayana longitudes).
    moon_tropical = sidereal_to_tropical(moon_pos.true_longitude, jd)
    delta = normalize(moon_tropical - vitribha_lon)
    if delta > 180:
        delta -= 360

    # Parallax pushes the Moon away from the zenith, i.e. away from the
    # nonagesimal along the ecliptic, so a Moon east of the nonagesimal
    # is carried further east and reaches apparent conjunction sooner.
    return -PARALLAX_DIFF_ARCMIN * lambana_factor(drkksepa, delta)


def nati_correction(jd: float, lat_deg: float, lon_deg: float) -> float:
    """
    Latitude parallax (nati) — SS Ch.5 v.10-12.

    Shifts Moon's apparent ecliptic latitude, changing whether
    an eclipse is visible and its magnitude.

    Args:
        jd:      Julian Day Number
        lat_deg: Observer latitude (degrees)
        lon_deg: Observer longitude (degrees, east positive)

    Returns:
        Shift of the Moon's apparent latitude in arcminutes
        (+ = north). Opposite in sign to the drkksepa, since parallax
        carries the Moon away from the zenith.
    """
    lst = local_sidereal_time(jd, lon_deg)
    _, drkksepa = nonagesimal(lst, lat_deg)
    return -PARALLAX_DIFF_ARCMIN * math.sin(math.radians(drkksepa))


# ─────────────────────────────────────────────────────────────────
#  NEW MOON FINDER
# ─────────────────────────────────────────────────────────────────

def _jd_to_ymd(jd: float) -> Tuple[int, int, float]:
    """Convert JD to (year, month, day_fraction) for compute()."""
    y, m, d, frac = from_julian_day(jd)
    return y, m, d + frac


def find_new_moon(year: int, month: int, day: float = 1.0) -> float:
    """
    Iteratively find nearest New Moon (elongation = 0 deg).
    Returns refined day (fractional).
    """
    for _ in range(15):
        sun_pos = compute("Sun", year, month, day)
        moon_pos = compute("Moon", year, month, day)
        elongation = normalize(moon_pos.true_longitude - sun_pos.true_longitude)
        diff = elongation if elongation <= 180 else elongation - 360
        if abs(diff) < 0.01:
            break
        day -= diff / RELATIVE_DAILY_MOTION_DEG
    return day


# ─────────────────────────────────────────────────────────────────
#  ECLIPSE EVALUATION (shared geometry)
# ─────────────────────────────────────────────────────────────────

def _evaluate(jd: float, lat_arcmin: float, sun_d: float, moon_d: float,
              notes: str = "", **extra) -> SolarEclipse:
    """Evaluate solar eclipse from geometric parameters."""
    sun_r = sun_d / 2
    moon_r = moon_d / 2
    abs_lat = abs(lat_arcmin)

    if abs_lat >= sun_r + moon_r:
        return SolarEclipse(
            jd=round(jd, 2), is_eclipse=False, eclipse_type="none",
            sun_diameter=round(sun_d, 2), moon_diameter=round(moon_d, 2),
            magnitude=0.0,
            moon_latitude=round(lat_arcmin, 2),
            notes=notes or "No eclipse: Moon outside solar disc zone",
            **extra,
        )

    magnitude = (sun_r + moon_r - abs_lat) / (2 * sun_r)

    if moon_d >= sun_d and abs_lat < moon_r - sun_r:
        eclipse_type = "total"
    elif moon_d < sun_d and abs_lat < sun_r - moon_r:
        eclipse_type = "annular"
    else:
        eclipse_type = "partial"

    moon_speed = RELATIVE_DAILY_MOTION_DEG * 60 / 1440.0
    discriminant = (sun_r + moon_r) ** 2 - abs_lat ** 2
    half_dur = (math.sqrt(max(0, discriminant)) / moon_speed
                if moon_speed > 0 else 0.0)

    return SolarEclipse(
        jd=round(jd, 2), is_eclipse=True, eclipse_type=eclipse_type,
        sun_diameter=round(sun_d, 2), moon_diameter=round(moon_d, 2),
        magnitude=round(magnitude, 4),
        moon_latitude=round(lat_arcmin, 2),
        half_duration=round(half_dur, 2),
        notes=notes or f"Moon lat={abs_lat:.1f}', limit={sun_r + moon_r:.1f}'",
        **extra,
    )


# ─────────────────────────────────────────────────────────────────
#  GEOCENTRIC SOLAR ECLIPSE (no parallax)
# ─────────────────────────────────────────────────────────────────

def compute_solar_eclipse(year: int, month: int, day: float = 1.0) -> SolarEclipse:
    """
    Geocentric solar eclipse (no observer-dependent parallax).

    Finds nearest New Moon, then checks if Moon's latitude is small
    enough for the lunar disc to overlap the solar disc.

    Args:
        year:  CE year
        month: Month containing approximate New Moon
        day:   Starting guess for day (default 1)

    Returns:
        SolarEclipse with geocentric geometry
    """
    day = find_new_moon(year, month, day)
    jd = julian_day(year, month, day)

    moon_pos = compute("Moon", year, month, day)
    node_lon = moon_node_longitude(jd)
    lat_arcmin = moon_latitude(moon_pos.true_longitude, node_lon)

    sun_d = APPARENT_DIAMETER_ARCMIN["Sun"]
    moon_d = apparent_diameter_moon(jd)

    return _evaluate(jd, lat_arcmin, sun_d, moon_d,
                     notes="Geocentric (no parallax)")


# ─────────────────────────────────────────────────────────────────
#  TOPOCENTRIC SOLAR ECLIPSE — SS Ch.5 full pipeline
# ─────────────────────────────────────────────────────────────────

def compute_solar_eclipse_topocentric(
    year: int, month: int, day: float,
    lat_deg: float, lon_deg: float,
) -> SolarEclipse:
    """
    Topocentric solar eclipse with full SS parallax corrections.

    Pipeline:
      1. Find geocentric New Moon
      2. Compute lambana → shift conjunction JD
      3. Compute nati → shift apparent Moon latitude
      4. Re-evaluate eclipse geometry with corrected values

    Args:
        year:    CE year
        month:   Month containing approximate New Moon
        day:     Starting guess for day
        lat_deg: Observer latitude (degrees, north positive)
        lon_deg: Observer longitude (degrees, east positive)

    Returns:
        SolarEclipse with parallax-corrected geometry
    """
    day = find_new_moon(year, month, day)
    jd = julian_day(year, month, day)

    moon_pos = compute("Moon", year, month, day)
    node_lon = moon_node_longitude(jd)
    geo_lat = moon_latitude(moon_pos.true_longitude, node_lon)

    lam = lambana_correction(jd, lat_deg, lon_deg)
    nat = nati_correction(jd, lat_deg, lon_deg)

    moon_speed_arcmin_day = RELATIVE_DAILY_MOTION_DEG * 60
    jd_corrected = jd + lam / moon_speed_arcmin_day
    lat_corrected = geo_lat + nat

    moon_d = apparent_diameter_moon(jd_corrected)
    sun_d = APPARENT_DIAMETER_ARCMIN["Sun"]

    # The overlap test is geometric. Daylight is an independent, local
    # condition evaluated at the corrected conjunction, using the Sun's
    # apparent position in the same tropical frame as sidereal time.
    cy, cm, cd = _jd_to_ymd(jd_corrected)
    sun_lon = sidereal_to_tropical(
        compute("Sun", cy, cm, cd).true_longitude, jd_corrected)
    sun_ra = right_ascension(sun_lon)
    sun_dec = declination(sun_lon)
    hour_angle = math.radians(local_sidereal_time(jd_corrected, lon_deg) - sun_ra)
    phi = math.radians(lat_deg)
    dec = math.radians(sun_dec)
    sin_alt = (math.sin(phi) * math.sin(dec)
               + math.cos(phi) * math.cos(dec) * math.cos(hour_angle))
    sun_altitude = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))

    return _evaluate(
        jd_corrected, lat_corrected, sun_d, moon_d,
        notes=(f"Topocentric ({lat_deg:.1f}°, {lon_deg:.1f}°E), "
               f"lambana={lam:.1f}', nati={nat:.1f}'"),
        lambana=round(lam, 2),
        nati=round(nat, 2),
        observer_lat=lat_deg,
        observer_lon=lon_deg,
        sun_altitude_deg=round(sun_altitude, 2),
        locally_visible=(abs(lat_corrected) < (sun_d + moon_d) / 2
                         and sun_altitude > 0.0),
    )
