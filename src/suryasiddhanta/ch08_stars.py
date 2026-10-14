"""
Chapter 8: Of the Stars (Taraganadhikara)
==========================================

SS Ch.8 catalogs the 27 nakshatras (lunar mansions) and their
yogatara (junction stars) with ecliptic coordinates.

  - **Nakshatra catalog**: 27 lunar mansions with yogatara
    coordinates, deities, and classifications
  - **Star position**: sidereal/tropical/equatorial at any epoch
  - **Star identification**: match observed position to catalog
  - **Rise/set times**: when a star rises and sets for an observer

Star positions in the catalog are sidereal (fixed). To obtain
tropical positions at a given epoch, the SS ayanamsha (trepidation
model) is applied.

Reference: SS Ch.8; Burgess (1860) pp.236-252
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from suryasiddhanta._types import Nakshatra
from suryasiddhanta.ch01_mean_motions import julian_day, from_julian_day
from suryasiddhanta.ch02_true_places import (
    normalize, ayanamsha, sidereal_to_tropical, OBLIQUITY_DEGREES,
)
from suryasiddhanta.ch03_direction_place_time import (
    ecliptic_to_equatorial, sunrise_hour_angle,
    local_sidereal_time, greenwich_mean_sidereal_time,
)


# -----------------------------------------------------------------
#  NAKSHATRA SPAN -- each = 360/27 = 13 deg 20 min
# -----------------------------------------------------------------

NAKSHATRA_SPAN = 360.0 / 27.0


# -----------------------------------------------------------------
#  FULL NAKSHATRA CATALOG -- SS Ch.8
#
#  Yogatara ecliptic coordinates (dhruvaka, viksepa) from
#  Burgess (1860) Table XVIII.  Spans are equal 13d20m arcs.
# -----------------------------------------------------------------

def _build_catalog() -> List[Nakshatra]:
    _data = [
        (1,  "Ashvini",            "अश्विनी",        "β Arietis",     8.0,   10.0, "Ashvini Kumaras", "Deva"),
        (2,  "Bharani",            "भरणी",           "35 Arietis",   20.0,   12.0, "Yama",            "Manushya"),
        (3,  "Krittika",           "कृत्तिका",        "η Tauri",      37.5,    5.0, "Agni",            "Rakshasa"),
        (4,  "Rohini",             "रोहिणी",          "α Tauri",      49.5,   -5.0, "Brahma",          "Manushya"),
        (5,  "Mrigashira",         "मृगशिरा",         "λ Orionis",    63.0,  -10.0, "Soma",            "Deva"),
        (6,  "Ardra",              "आर्द्रा",          "α Orionis",    67.0 + 20/60, -9.0, "Rudra",           "Manushya"),
        (7,  "Punarvasu",          "पुनर्वसु",         "β Geminorum",  93.0,    6.0, "Aditi",           "Deva"),
        (8,  "Pushya",             "पुष्य",           "δ Cancri",    106.0,    0.0, "Brihaspati",      "Deva"),
        (9,  "Ashlesha",           "आश्लेषा",         "ε Hydrae",    109.0,   -7.0, "Sarpa",           "Rakshasa"),
        (10, "Magha",              "मघा",            "α Leonis",    129.0,    0.0, "Pitris",          "Rakshasa"),
        (11, "Purva Phalguni",     "पूर्वफाल्गुनी",     "δ Leonis",    144.0,   12.0, "Bhaga",           "Manushya"),
        (12, "Uttara Phalguni",    "उत्तरफाल्गुनी",    "β Leonis",    155.0,   13.0, "Aryaman",         "Manushya"),
        (13, "Hasta",              "हस्ता",           "δ Corvi",     170.0,  -11.0, "Savitar",         "Deva"),
        (14, "Chitra",             "चित्रा",          "α Virginis",  180.0,   -2.0, "Tvashtar",        "Rakshasa"),
        (15, "Svati",              "स्वाती",           "α Bootis",    199.0,   37.0, "Vayu",            "Deva"),
        (16, "Vishakha",           "विशाखा",          "α Librae",    213.0,   -1.5, "Indragni",        "Rakshasa"),
        (17, "Anuradha",           "अनुराधा",         "δ Scorpii",   224.0,   -3.0, "Mitra",           "Deva"),
        (18, "Jyeshtha",           "ज्येष्ठा",         "α Scorpii",   229.0,   -4.0, "Indra",           "Rakshasa"),
        (19, "Mula",               "मूला",            "λ Scorpii",   241.0,   -9.0, "Nirriti",         "Rakshasa"),
        (20, "Purva Ashadha",      "पूर्वाषाढा",       "δ Sagittarii", 254.0,  -5.5, "Apas",            "Manushya"),
        (21, "Uttara Ashadha",     "उत्तराषाढा",      "σ Sagittarii", 260.0,  -5.0, "Vishvedevas",     "Manushya"),
        (22, "Shravana",           "श्रवणा",          "α Aquilae",   280.0,   30.0, "Vishnu",          "Deva"),
        (23, "Dhanishta",          "धनिष्ठा",         "β Delphini",  290.0,   36.0, "Vasus",           "Rakshasa"),
        (24, "Shatabhisha",        "शतभिषा",         "λ Aquarii",   320.0,   -0.5, "Varuna",          "Rakshasa"),
        (25, "Purva Bhadrapada",   "पूर्वभाद्रपदा",    "α Pegasi",    326.0,   24.0, "Aja Ekapada",     "Manushya"),
        (26, "Uttara Bhadrapada",  "उत्तरभाद्रपदा",   "γ Pegasi",    337.0,   26.0, "Ahir Budhnya",    "Manushya"),
        (27, "Revati",             "रेवती",           "ζ Piscium",   359.83,   0.0, "Pushan",          "Deva"),
    ]
    catalog = []
    for num, name, dev, star, lon, lat, deity, gana in _data:
        span_start = (num - 1) * NAKSHATRA_SPAN
        span_end = num * NAKSHATRA_SPAN
        catalog.append(Nakshatra(
            number=num, name=name, devanagari=dev,
            longitude=lon, latitude=lat, star=star,
            span_start=round(span_start, 4),
            span_end=round(span_end, 4),
            deity=deity, gana=gana,
        ))
    return catalog


NAKSHATRA_DATA: List[Nakshatra] = _build_catalog()

# SS Ch.8 recognizes 28 asterisms: Abhijit (alpha Lyrae / Vega) sits
# at the end of Purva-Ashadha's portion (viii.4), with the greatest
# latitude in the catalog (viii.6: 60 deg north), but receives no
# bhoga of its own in the 27-fold equal division (ii.64). It is kept
# out of NAKSHATRA_DATA so the span arithmetic stays 27-fold; its
# "span" is the zero-width point it occupies.
ABHIJIT = Nakshatra(
    number=28, name="Abhijit", devanagari="अभिजित",
    longitude=266.0 + 40 / 60, latitude=60.0, star="α Lyrae",
    span_start=266.0 + 40 / 60, span_end=266.0 + 40 / 60,
    deity="Brahma", gana="Deva",
)

_BY_NAME: Dict[str, Nakshatra] = {n.name: n for n in NAKSHATRA_DATA}
_BY_NAME[ABHIJIT.name] = ABHIJIT
_BY_NUMBER: Dict[int, Nakshatra] = {n.number: n for n in NAKSHATRA_DATA}
_BY_NUMBER[ABHIJIT.number] = ABHIJIT


# -----------------------------------------------------------------
#  CATALOG LOOKUP
# -----------------------------------------------------------------

def get_nakshatra(key) -> Nakshatra:
    """
    Look up nakshatra by name (str) or number (int).

    Raises:
        KeyError: if not found
    """
    if isinstance(key, int):
        if key not in _BY_NUMBER:
            raise KeyError(f"No nakshatra #{key}. Valid: 1-28")
        return _BY_NUMBER[key]
    if isinstance(key, str):
        if key not in _BY_NAME:
            available = ", ".join(sorted(_BY_NAME.keys()))
            raise KeyError(f"Unknown nakshatra '{key}'. Available: {available}")
        return _BY_NAME[key]
    raise TypeError(f"key must be str or int, got {type(key).__name__}")


def list_nakshatras() -> List[str]:
    """Return all 27 nakshatra names in order."""
    return [n.name for n in NAKSHATRA_DATA]


def load_catalog_json() -> dict:
    """Load the nakshatra catalog from the bundled JSON file."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    path = os.path.join(data_dir, "nakshatra_catalog.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------------------------------------------
