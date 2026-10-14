"""
Chapter 2: True Places of the Planets (Spashṭādhikāra)
=======================================================

Implements the Surya Siddhanta methods for computing true (apparent)
planetary positions from mean positions using epicyclic corrections.

This chapter covers:
- The 24-entry jyā (sine) table with R = 3438 arcminutes (v.17-22)
- Angle utilities: normalization, bhuja/koti derivation (v.28-30)
- Manda (equation of centre) correction (v.39-43)
- Sighra (synodic) correction (v.40-45)
- Full 4-step true-position pipeline (v.43-60)
- Planet position pipeline: compute(), compute_all()
- Ayanamsha (precession) for tropical conversion

Reference: Burgess (1860) ch.2, pp.196-260
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

from suryasiddhanta._types import EpicyclePair, PlanetPosition
from suryasiddhanta.ch01_mean_motions import (
    mean_longitude, mandocca_longitude, sighrocca_longitude,
    ahargana, julian_day, from_julian_day, kali_years_elapsed,
    rashi_from_longitude, nakshatra_from_longitude,
    ALL_PLANETS,
)

# ─────────────────────────────────────────────────────────────────
#  SS SINE TABLE CONSTANTS
# ─────────────────────────────────────────────────────────────────

R_SINE = 3438

JYA_TABLE = [
    225,  449,  671,  890, 1105, 1315, 1520, 1719,
    1910, 2093, 2267, 2431, 2585, 2728, 2859, 2978,
    3084, 3177, 3256, 3321, 3372, 3409, 3431, 3438,
]

JYA_STEP_ARCMIN = 225

OBLIQUITY_DEGREES = 24.0


# ─────────────────────────────────────────────────────────────────
#  ANGLE UTILITIES
# ─────────────────────────────────────────────────────────────────

def normalize(degrees: float) -> float:
    """Normalize angle to [0, 360)."""
    return degrees % 360.0


def normalize_signed(degrees: float) -> float:
    """Normalize angle to (-180, 180]."""
    d = degrees % 360.0
    return d - 360.0 if d > 180.0 else d


def to_dms(degrees: float) -> Tuple[int, int, float]:
    """Decimal degrees -> (degrees, arcminutes, arcseconds)."""
    d = int(degrees)
    m_float = (degrees - d) * 60
    m = int(m_float)
    s = (m_float - m) * 60
    return d, m, s


def from_dms(d: int, m: int, s: float) -> float:
    """(degrees, arcminutes, arcseconds) -> decimal degrees."""
    return d + m / 60.0 + s / 3600.0


def angular_error(a: float, b: float) -> float:
    """Minimum angular difference (0-180) between two angles."""
    diff = abs(normalize(a) - normalize(b))
    return diff if diff <= 180.0 else 360.0 - diff


# ─────────────────────────────────────────────────────────────────
#  UNIT CONVERSIONS
# ─────────────────────────────────────────────────────────────────

def deg_to_arcmin(d: float) -> float:
    return d * 60.0


def arcmin_to_deg(m: float) -> float:
    return m / 60.0


def deg_to_arcsec(d: float) -> float:
    return d * 3600.0


def arcsec_to_deg(s: float) -> float:
    return s / 3600.0


# ─────────────────────────────────────────────────────────────────
#  SS SINE (JYĀ) — R = 3438 arcminutes
#
#  24-entry table covers 0-90 deg in 3deg 45min (225 arcmin) steps.
#  Full circle handled by quadrant reduction.
#  SS Ch.2 v.17-22; Burgess (1860) pp.200-210
# ─────────────────────────────────────────────────────────────────

def jya(angle_deg: float) -> float:
    """
    Compute jya (R * sin) using SS 24-entry table with linear interpolation.

    Returns R * sin(angle) where R = 3438 arcminutes.
    """
    a = normalize(float(angle_deg))

    if 0.0 <= a <= 90.0:
        bhuja, sign = a, 1
    elif a <= 180.0:
        bhuja, sign = 180.0 - a, 1
    elif a <= 270.0:
        bhuja, sign = a - 180.0, -1
    else:
        bhuja, sign = 360.0 - a, -1

    bhuja_arcmin = bhuja * 60.0
    idx = bhuja_arcmin / JYA_STEP_ARCMIN
    lo = int(idx)
    frac = idx - lo

    if lo >= len(JYA_TABLE):
        return sign * R_SINE

    lo_val = JYA_TABLE[lo - 1] if lo > 0 else 0.0
    hi_val = JYA_TABLE[lo] if lo < len(JYA_TABLE) else R_SINE

    return sign * (lo_val + frac * (hi_val - lo_val))


def jya_normalized(angle_deg: float) -> float:
    """SS-table sin normalized to [-1, 1]."""
    return jya(angle_deg) / R_SINE


def koti(angle_deg: float) -> float:
    """Kotijya (R * cos) = jya(90 - angle)."""
    return jya(90.0 - normalize_signed(angle_deg))


def utkrama_jya(angle_deg: float) -> float:
    """Utkramajya (versed sine): R * (1 - cos) = R - kotijya."""
    return R_SINE - koti(angle_deg)


def arcjya(value: float) -> float:
    """
    Inverse jya: given R * sin(x), return x in degrees.
    Linear interpolation in SS table. Returns [-90, 90].
    """
    sign = 1.0 if value >= 0 else -1.0
    v = min(abs(value), R_SINE)

    if v <= 0:
        return 0.0
    if v >= R_SINE:
        return sign * 90.0

    lo_idx = 0
    for i, val in enumerate(JYA_TABLE):
        if val >= v:
            lo_idx = i
            break

    lo_val = JYA_TABLE[lo_idx - 1] if lo_idx > 0 else 0.0
    hi_val = JYA_TABLE[lo_idx]

    if hi_val == lo_val:
        frac = 0.0
    else:
        frac = (v - lo_val) / (hi_val - lo_val)

    angle_arcmin = (lo_idx + frac) * JYA_STEP_ARCMIN
    return sign * (angle_arcmin / 60.0)


# ─────────────────────────────────────────────────────────────────
#  CONVENIENCE WRAPPERS
# ─────────────────────────────────────────────────────────────────

def ss_sin(angle_deg: float) -> float:
    """SS-table sine, [-1, 1] range."""
    return jya_normalized(angle_deg)


def ss_cos(angle_deg: float) -> float:
    """SS-table cosine, [-1, 1] range."""
    return koti(angle_deg) / R_SINE


def ss_arcsin(value: float) -> float:
    """SS-table arcsin, returns degrees."""
    return arcjya(value * R_SINE)


# ─────────────────────────────────────────────────────────────────
#  BHUJA AND KOTI DERIVATION (SS Ch.2 v.28-30)
# ─────────────────────────────────────────────────────────────────

def get_bhuja_koti(kendra_deg: float) -> Tuple[float, float]:
    """
    Derive bhuja (base) and koti (perpendicular) from kendra (anomaly).
    Returns (bhuja_deg, koti_deg), both in [0, 90].
    """
    k = normalize(kendra_deg)
    if k <= 90.0:
        return k, 90.0 - k
    elif k <= 180.0:
        return 180.0 - k, k - 90.0
    elif k <= 270.0:
        return k - 180.0, 270.0 - k
    else:
        return 360.0 - k, k - 270.0


def get_quadrant(angle_deg: float) -> int:
    """Return quadrant (1-4) for given angle."""
    a = normalize(angle_deg)
    if a < 90:
        return 1
    if a < 180:
        return 2
    if a < 270:
        return 3
    return 4


def is_odd_quadrant(angle_deg: float) -> bool:
    """True if angle in odd quadrant (1 or 3)."""
    return get_quadrant(angle_deg) in (1, 3)


# ─────────────────────────────────────────────────────────────────
#  SS TABLE ACCURACY ANALYSIS
# ─────────────────────────────────────────────────────────────────

def table_accuracy_report() -> dict:
    """Compare SS jya table against modern sin. Returns angle -> stats."""
    report = {}
    for i in range(24):
        angle_arcmin = (i + 1) * JYA_STEP_ARCMIN
        angle_deg = angle_arcmin / 60.0
        ss_val = JYA_TABLE[i]
        modern_val = R_SINE * math.sin(math.radians(angle_deg))
        error = abs(ss_val - modern_val)
        report[angle_deg] = {
            "ss_jya": ss_val,
            "modern_val": round(modern_val, 2),
            "error": round(error, 2),
            "error_pct": round(error / modern_val * 100, 4) if modern_val else 0,
        }
    return report


# ─────────────────────────────────────────────────────────────────
#  EPICYCLE CONSTANTS (SS Ch.2 v.34-38)
#
#  v.34: Sun 14, Moon 32 deg at the end of the even quadrants;
#        "twenty minutes less for both" at the odd -> 13d40', 31d40'.
#  v.35-36: manda, even: 75, 30, 33, 12, 49;
#           odd: 72, 28, 32, 11, 48  (Mars, Mercury, Jupiter,
#           Venus, Saturn).
#  v.36-37: sighra, even: 235, 133, 70, 262, 39;
#           odd: 232, 132, 72, 260, 40.
#  EpicyclePair.at_bhuja pulsates even -> odd by sin(bhuja) (v.38).
# ─────────────────────────────────────────────────────────────────

MANDA_EPICYCLE = {
    "Sun":     EpicyclePair(even=14.0,  odd=13.0 + 40 / 60),
    "Moon":    EpicyclePair(even=32.0,  odd=31.0 + 40 / 60),
    "Mars":    EpicyclePair(even=75.0,  odd=72.0),
    "Mercury": EpicyclePair(even=30.0,  odd=28.0),
    "Jupiter": EpicyclePair(even=33.0,  odd=32.0),
    "Venus":   EpicyclePair(even=12.0,  odd=11.0),
    "Saturn":  EpicyclePair(even=49.0,  odd=48.0),
}

SIGHRA_EPICYCLE = {
    "Mars":    EpicyclePair(even=235.0, odd=232.0),
    "Mercury": EpicyclePair(even=133.0, odd=132.0),
    "Jupiter": EpicyclePair(even=70.0,  odd=72.0),
    "Venus":   EpicyclePair(even=262.0, odd=260.0),
    "Saturn":  EpicyclePair(even=39.0,  odd=40.0),
}

PLANETS_WITH_SIGHRA = list(SIGHRA_EPICYCLE.keys())


# ─────────────────────────────────────────────────────────────────
#  MANDA CORRECTION — Equation of Centre (SS Ch.2 v.28-43)
#
#  Corrects mean longitude for orbital eccentricity using
#  pulsating epicycles unique to SS.
# ─────────────────────────────────────────────────────────────────

def corrected_manda_epicycle(planet: str, kendra_deg: float) -> float:
    """Pulsating manda epicycle size at given kendra."""
    if planet not in MANDA_EPICYCLE:
        raise ValueError(f"No manda epicycle data for '{planet}'")
    return MANDA_EPICYCLE[planet].at_bhuja(get_bhuja_koti(kendra_deg)[0])


def manda_correction(
    planet: str,
    mean_lon_deg: float,
    mandocca_deg: float,
) -> float:
    """
    Manda correction (equation of centre).

    The SS manda kendra is mandocca - graha (Ch.2 v.29, v.45): the phala is
    positive (added) when that kendra is below 180 deg, negative above.
    Equivalently, with kendra = graha - mandocca as computed here, the phala is
    negative for 0-180 and positive for 180-360 (the body lags its mean place
    after apogee and leads it before apogee).

    manda_phala = arcsin(sin(bhuja) * periphery / 360)
    """
    if planet not in MANDA_EPICYCLE:
        raise ValueError(f"No manda data for '{planet}'")

    kendra = normalize(mean_lon_deg - mandocca_deg)
    bhuja, _ = get_bhuja_koti(kendra)

    periphery = corrected_manda_epicycle(planet, kendra)

    sin_bhuja = jya(bhuja) / R_SINE
    ratio = sin_bhuja * periphery / 360.0
    ratio = max(-1.0, min(1.0, ratio))
    manda_phala = math.degrees(math.asin(ratio))

    if kendra < 180.0:
        manda_phala = -manda_phala

    return manda_phala


def manda_longitude(
    planet: str,
    mean_lon_deg: float,
    mandocca_deg: float,
) -> float:
    """Apply manda correction -> manda-sphuta longitude [0, 360)."""
    return normalize(mean_lon_deg + manda_correction(planet, mean_lon_deg, mandocca_deg))


# ─────────────────────────────────────────────────────────────────
#  SIGHRA CORRECTION — Synodic Anomaly (SS Ch.2 v.43-60)
#
#  Models planet's position relative to Sun, producing retrograde.
#  Uses hypotenuse formula for the epicycle-on-deferent geometry.
# ─────────────────────────────────────────────────────────────────

def corrected_sighra_epicycle(planet: str, kendra_deg: float) -> float:
    """Pulsating sighra epicycle size at given kendra."""
    if planet not in SIGHRA_EPICYCLE:
        raise ValueError(f"No sighra data for '{planet}'. Sun/Moon have none.")
    return SIGHRA_EPICYCLE[planet].at_bhuja(get_bhuja_koti(kendra_deg)[0])


def sighra_correction(
    planet: str,
    manda_sphuta_deg: float,
    sighrocca_deg: float,
) -> float:
    """
    Sighra correction using hypotenuse formula.

    sighra_kendra = sighrocca - manda_sphuta
    H = sqrt((1 + r*cos_k)^2 + (r*sin_bhuja)^2)
    sighra_phala = arcsin(r * sin_bhuja / H)
    """
    if planet not in SIGHRA_EPICYCLE:
        raise ValueError(f"No sighra correction for '{planet}'")

    kendra = normalize(sighrocca_deg - manda_sphuta_deg)
    bhuja, _ = get_bhuja_koti(kendra)

    periphery = corrected_sighra_epicycle(planet, kendra)
    r = periphery / 360.0

    sin_bhuja = jya(bhuja) / R_SINE
    cos_bhuja = math.sqrt(max(0.0, 1.0 - sin_bhuja ** 2))

    if 90.0 < normalize(kendra) < 270.0:
        cos_k = -cos_bhuja
    else:
        cos_k = cos_bhuja

    H = math.sqrt((1.0 + r * cos_k) ** 2 + (r * sin_bhuja) ** 2)

    if H == 0:
        return 0.0

    sin_sighra = r * sin_bhuja / H
    sin_sighra = max(-1.0, min(1.0, sin_sighra))
    sighra_phala = math.degrees(math.asin(sin_sighra))

    if kendra > 180.0:
        sighra_phala = -sighra_phala

    return sighra_phala


# ─────────────────────────────────────────────────────────────────
#  FULL FOUR-STEP TRUE LONGITUDE PIPELINE (SS Ch.2 v.43-45)
#
#  "To the mean place of the planet apply half the equation of the
#   conjunction (sighraphala), likewise half the equation of the
#   apsis; to the mean place of the planet apply the whole equation
#   of the apsis (mandaphala), and also that of the conjunction."
#
#  Step 1: half sighra applied to mean
#  Step 2: half manda (computed from step-1 result) applied to that
#  Step 3: full manda computed from step-2 result,
#          applied to the ORIGINAL mean -> manda-sphuta
#  Step 4: full sighra from manda-sphuta -> true longitude
#
#  Sun/Moon: manda only (no sighra), v.39.
# ─────────────────────────────────────────────────────────────────

def true_longitude_full(planet: str, jd: float) -> dict:
    """
    Full 4-step SS true longitude pipeline.
    Returns dict with all intermediate values and final true_longitude.
    """
    mean_lon = mean_longitude(planet, jd)
    mandocca = mandocca_longitude(planet, jd)

    result = {
        "planet": planet,
        "jd": jd,
        "mean_lon": round(mean_lon, 4),
        "mandocca": round(mandocca, 4),
    }

    if planet in ("Sun", "Moon"):
        manda_corr = manda_correction(planet, mean_lon, mandocca)
        true_lon = normalize(mean_lon + manda_corr)
        result.update({
            "manda_kendra": round(normalize(mean_lon - mandocca), 4),
            "manda_corr": round(manda_corr, 4),
            "true_longitude": round(true_lon, 4),
            "steps": ["manda_only"],
        })
        return result

    sighrocca = sighrocca_longitude(planet, jd)
    result["sighrocca"] = round(sighrocca, 4)

    # Step 1: Half sighra applied to mean place (SS ii.43-44)
    sighra_corr1 = sighra_correction(planet, mean_lon, sighrocca)
    p1 = normalize(mean_lon + sighra_corr1 / 2.0)

    # Step 2: Half manda, computed from step-1 result
    manda_corr1 = manda_correction(planet, p1, mandocca)
    p2 = normalize(p1 + manda_corr1 / 2.0)

    # Step 3: Full manda from step-2 result, applied to ORIGINAL mean
    manda_corr2 = manda_correction(planet, p2, mandocca)
    ms2 = normalize(mean_lon + manda_corr2)

    # Step 4: Final sighra from manda-sphuta
    sighra_corr2 = sighra_correction(planet, ms2, sighrocca)
    true_lon = normalize(ms2 + sighra_corr2)

    result.update({
        "manda_kendra": round(normalize(mean_lon - mandocca), 4),
        "sighra_corr1": round(sighra_corr1, 4),
        "manda_corr1": round(manda_corr1, 4),
        "ms1": round(p2, 4),
        "manda_corr2": round(manda_corr2, 4),
        "ms2": round(ms2, 4),
        "sighra_kendra": round(normalize(sighrocca - ms2), 4),
        "sighra_corr2": round(sighra_corr2, 4),
        "true_longitude": round(true_lon, 4),
        "steps": ["half_sighra", "half_manda", "full_manda", "full_sighra"],
    })
    return result


# ─────────────────────────────────────────────────────────────────
#  CELESTIAL LATITUDE (VIKSHEPA / SHARA) — SS Ch.2 v.56-57
#
#  Latitude = sin(vikshepa-kendra) * mean latitude * R / antya-karna,
#  north when the kendra is under 180 deg.  Mean latitudes (SS Ch.1
#  v.68-70, arc-minutes): Moon 270, Mars 90, Mercury 120, Jupiter 60,
#  Venus 120, Saturn 120.
# ─────────────────────────────────────────────────────────────────

MADHYAMA_VIKSHEPA_ARCMIN: Dict[str, float] = {
    "Moon": 270.0, "Mars": 90.0, "Mercury": 120.0,
    "Jupiter": 60.0, "Venus": 120.0, "Saturn": 120.0,
}


def sighra_karna(planet: str, manda_sphuta_deg: float,
                 sighrocca_deg: float) -> float:
    """
    Final sighra karna (hypotenuse) in SS units where the deferent
    radius is R = 3438 (SS Ch.2 v.40-42), e.g. 3608 for the book's
    Jupiter example.
    """
    kendra = normalize(sighrocca_deg - manda_sphuta_deg)
    bhuja, _ = get_bhuja_koti(kendra)
    r = corrected_sighra_epicycle(planet, kendra) / 360.0
    sin_b = jya(bhuja) / R_SINE
    cos_b = math.sqrt(max(0.0, 1.0 - sin_b ** 2))
    cos_k = -cos_b if 90.0 < kendra < 270.0 else cos_b
    return R_SINE * math.sqrt((1.0 + r * cos_k) ** 2 + (r * sin_b) ** 2)


def spashta_vikshepa(kendra_deg: float, madhya_arcmin: float,
                     karna: float = R_SINE) -> float:
    """
    True latitude in arc-minutes (north positive) from the vikshepa
    kendra (planet minus node), SS Ch.2 v.57:
    madhya * Rsin(kendra) / karna.  Pass ``karna=R_SINE`` for the Moon,
    which has no sighra step.
    """
    sine = jya(normalize(kendra_deg) % 180.0)
    # jya() of a quadrant-reduced angle is positive; sign from the half
    lat = madhya_arcmin * sine / karna
    return lat if normalize(kendra_deg) < 180.0 else -lat


def planet_latitude(planet: str, jd: float) -> float:
    """
    Celestial latitude (shara) in arc-minutes, north positive.

    Moon: node distance of the true Moon.  Mars/Jupiter/Saturn: planet
    minus its node corrected by the second sighra phala.  Mercury/Venus:
    sighrocca minus its node corrected (reversed) by the second manda
    phala.  The Sun is on the ecliptic (0).
    """
    from suryasiddhanta.ch01_mean_motions import (
        planet_node_longitude, moon_node_longitude,
    )
    if planet == "Sun":
        return 0.0
    if planet == "Moon":
        t = true_longitude_full("Moon", jd)["true_longitude"]
        return spashta_vikshepa(t - moon_node_longitude(jd),
                                MADHYAMA_VIKSHEPA_ARCMIN["Moon"])
    if planet not in MADHYAMA_VIKSHEPA_ARCMIN:
        raise ValueError(f"No latitude data for '{planet}'")

    d = true_longitude_full(planet, jd)
    node = planet_node_longitude(planet, jd)
    if planet in ("Mercury", "Venus"):
        kendra = d["sighrocca"] - (node - d["manda_corr2"])
        karna = sighra_karna(planet, d["ms2"], d["sighrocca"])
    else:
        kendra = d["true_longitude"] - (node + d["sighra_corr2"])
        karna = sighra_karna(planet, d["ms2"], d["sighrocca"])
    return spashta_vikshepa(kendra, MADHYAMA_VIKSHEPA_ARCMIN[planet], karna)


# ─────────────────────────────────────────────────────────────────
#  AYANAMSHA (PRECESSION) — SS Ch.3 v.9-12
#
#  Libration (trepidation) model: the equinox librates +/-27 deg
#  about the initial point, 600 librations per Mahayuga -> period
#  7200 years, LINEAR in time (not sinusoidal): fold the cycle
#  angle into a signed bhuja of [-90, +90], then take three-tenths
#  of it (3:10 :: 27:90, per Burgess comm. under iii.9-12).
#  Zero at Kali 0 and Kali 3600 (499 CE); positive (equinox west
#  of the initial point, tropical = sidereal + ayanamsha) in the
#  half-cycle after 499 CE.
#
#  Burgess worked example: Jan 1, 1860 -> 20 deg 24' 38".67.
#  Placed here because compute() needs it; Ch.3 re-exports.
# ─────────────────────────────────────────────────────────────────

AYANAMSHA_AMPLITUDE = 27.0
AYANAMSHA_PERIOD = 7200
AYANAMSHA_ZERO_KALI = 3600.0


def ayanamsha(jd: float) -> float:
    """SS ayanamsha (precession offset) at given Julian Day."""
    kali_years = kali_years_elapsed(jd)
    cycle = (kali_years * 360.0 / AYANAMSHA_PERIOD) % 360.0

    # signed triangular fold of the cycle angle to [-90, +90]
    if cycle <= 90.0:
        bhuja = cycle
    elif cycle <= 270.0:
        bhuja = 180.0 - cycle
    else:
        bhuja = cycle - 360.0

    # three-tenths of the bhuja; sign flipped so the half-cycle
    # beginning at Kali 3600 (499 CE) gives positive ayanamsha
    return -bhuja * AYANAMSHA_AMPLITUDE / 90.0


def sidereal_to_tropical(sidereal_lon: float, jd: float) -> float:
    """Convert SS sidereal longitude to tropical."""
    return (sidereal_lon + ayanamsha(jd)) % 360.0


def tropical_to_sidereal(tropical_lon: float, jd: float) -> float:
    """Convert tropical longitude to SS sidereal."""
    return (tropical_lon - ayanamsha(jd)) % 360.0


# ─────────────────────────────────────────────────────────────────
#  PLANET POSITION PIPELINE
# ─────────────────────────────────────────────────────────────────

VALID_PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}


def compute(
    planet: str,
    year: int,
    month: int = 1,
    day: float = 1.0,
    gregorian: bool = None,
) -> PlanetPosition:
    """
    Compute complete planetary position for a calendar date.

    Args:
        planet:    One of Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn
        year:      CE year (negative for BCE)
        month:     1-12
        day:       1-31 (fractional for time of day)
        gregorian: Calendar of the given date. None (default) auto-selects
                   like julian_day(): Julian before 1582 Oct 15, Gregorian
                   after. Pass True/False to override.

    Returns:
        PlanetPosition with full SS computation results
    """
    if planet not in VALID_PLANETS:
        raise ValueError(f"Unknown planet '{planet}'. Valid: {sorted(VALID_PLANETS)}")

    jd = julian_day(year, month, float(day), gregorian=gregorian)
    ahan = ahargana(jd)
    ayan = ayanamsha(jd)

    result = true_longitude_full(planet, jd)
    true_lon = result["true_longitude"]
    mean_lon = result["mean_lon"]
    mandocca_val = result["mandocca"]
    manda_k = normalize(mean_lon - mandocca_val)

    if planet in ("Sun", "Moon"):
        manda_c = result["manda_corr"]
    else:
        manda_c = result.get("manda_corr2", 0.0)

    sighrocca_val = result.get("sighrocca")
    sighra_k = result.get("sighra_kendra")
    sighra_c = result.get("sighra_corr2")

    tropical = sidereal_to_tropical(true_lon, jd)

    nak_idx, nak_name, nak_pada, nak_deg = nakshatra_from_longitude(true_lon)
    rashi_idx, rashi_name, rashi_deg = rashi_from_longitude(true_lon)

    return PlanetPosition(
        planet=planet,
        jd=jd,
        year=year,
        month=month,
        day=int(day),
        ahargana=ahan,
        mean_lon=mean_lon,
        mandocca=mandocca_val,
        manda_kendra=manda_k,
        manda_corr=manda_c,
        sighrocca=sighrocca_val,
        sighra_kendra=sighra_k,
        sighra_corr=sighra_c,
        true_longitude=true_lon,
        ayanamsha=ayan,
        tropical_longitude=tropical,
        nakshatra={
            "index": nak_idx,
            "name": nak_name,
            "pada": nak_pada,
            "deg_in_nakshatra": nak_deg,
        },
        rashi={
            "index": rashi_idx,
            "name": rashi_name,
            "degrees": rashi_deg,
        },
    )


def compute_all(
    year: int,
    month: int = 1,
    day: float = 1.0,
    gregorian: bool = None,
) -> Dict[str, PlanetPosition]:
    """Compute positions for all seven classical planets."""
    return {
        p: compute(p, year, month, day, gregorian=gregorian)
        for p in ALL_PLANETS
    }
