"""
Chapter 7: Planetary Conjunctions (Grahayuddhadhikara)
======================================================

Conjunction detection and classification per SS Ch.7.

  - **Samagama** (conjunction): two planets at same ecliptic longitude
  - **Graha-yuddha** (planetary war): conjunction within 1 deg,
    the northern planet "wins" per SS Ch.7 v.20-21
  - **Planet-star**: planet passes near a yogatara (junction star)

The SS defines conjunction as equality of ecliptic longitude.
Planetary latitude enters the disc separation and is returned for each
body; winner determination is not computed in this model.

Reference: SS Ch.7; Burgess (1860) pp.221-235
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from suryasiddhanta.ch01_mean_motions import julian_day, from_julian_day
from suryasiddhanta.ch02_true_places import planet_latitude, normalize, compute


# -----------------------------------------------------------------
#  YOGATARA CATALOG -- SS Ch.8 junction stars (sidereal coordinates)
#
#  Ecliptic longitude (dhruvaka) and latitude (viksepa) for the
#  yogatara of each nakshatra, per Burgess (1860) Table XVIII.
#  Format: {name: (longitude_deg, latitude_deg)}
# -----------------------------------------------------------------

YOGATARA: Dict[str, Tuple[float, float]] = {
    "Ashvini":            (8.0,   10.0),
    "Bharani":            (20.0,  12.0),
    "Krittika":           (37.5,   5.0),
    "Rohini":             (49.5,  -5.0),
    "Mrigashira":         (63.0, -10.0),
    "Ardra":              (67.0 + 20/60, -9.0),
    "Punarvasu":          (93.0,   6.0),
    "Pushya":            (106.0,   0.0),
    "Ashlesha":          (109.0,  -7.0),
    "Magha":             (129.0,   0.0),
    "Purva Phalguni":    (144.0,  12.0),
    "Uttara Phalguni":   (155.0,  13.0),
    "Hasta":             (170.0, -11.0),
    "Chitra":            (180.0,  -2.0),
    "Svati":             (199.0,  37.0),
    "Vishakha":          (213.0,  -1.5),
    "Anuradha":          (224.0,  -3.0),
    "Jyeshtha":          (229.0,  -4.0),
    "Mula":              (241.0,  -9.0),
    "Purva Ashadha":     (254.0,  -5.5),
    "Uttara Ashadha":    (260.0,  -5.0),
    "Shravana":          (280.0,  30.0),
    "Dhanishta":         (290.0,  36.0),
    "Shatabhisha":       (320.0,  -0.5),
    "Purva Bhadrapada":  (326.0,  24.0),
    "Uttara Bhadrapada": (337.0,  26.0),
    "Revati":            (359.83,  0.0),
}

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Only the five star-planets (tara-graha) can fight: a planet meeting the
# Moon is a samagama and one meeting the Sun is set (SS Ch.7 v.1).
TARAGRAHA = frozenset({"Mars", "Mercury", "Jupiter", "Venus", "Saturn"})


# -----------------------------------------------------------------
#  CONJUNCTION RESULT
# -----------------------------------------------------------------

@dataclass
class Conjunction:
    """Result of a planetary conjunction computation."""
    body1: str
    body2: str
    jd: float
    longitude: float
    separation_deg: float
    conjunction_type: str
    body1_lat: float = 0.0
    body2_lat: float = 0.0
    notes: str = ""

    def __str__(self) -> str:
        y, m, d, frac = from_julian_day(self.jd)
        return (
            f"Conjunction: {self.body1} -- {self.body2}\n"
            f"  Date      : {y}-{m:02d}-{d:02d} ({frac:.2f} day)\n"
            f"  Longitude : {self.longitude:.2f} deg\n"
            f"  Separation: {self.separation_deg:.4f} deg\n"
            f"  Type      : {self.conjunction_type}\n"
        )


# -----------------------------------------------------------------
#  ANGULAR SEPARATION -- spherical geometry
# -----------------------------------------------------------------

def angular_separation(lon1: float, lat1: float,
                       lon2: float, lat2: float) -> float:
    """
    Great-circle angular separation between two ecliptic positions.

    Args:
        lon1, lat1: Ecliptic longitude/latitude of body 1 (degrees)
        lon2, lat2: Ecliptic longitude/latitude of body 2 (degrees)

    Returns:
        Angular separation in degrees (0 to 180)
    """
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlon_r = math.radians(lon1 - lon2)
    cos_d = (math.sin(lat1_r) * math.sin(lat2_r)
             + math.cos(lat1_r) * math.cos(lat2_r) * math.cos(dlon_r))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_d))))


def longitude_difference(lon1: float, lon2: float) -> float:
    """
    Signed ecliptic longitude difference, in range -180 to +180.
    Positive when lon1 is ahead of lon2 in the zodiac.
    """
    d = normalize(lon1 - lon2)
    return d - 360 if d > 180 else d


# -----------------------------------------------------------------
#  HELPERS
# -----------------------------------------------------------------

def _jd_to_ymd(jd: float) -> Tuple[int, int, float]:
    y, m, d, frac = from_julian_day(jd)
    return y, m, d + frac


def _planet_lon(planet: str, jd: float) -> float:
    """Sidereal longitude of planet at JD."""
    y, m, d_frac = _jd_to_ymd(jd)
    pos = compute(planet, y, m, d_frac)
    return pos.true_longitude


def _bisect_zero(diff_fn, lo: float, hi: float, n: int = 25) -> float:
    """Bisect to find zero crossing of diff_fn between lo and hi."""
    d_lo = diff_fn(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        d_mid = diff_fn(mid)
        if d_lo * d_mid <= 0:
            hi = mid
        else:
            lo = mid
            d_lo = d_mid
    return (lo + hi) / 2


# -----------------------------------------------------------------
#  CONJUNCTION SEARCH -- SS Ch.7 v.1-4
# -----------------------------------------------------------------

def find_conjunction(planet1: str, planet2: str,
                     start_jd: float, end_jd: float,
                     step: float = 1.0) -> List[Conjunction]:
    """
    Find all conjunctions (same ecliptic longitude) between two
    planets in the given JD range.

    Scans in daily steps, detects sign changes in longitude
    difference, then refines each crossing with bisection.

    Args:
        planet1:  First planet name
        planet2:  Second planet name
        start_jd: Start of search range (Julian Day)
        end_jd:   End of search range (Julian Day)
        step:     Scan step in days (default 1.0)

    Returns:
        List of Conjunction results, chronologically ordered
    """
    if planet1 == planet2:
        return []

    results = []
    jd = start_jd
    prev_diff = longitude_difference(
        _planet_lon(planet1, jd), _planet_lon(planet2, jd))

    while jd + step <= end_jd:
        jd += step
        curr_diff = longitude_difference(
            _planet_lon(planet1, jd), _planet_lon(planet2, jd))

        if (prev_diff * curr_diff < 0
                and abs(prev_diff) < 90
                and abs(curr_diff) < 90):

            p1, p2 = planet1, planet2
            diff_fn = lambda t, _p1=p1, _p2=p2: longitude_difference(
                _planet_lon(_p1, t), _planet_lon(_p2, t))
            conj_jd = _bisect_zero(diff_fn, jd - step, jd)

            lon1 = _planet_lon(planet1, conj_jd)
            lon2 = _planet_lon(planet2, conj_jd)
            # Separation of the discs includes the latitude difference
            # (SS Ch.7 v.12, v.18-22); at equal longitude it is just that.
            lat1 = planet_latitude(planet1, conj_jd) / 60.0
            lat2 = planet_latitude(planet2, conj_jd) / 60.0
            sep = angular_separation(lon1, lat1, lon2, lat2)
            conj_type = classify_conjunction(
                sep, both_taragraha=(planet1 in TARAGRAHA
                                     and planet2 in TARAGRAHA))

            results.append(Conjunction(
                body1=planet1,
                body2=planet2,
                jd=round(conj_jd, 4),
                longitude=round(normalize((lon1 + lon2) / 2), 4),
                separation_deg=round(sep, 4),
                conjunction_type=conj_type,
                body1_lat=round(lat1, 4),
                body2_lat=round(lat2, 4),
            ))

        prev_diff = curr_diff

    return results


def planet_planet_conjunction(planet1: str, planet2: str,
                              year: int, month: int = 1,
                              months: int = 12) -> List[Conjunction]:
    """
    Find all conjunctions between two planets over a span of months.

    Args:
        planet1: First planet (e.g. "Jupiter")
        planet2: Second planet (e.g. "Saturn")
        year:    Starting CE year
        month:   Starting month (default 1)
        months:  Number of months to search (default 12)

    Returns:
        List of Conjunction results
    """
    start_jd = julian_day(year, month, 1.0)
    end_jd = start_jd + months * 30.44
    return find_conjunction(planet1, planet2, start_jd, end_jd)


def planet_star_conjunction(planet: str, star_name: str,
                            year: int, months: int = 12) -> List[Conjunction]:
    """
    Find conjunctions of a planet with a yogatara (junction star).

    Detects when planet's sidereal longitude matches star's longitude.
    Retrograde planets can produce multiple crossings per year.

    Args:
        planet:    Planet name
        star_name: Name from YOGATARA catalog
        year:      Starting CE year
        months:    Search span in months (default 12)

    Returns:
        List of Conjunction results

    Raises:
        ValueError: If star_name not in YOGATARA catalog
    """
    if star_name not in YOGATARA:
        available = ", ".join(sorted(YOGATARA.keys()))
        raise ValueError(f"Unknown star '{star_name}'. Available: {available}")

    star_lon, star_lat = YOGATARA[star_name]
    start_jd = julian_day(year, 1, 1.0)
    end_jd = start_jd + months * 30.44

    results = []
    jd = start_jd
    prev_diff = longitude_difference(_planet_lon(planet, jd), star_lon)

    while jd + 1.0 <= end_jd:
        jd += 1.0
        curr_diff = longitude_difference(_planet_lon(planet, jd), star_lon)

        if (prev_diff * curr_diff < 0
                and abs(prev_diff) < 90
                and abs(curr_diff) < 90):

            s_lon = star_lon
            p = planet
            diff_fn = lambda t, _p=p, _sl=s_lon: longitude_difference(
                _planet_lon(_p, t), _sl)
            conj_jd = _bisect_zero(diff_fn, jd - 1.0, jd)

            planet_lon = _planet_lon(planet, conj_jd)
            planet_lat = planet_latitude(planet, conj_jd) / 60.0
            sep = angular_separation(planet_lon, planet_lat, star_lon, star_lat)

            results.append(Conjunction(
                body1=planet,
                body2=star_name,
                jd=round(conj_jd, 4),
                longitude=round(star_lon, 4),
                separation_deg=round(sep, 4),
                conjunction_type="star_conjunction",
                body1_lat=round(planet_lat, 4),
                body2_lat=star_lat,
                notes=f"Star at ({star_lon} deg, {star_lat} deg)",
            ))

        prev_diff = curr_diff

    return results


def nearest_conjunction(planet1: str, planet2: str,
                        jd: float,
                        search_days: float = 400.0) -> Optional[Conjunction]:
    """
    Find the conjunction nearest to the given JD.

    Searches +/- search_days around jd.

    Args:
        planet1:     First planet
        planet2:     Second planet
        jd:          Centre of search window (Julian Day)
        search_days: Half-width of search in days (default 400)

    Returns:
        Nearest Conjunction, or None if none found
    """
    results = find_conjunction(planet1, planet2,
                               jd - search_days, jd + search_days)
    if not results:
        return None
    return min(results, key=lambda c: abs(c.jd - jd))


# -----------------------------------------------------------------
#  CONJUNCTION CLASSIFICATION -- SS Ch.7 v.19-20
# -----------------------------------------------------------------

def classify_conjunction(separation_deg: float,
                         both_taragraha: bool = True) -> str:
    """
    Classify conjunction per SS Ch.7 v.19-20.

    - **yuddha** (war): discs within 1 deg, both planets tara-graha
    - **samagama** (meeting): every other conjunction (the text sets no
      upper bound)

    Args:
        separation_deg: Angular separation in degrees
        both_taragraha: False if either body is the Sun or Moon

    Returns:
        Classification string
    """
    if both_taragraha and separation_deg < 1.0:
        return "yuddha"
    return "samagama"