#  STAR POSITION -- SS Ch.8 v.1-9
# -----------------------------------------------------------------

@dataclass
class StarPosition:
    """Computed position of a yogatara at a given epoch."""
    name: str
    sidereal_lon: float
    sidereal_lat: float
    tropical_lon: float
    ayanamsha_val: float
    right_ascension: float
    declination_val: float

    def __str__(self) -> str:
        return (
            f"Star: {self.name}\n"
            f"  Sidereal  : {self.sidereal_lon:.2f} deg lon, "
            f"{self.sidereal_lat:.2f} deg lat\n"
            f"  Tropical  : {self.tropical_lon:.2f} deg\n"
            f"  Ayanamsha : {self.ayanamsha_val:.4f} deg\n"
            f"  RA        : {self.right_ascension:.2f} deg\n"
            f"  Dec       : {self.declination_val:.2f} deg\n"
        )


def star_position(name: str, jd: float) -> StarPosition:
    """
    Compute position of a yogatara at the given epoch.

    Applies SS ayanamsha to convert sidereal catalog position
    to tropical, then transforms to equatorial (RA, dec).

    Args:
        name: Nakshatra name (e.g. "Rohini")
        jd:   Julian Day

    Returns:
        StarPosition with sidereal, tropical, and equatorial coords
    """
    nak = get_nakshatra(name)
    ayan = ayanamsha(jd)
    trop_lon = normalize(nak.longitude + ayan)
    ra, dec = ecliptic_to_equatorial(trop_lon, nak.latitude)

    return StarPosition(
        name=nak.name,
        sidereal_lon=nak.longitude,
        sidereal_lat=nak.latitude,
        tropical_lon=round(trop_lon, 4),
        ayanamsha_val=round(ayan, 4),
        right_ascension=round(ra, 4),
        declination_val=round(dec, 4),
    )


