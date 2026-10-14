"""
Chapter 3: Direction, Place, and Time (Triprashnādhikāra)
==========================================================

Coordinate transformations, gnomon shadows, sunrise/sunset,
and related positional astronomy from the Surya Siddhanta.

This chapter covers:
- Ecliptic to equatorial conversion (v.24-28)
- Declination, right ascension
- Equatorial to horizontal conversion
- Gnomon (shanku) shadow calculations (v.21-33)
- Sunrise/sunset hour angle (v.39-42)
- Day length in ghatis
- Local sidereal time (v.46)
- Cara (ascensional difference, v.42-44)
- Lagna (ascendant / rising sign, v.46-50)
- Direction from gnomon (dik)

Reference: SS Ch.3 v.1-50; Burgess (1860) pp.100-140
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

from suryasiddhanta._types import GnomonResult
from suryasiddhanta.ch01_mean_motions import RASHIS, jd_to_ut
from suryasiddhanta.ch02_true_places import (
    normalize, OBLIQUITY_DEGREES, tropical_to_sidereal,
)


# ─────────────────────────────────────────────────────────────────
#  ECLIPTIC <-> EQUATORIAL (SS Ch.3 v.24-28)
# ─────────────────────────────────────────────────────────────────

def ecliptic_to_equatorial(
    lon_deg: float,
    lat_deg: float = 0.0,
    obliquity: float = OBLIQUITY_DEGREES,
) -> Tuple[float, float]:
    """
    Convert ecliptic (lon, lat) to equatorial (RA, Dec).
    SS obliquity = 24 deg.

    Returns (right_ascension_deg, declination_deg).
    """
    lon_r = math.radians(lon_deg)
    lat_r = math.radians(lat_deg)
    eps_r = math.radians(obliquity)

    sin_dec = (math.sin(lat_r) * math.cos(eps_r) +
               math.cos(lat_r) * math.sin(eps_r) * math.sin(lon_r))
    dec_r = math.asin(max(-1.0, min(1.0, sin_dec)))
    dec_deg = math.degrees(dec_r)

    cos_dec = math.cos(dec_r)
    if abs(cos_dec) < 1e-10:
        return 0.0, dec_deg

    sin_ra_num = (math.cos(lat_r) * math.sin(lon_r) * math.cos(eps_r) -
                  math.sin(lat_r) * math.sin(eps_r))
    cos_ra_num = math.cos(lat_r) * math.cos(lon_r)

    ra_r = math.atan2(sin_ra_num, cos_ra_num)
    ra_deg = normalize(math.degrees(ra_r))

    return ra_deg, dec_deg


def declination(lon_deg: float, obliquity: float = OBLIQUITY_DEGREES) -> float:
    """
    Declination of a point on the ecliptic (zero latitude).
    delta = arcsin(sin(epsilon) * sin(lambda))
    """
    eps_r = math.radians(obliquity)
    lon_r = math.radians(lon_deg)
    sin_dec = math.sin(eps_r) * math.sin(lon_r)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_dec))))


def right_ascension(lon_deg: float, obliquity: float = OBLIQUITY_DEGREES) -> float:
    """Right ascension for ecliptic longitude (zero latitude). Returns [0, 360)."""
    ra, _ = ecliptic_to_equatorial(lon_deg, 0.0, obliquity)
    return ra


# ─────────────────────────────────────────────────────────────────
#  EQUATORIAL -> HORIZONTAL
# ─────────────────────────────────────────────────────────────────

def equatorial_to_horizontal(
    ra_deg: float,
    dec_deg: float,
    lst_deg: float,
    lat_deg: float,
) -> Tuple[float, float]:
    """
    Convert equatorial to horizontal (azimuth, altitude).
    Azimuth measured from North, clockwise.

    Args:
        ra_deg:  Right ascension (degrees)
        dec_deg: Declination (degrees)
        lst_deg: Local sidereal time (degrees)
        lat_deg: Observer latitude (degrees)

    Returns (azimuth_deg, altitude_deg).
    """
    hour_angle = normalize(lst_deg - ra_deg)
    h_r = math.radians(hour_angle)
    dec_r = math.radians(dec_deg)
    lat_r = math.radians(lat_deg)

    sin_alt = (math.sin(dec_r) * math.sin(lat_r) +
               math.cos(dec_r) * math.cos(lat_r) * math.cos(h_r))
    alt_r = math.asin(max(-1.0, min(1.0, sin_alt)))
    alt_deg = math.degrees(alt_r)

    cos_az_num = math.sin(dec_r) - math.sin(lat_r) * math.sin(alt_r)
    cos_az_den = math.cos(lat_r) * math.cos(alt_r)
    if abs(cos_az_den) < 1e-10:
        return 0.0, alt_deg

    az_r = math.acos(max(-1.0, min(1.0, cos_az_num / cos_az_den)))
    az_deg = math.degrees(az_r)
    if math.sin(h_r) > 0:
        az_deg = 360.0 - az_deg

    return az_deg, alt_deg


# ─────────────────────────────────────────────────────────────────
#  GNOMON SHADOW (SS Ch.3 v.21-33)
#
#  Standard SS gnomon = 12 angulas.
#  shadow = gnomon / tan(altitude)
# ─────────────────────────────────────────────────────────────────

def gnomon_shadow(
    sun_altitude_deg: float,
    gnomon_length: float = 12.0,
    *,
    sun_azimuth_deg: Optional[float] = None,
) -> GnomonResult:
    """
    Compute gnomon shadow length from solar altitude.
    A shadow direction requires the Sun's azimuth (clockwise from north).
    """
    if sun_altitude_deg <= 0:
        return GnomonResult(
            gnomon_length=gnomon_length,
            shadow_length=float('inf'),
            altitude_deg=sun_altitude_deg,
            azimuth_deg=None,
            direction="Sun below horizon",
        )

    alt_r = math.radians(sun_altitude_deg)
    shadow = gnomon_length / math.tan(alt_r)

    shadow_azimuth = None if sun_azimuth_deg is None else (sun_azimuth_deg + 180.0) % 360.0
    directions = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    direction = ("Undetermined" if shadow_azimuth is None else
                 directions[int((shadow_azimuth + 22.5) // 45.0) % 8])

    return GnomonResult(
        gnomon_length=gnomon_length,
        shadow_length=round(shadow, 4),
        altitude_deg=round(sun_altitude_deg, 4),
        azimuth_deg=shadow_azimuth,
        direction=direction,
    )


def solar_altitude_from_shadow(
    shadow_length: float,
    gnomon_length: float = 12.0,
) -> float:
    """Inverse gnomon: altitude = arctan(gnomon / shadow)."""
    if shadow_length <= 0:
        return 90.0
    return math.degrees(math.atan(gnomon_length / shadow_length))


# ─────────────────────────────────────────────────────────────────
#  SUNRISE / SUNSET (SS Ch.3 v.39-42)
# ─────────────────────────────────────────────────────────────────

def sunrise_hour_angle(lat_deg: float, dec_deg: float) -> float:
    """
    Hour angle at sunrise/sunset.
    cos(H) = -tan(phi) * tan(delta)
    Returns H in degrees (half of day arc).
    """
    lat_r = math.radians(lat_deg)
    dec_r = math.radians(dec_deg)
    cos_h = -math.tan(lat_r) * math.tan(dec_r)
    cos_h = max(-1.0, min(1.0, cos_h))
    return math.degrees(math.acos(cos_h))


def day_length_ghatis(lat_deg: float, sun_lon_deg: float) -> float:
    """
    Day length in ghatis (60 ghatis = 24 hours).
    Uses declination from Sun's longitude.
    """
    dec = declination(sun_lon_deg)
    H = sunrise_hour_angle(lat_deg, dec)
    return 60.0 * (2 * H / 360.0)


def night_length_ghatis(lat_deg: float, sun_lon_deg: float) -> float:
    """Night length in ghatis = 60 - day_length."""
    return 60.0 - day_length_ghatis(lat_deg, sun_lon_deg)


def sunrise_sunset_offset(lat_deg: float, dec_deg: float) -> float:
    """
    Time offset from noon to sunrise/sunset in hours.
    H / 15 converts hour angle degrees to hours.
    """
    H = sunrise_hour_angle(lat_deg, dec_deg)
    return H / 15.0


# ─────────────────────────────────────────────────────────────────
#  LOCAL SIDEREAL TIME
#
#  LST = GMST + observer_longitude (east positive)
#  GMST approximated from JD using standard formula, after converting
#  the library's Ujjain-mean-time JD to Universal Time.
# ─────────────────────────────────────────────────────────────────

def greenwich_mean_sidereal_time(jd: float) -> float:
    """
    GMST in degrees at a library JD. Standard IAU approximation.

    The IAU formula runs on Universal Time, while a library JD is in
    Ujjain mean time (ch01, i.50), so the JD is converted first. Reading
    it as UT instead would turn the sky about 76 degrees too far.
    """
    jd = jd_to_ut(jd)
    T = (jd - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + \
           0.000387933 * T * T - T * T * T / 38710000.0
    return normalize(gmst)


def local_sidereal_time(jd: float, observer_lon: float) -> float:
    """
    Local sidereal time in degrees.

    Args:
        jd:           Julian Day
        observer_lon: Observer longitude, east positive (degrees)

    Returns:
        LST in degrees [0, 360)
    """
    gmst = greenwich_mean_sidereal_time(jd)
    return normalize(gmst + observer_lon)


# ─────────────────────────────────────────────────────────────────
#  CARA — Ascensional Difference (SS Ch.3 v.42-44)
#
#  Cara = excess/deficit of half-day from 15 ghatis (6 hours).
#  cara = arcsin(tan(lat) * tan(dec)) converted to time.
# ─────────────────────────────────────────────────────────────────

def cara(lat_deg: float, dec_deg: float) -> float:
    """
    Ascensional difference (cara) in ghatis.

    Positive when day > night (summer in northern hemisphere).
    cara = arcsin(tan(lat) * tan(dec)) * (60 / 360)

    Args:
        lat_deg: Observer latitude (degrees)
        dec_deg: Solar declination (degrees)

    Returns:
        Cara in ghatis (add to 15 for half-day length)
    """
    lat_r = math.radians(lat_deg)
    dec_r = math.radians(dec_deg)
    sin_cara = math.tan(lat_r) * math.tan(dec_r)
    sin_cara = max(-1.0, min(1.0, sin_cara))
    cara_deg = math.degrees(math.asin(sin_cara))
    return cara_deg * 60.0 / 360.0


# ─────────────────────────────────────────────────────────────────
#  OBLIQUE ASCENSION — rising times of signs (SS Ch.3 v.46-50)
#
#  Right ascension intervals differ from ecliptic intervals due
#  to obliquity. At a given latitude, the rising time of each
#  sign is further modified by the cara.
# ─────────────────────────────────────────────────────────────────

def _right_ascension_interval(sign_start_lon: float, obliquity: float) -> float:
    """RA interval for a 30-deg ecliptic span starting at sign_start_lon."""
    ra_start = right_ascension(sign_start_lon, obliquity)
    ra_end = right_ascension(sign_start_lon + 30.0, obliquity)
    diff = ra_end - ra_start
    if diff < 0:
        diff += 360.0
    return diff


def _oblique_ascension_point(lon_deg: float, lat_deg: float) -> float:
    """Oblique ascension of a single ecliptic point: OA = RA - ascensional_diff."""
    ra = right_ascension(lon_deg, OBLIQUITY_DEGREES)
    dec = declination(lon_deg, OBLIQUITY_DEGREES)
    lat_r = math.radians(lat_deg)
    dec_r = math.radians(dec)
    sin_ad = math.tan(lat_r) * math.tan(dec_r)
    sin_ad = max(-1.0, min(1.0, sin_ad))
    ad = math.degrees(math.asin(sin_ad))
    return ra - ad


def oblique_ascension(sign_index: int, lat_deg: float) -> float:
    """
    Rising time of a rashi (zodiac sign) at given latitude, in degrees.

    Computed as difference of oblique ascensions at sign boundaries:
    OA(end) - OA(start), where OA(lambda) = RA(lambda) - arcsin(tan(phi)*tan(delta))

    Args:
        sign_index: 0 (Mesha) through 11 (Meena)
        lat_deg:    Observer latitude (degrees)

    Returns:
        Rising time in degrees of sidereal time
    """
    lon_start = sign_index * 30.0
    lon_end = lon_start + 30.0

    oa_start = _oblique_ascension_point(lon_start, lat_deg)
    oa_end = _oblique_ascension_point(lon_end, lat_deg)

    diff = oa_end - oa_start
    if diff < 0:
        diff += 360.0
    return diff


# ─────────────────────────────────────────────────────────────────
#  LAGNA — Ascendant / Rising Sign (SS Ch.3 v.46-50)
#
#  The lagna is the ecliptic degree rising on the eastern horizon.
#  Computed by finding which rashi is rising at the given LST.
# ─────────────────────────────────────────────────────────────────

def lagna(jd: float, lat_deg: float, lon_deg: float) -> Tuple[float, int, str]:
    """
    Compute the sidereal lagna (ascendant) — ecliptic degree on the eastern horizon.

    Uses oblique ascension of tropical sign intervals to determine which
    portion of the ecliptic is rising, then converts it to SS sidereal longitude.

    Args:
        jd:      Julian Day
        lat_deg: Observer latitude (degrees)
        lon_deg: Observer longitude, east positive (degrees)

    Returns:
        (lagna_degree, rashi_index, rashi_name)
    """
    # At rising, H = -90° - ascensional difference, so LST = OA - 90°.
    # Sign intervals below are tropical ecliptic intervals.
    rising_oa = normalize(local_sidereal_time(jd, lon_deg) + 90.0)

    rising_times = []
    for i in range(12):
        rising_times.append(oblique_ascension(i, lat_deg))

    cumulative = 0.0
    sign_idx = 0
    for i in range(12):
        if cumulative + rising_times[i] > rising_oa:
            sign_idx = i
            break
        cumulative += rising_times[i]
    else:
        sign_idx = 0
        cumulative = 0.0

    remaining = rising_oa - cumulative
    if rising_times[sign_idx] > 0:
        frac = remaining / rising_times[sign_idx]
    else:
        frac = 0.0
    frac = max(0.0, min(1.0, frac))

    tropical_deg = normalize(sign_idx * 30.0 + frac * 30.0)
    lagna_deg = tropical_to_sidereal(tropical_deg, jd)
    sidereal_sign_idx = int(lagna_deg // 30.0)
    return lagna_deg, sidereal_sign_idx, RASHIS[sidereal_sign_idx]


# ─────────────────────────────────────────────────────────────────
#  DIRECTION FROM GNOMON (SS Ch.3 v.17-20)
#
#  Two shadow measurements at different times give direction.
#  The midpoint of the shadow tips gives the N-S line.
# ─────────────────────────────────────────────────────────────────

def dik_from_gnomon(
    shadow_x1: float,
    shadow_y1: float,
    shadow_x2: float,
    shadow_y2: float,
    *,
    noon_shadow_direction: str,
) -> Tuple[float, str]:
    """
    Determine direction from two gnomon shadow-tip positions.

    The SS method (Ch.3 v.1-4): mark shadow tips at two equal-
    altitude times (morning and afternoon). The line connecting
    them runs E-W; the perpendicular bisector gives N-S.

    Args:
        shadow_x1, shadow_y1: First shadow tip (arbitrary coords)
        shadow_x2, shadow_y2: Second shadow tip
        noon_shadow_direction: Observed north/south direction of the noon shadow

    Returns:
        (angle_from_north_deg, cardinal_direction)
        Angle measured clockwise from North.
    """
    shadow_direction = noon_shadow_direction.lower()
    if shadow_direction not in ("north", "south"):
        raise ValueError("noon_shadow_direction must be 'north' or 'south'")

    mid_x = (shadow_x1 + shadow_x2) / 2.0
    mid_y = (shadow_y1 + shadow_y2) / 2.0

    ew_dx = shadow_x2 - shadow_x1
    ew_dy = shadow_y2 - shadow_y1

    # The perpendicular has two possible orientations. A physical noon
    # shadow observation identifies which side is north at this location/date.
    nx, ny = -ew_dy, ew_dx
    dot = nx * mid_x + ny * mid_y
    if abs(dot) < 1e-12:
        raise ValueError("shadow-tip midpoint does not orient the N-S line")
    if (dot < 0) == (shadow_direction == "north"):
        nx, ny = -nx, -ny
    ns_angle = normalize(math.degrees(math.atan2(nx, ny)))

    if ns_angle <= 22.5 or ns_angle > 337.5:
        direction = "N"
    elif ns_angle <= 67.5:
        direction = "NE"
    elif ns_angle <= 112.5:
        direction = "E"
    elif ns_angle <= 157.5:
        direction = "SE"
    elif ns_angle <= 202.5:
        direction = "S"
    elif ns_angle <= 247.5:
        direction = "SW"
    elif ns_angle <= 292.5:
        direction = "W"
    else:
        direction = "NW"

    return ns_angle, direction


def latitude_from_noon_shadow(
    shadow_length: float,
    sun_lon_deg: float,
    gnomon_length: float = 12.0,
    *,
    shadow_direction: str,
) -> float:
    """
    Derive observer latitude from noon shadow measurement.

    At local noon: altitude = 90 - |lat - dec|. The shadow points north
    when latitude exceeds the Sun's declination, south otherwise.

    Args:
        shadow_length: Noon shadow length (same units as gnomon)
        sun_lon_deg:   Sun's ecliptic longitude at noon
        gnomon_length: Gnomon height (default 12 angulas)
        shadow_direction: Observed north/south direction of the noon shadow

    Returns:
        Estimated latitude in degrees
    """
    altitude = solar_altitude_from_shadow(shadow_length, gnomon_length)
    dec = declination(sun_lon_deg)
    direction = shadow_direction.lower()
    if direction not in ("north", "south"):
        raise ValueError("shadow_direction must be 'north' or 'south'")
    zenith_distance = 90.0 - altitude
    lat = dec + zenith_distance if direction == "north" else dec - zenith_distance
    return lat