# -----------------------------------------------------------------
#  STAR IDENTIFICATION
# -----------------------------------------------------------------

def identify_star(lon_deg: float, lat_deg: float,
                  tolerance_deg: float = 5.0) -> List[Nakshatra]:
    """
    Find yogatara(s) near the given ecliptic position.

    Searches the catalog for stars within tolerance of (lon, lat)
    using great-circle angular separation. Returns matches sorted
    by proximity.

    Args:
        lon_deg:       Ecliptic longitude (sidereal, degrees)
        lat_deg:       Ecliptic latitude (degrees)
        tolerance_deg: Maximum separation in degrees (default 5)

    Returns:
        List of matching Nakshatra objects, nearest first
    """
    matches = []
    for nak in [*NAKSHATRA_DATA, ABHIJIT]:
        sep = _angular_sep(lon_deg, lat_deg, nak.longitude, nak.latitude)
        if sep <= tolerance_deg:
            matches.append((sep, nak))
    matches.sort(key=lambda x: x[0])
    return [nak for _, nak in matches]


def nearest_star(lon_deg: float, lat_deg: float) -> Tuple[Nakshatra, float]:
    """
    Find the yogatara nearest to the given position.

    Args:
        lon_deg: Ecliptic longitude (sidereal, degrees)
        lat_deg: Ecliptic latitude (degrees)

    Returns:
        (Nakshatra, separation_deg) tuple
    """
    best_nak = NAKSHATRA_DATA[0]
    best_sep = _angular_sep(lon_deg, lat_deg,
                            best_nak.longitude, best_nak.latitude)
    for nak in [*NAKSHATRA_DATA[1:], ABHIJIT]:
        sep = _angular_sep(lon_deg, lat_deg, nak.longitude, nak.latitude)
        if sep < best_sep:
            best_sep = sep
            best_nak = nak
    return best_nak, round(best_sep, 4)


def _angular_sep(lon1: float, lat1: float,
                 lon2: float, lat2: float) -> float:
    """Great-circle separation in degrees."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlon_r = math.radians(lon1 - lon2)
    cos_d = (math.sin(lat1_r) * math.sin(lat2_r)
             + math.cos(lat1_r) * math.cos(lat2_r) * math.cos(dlon_r))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_d))))


# -----------------------------------------------------------------
#  STAR RISE/SET -- using equatorial coordinates
# -----------------------------------------------------------------

SIDEREAL_RATE = 360.98564736629


@dataclass
class StarRiseSet:
    """Rise and set data for a star at a given location and date."""
    name: str
    rises: bool
    sets: bool
    is_circumpolar: bool
    is_never_visible: bool
    rise_jd: Optional[float] = None
    set_jd: Optional[float] = None
    hour_angle_deg: float = 0.0

    def __str__(self) -> str:
        if self.is_circumpolar:
            return f"{self.name}: circumpolar (never sets)"
        if self.is_never_visible:
            return f"{self.name}: never rises at this latitude"
        lines = [f"{self.name}:"]
        if self.rise_jd is not None:
            y, m, d, f = from_julian_day(self.rise_jd)
            hrs = f * 24
            lines.append(f"  Rise: {y}-{m:02d}-{d:02d} {hrs:.2f}h")
        if self.set_jd is not None:
            y, m, d, f = from_julian_day(self.set_jd)
            hrs = f * 24
            lines.append(f"  Set : {y}-{m:02d}-{d:02d} {hrs:.2f}h")
        return "\n".join(lines)


def star_rise_set(name: str, jd: float,
                  lat_deg: float, lon_deg: float) -> StarRiseSet:
    """
    Compute next rise and set times for a yogatara.

    Uses the star's equatorial coordinates (RA, dec) at the
    given epoch and the observer's position to find when the
    star crosses the horizon.

    Args:
        name:    Nakshatra name
        jd:      Julian Day (starting search point)
        lat_deg: Observer latitude (degrees)
        lon_deg: Observer longitude (degrees, east positive)

    Returns:
        StarRiseSet with rise/set JDs and circumpolar status
    """
    pos = star_position(name, jd)
    ra = pos.right_ascension
    dec = pos.declination_val

    cos_h = -math.tan(math.radians(lat_deg)) * math.tan(math.radians(dec))

    if cos_h < -1.0:
        return StarRiseSet(
            name=name, rises=True, sets=False,
            is_circumpolar=True, is_never_visible=False,
        )
    if cos_h > 1.0:
        return StarRiseSet(
            name=name, rises=False, sets=False,
            is_circumpolar=False, is_never_visible=True,
        )

    H = math.degrees(math.acos(cos_h))

    lst_rise = normalize(ra - H)
    lst_set = normalize(ra + H)
    lst_now = local_sidereal_time(jd, lon_deg)

    dt_rise = normalize(lst_rise - lst_now) / SIDEREAL_RATE
    dt_set = normalize(lst_set - lst_now) / SIDEREAL_RATE

    if dt_rise < 1e-4:
        dt_rise += 1.0 / (SIDEREAL_RATE / 360.0)

    return StarRiseSet(
        name=name,
        rises=True, sets=True,
        is_circumpolar=False, is_never_visible=False,
        rise_jd=round(jd + dt_rise, 4),
        set_jd=round(jd + dt_set, 4),
        hour_angle_deg=round(H, 4),
    )


# -----------------------------------------------------------------
#  NAKSHATRA HOUSING -- which nakshatra contains a longitude
# -----------------------------------------------------------------

def nakshatra_of(sidereal_lon: float) -> Nakshatra:
    """
    Return the nakshatra containing the given sidereal longitude.

    Each nakshatra spans exactly 13 deg 20 min (360/27).

    Args:
        sidereal_lon: Sidereal ecliptic longitude in degrees

    Returns:
        Nakshatra object
    """
    lon = normalize(sidereal_lon)
    idx = int(lon / NAKSHATRA_SPAN)
    if idx >= 27:
        idx = 26
    return NAKSHATRA_DATA[idx]
