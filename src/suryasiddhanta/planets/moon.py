"""
The Moon, gathered from every chapter that computes it.

A planet-wise view of the chapter modules: each function here is either a
chapter function with ``planet="Moon"`` already bound, under the same name
and with the remaining parameters unchanged, or a Moon chapter function
re-exported as it is. The chapter modules stay the one implementation;
nothing is computed here.

Functions that need the Sun and the Moon together sit where a reader
would look for them: the lunar eclipse, phases, horns and moonrise are
here, the solar eclipse and parallax are in ``sun``, and the
tithi/yoga/karana, panchanga, patas and eclipse projection are in both.
The Moon's node is also in ``rahu``.

Chapters drawn on: 1, 2, 4, 5, 6, 7, 10, 11, 12, 14.

Example::

    from suryasiddhanta.planets import moon
    moon.compute(2024, 4, 9).true_longitude
    moon.phase_name(2460410.5)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from suryasiddhanta import ch01_mean_motions as _ch01
from suryasiddhanta import ch02_true_places as _ch02
from suryasiddhanta import ch07_conjunctions as _ch07
from suryasiddhanta import ch12_cosmography as _ch12
from suryasiddhanta.ch01_mean_motions import (
    moon_node_longitude,
    tithi_from_elongation,
    yoga_from_longitudes,
    karana_from_elongation,
    compute_panchanga,
)
from suryasiddhanta.ch04_lunar_eclipses import (
    apparent_diameter_moon,
    earth_shadow_diameter,
    moon_latitude,
    is_near_node,
    check_lunar_eclipse_condition,
    find_full_moon,
    compute_lunar_eclipse,
    MOON_DIAMETER_YOJANA,
    MAX_MOON_LATITUDE_ARCMIN,
    MOON_DAILY_MOTION_DEG,
)
from suryasiddhanta.ch05_solar_eclipses import (
    MOON_HP_ARCMIN,
)
from suryasiddhanta.ch06_eclipse_projection import (
    eclipse_contact_points,
    project_eclipse_path,
    eclipse_diagram_data,
    plot_eclipse,
)
from suryasiddhanta.ch10_lunar_horns import (
    moon_elongation,
    illuminated_fraction,
    phase_name,
    is_waxing,
    crescent_width,
    bright_limb_angle,
    horn_angle,
    moonrise,
    moonset,
    MOON_APPARENT_RADIUS,
    PHASE_NAMES,
)
from suryasiddhanta.ch11_pata import (
    moon_latitude_deg,
    moon_declination,
    moon_declination_exact,
    longitude_sum,
    find_patas,
    find_next_pata,
    active_pata,
    VYATIPATA_SUM,
    VAIDHRITA_SUM,
    PATA_KINDS,
)
from suryasiddhanta.ch12_cosmography import (
    MOON_ORBIT_YOJANAS,
    SYNODIC_MONTH_DAYS,
)
from suryasiddhanta.ch14_reckoning_time import (
    pitrya_clock,
)

if TYPE_CHECKING:
    from suryasiddhanta._types import PlanetPosition
    from suryasiddhanta.ch07_conjunctions import Conjunction

# Name of the body.
NAME = "Moon"

# Revolutions in a mahayuga (SS i.29-34).
REVOLUTIONS_PER_MAHAYUGA = _ch01.BHAGANA[NAME]
# Mean daily motion, degrees per civil day.
MEAN_DAILY_MOTION = _ch01.MEAN_DAILY_MOTION[NAME]
# Revolutions of the apogee (mandocca) in a mahayuga (SS i.33).
APOGEE_REVOLUTIONS_PER_MAHAYUGA = _ch01.BHAGANA["Moon_apogee"]
# Apogee longitude at the Kali epoch, degrees.
MANDOCCA_AT_EPOCH = _ch01.MANDOCCA_AT_EPOCH[NAME]
# Manda epicycle at the even and odd quadrants, degrees (SS ii.34-37).
MANDA_EPICYCLE = _ch02.MANDA_EPICYCLE[NAME]
# Greatest latitude, arcminutes (SS i.68-70).
MADHYAMA_VIKSHEPA_ARCMIN = _ch02.MADHYAMA_VIKSHEPA_ARCMIN[NAME]

__all__ = [
    "NAME",
    "REVOLUTIONS_PER_MAHAYUGA",
    "MEAN_DAILY_MOTION",
    "APOGEE_REVOLUTIONS_PER_MAHAYUGA",
    "MANDOCCA_AT_EPOCH",
    "MANDA_EPICYCLE",
    "MADHYAMA_VIKSHEPA_ARCMIN",
    "mean_longitude",
    "mandocca_longitude",
    "corrected_manda_epicycle",
    "manda_correction",
    "manda_longitude",
    "true_longitude_full",
    "planet_latitude",
    "compute",
    "find_conjunction",
    "planet_planet_conjunction",
    "nearest_conjunction",
    "planet_star_conjunction",
    "orbit_yojanas",
    "daily_motion_arcmin",
    "orbit_diameter",
    "mean_distance",
    "moon_node_longitude",
    "tithi_from_elongation",
    "yoga_from_longitudes",
    "karana_from_elongation",
    "compute_panchanga",
    "apparent_diameter_moon",
    "earth_shadow_diameter",
    "moon_latitude",
    "is_near_node",
    "check_lunar_eclipse_condition",
    "find_full_moon",
    "compute_lunar_eclipse",
    "MOON_DIAMETER_YOJANA",
    "MAX_MOON_LATITUDE_ARCMIN",
    "MOON_DAILY_MOTION_DEG",
    "MOON_HP_ARCMIN",
    "eclipse_contact_points",
    "project_eclipse_path",
    "eclipse_diagram_data",
    "plot_eclipse",
    "moon_elongation",
    "illuminated_fraction",
    "phase_name",
    "is_waxing",
    "crescent_width",
    "bright_limb_angle",
    "horn_angle",
    "moonrise",
    "moonset",
    "MOON_APPARENT_RADIUS",
    "PHASE_NAMES",
    "moon_latitude_deg",
    "moon_declination",
    "moon_declination_exact",
    "longitude_sum",
    "find_patas",
    "find_next_pata",
    "active_pata",
    "VYATIPATA_SUM",
    "VAIDHRITA_SUM",
    "PATA_KINDS",
    "MOON_ORBIT_YOJANAS",
    "SYNODIC_MONTH_DAYS",
    "pitrya_clock",
]


def mean_longitude(jd: float) -> float:
    """
    Mean sidereal longitude of the Moon at a Julian Day, in degrees [0, 360).

    Bound form of ``ch01_mean_motions.mean_longitude`` with ``planet="Moon"``.
    """
    return _ch01.mean_longitude(NAME, jd)


def mandocca_longitude(jd: float) -> float:
    """
    Longitude of the Moon's mandocca (apex of the slow epicycle), in degrees.

    Bound form of ``ch01_mean_motions.mandocca_longitude`` with ``planet="Moon"``.
    """
    return _ch01.mandocca_longitude(NAME, jd)


def corrected_manda_epicycle(kendra_deg: float) -> float:
    """
    Size of the Moon's pulsating manda epicycle at a kendra, in degrees.

    Bound form of ``ch02_true_places.corrected_manda_epicycle`` with ``planet="Moon"``.
    """
    return _ch02.corrected_manda_epicycle(NAME, kendra_deg)


def manda_correction(mean_lon_deg: float, mandocca_deg: float) -> float:
    """
    Manda correction (equation of centre) for the Moon, in degrees.

    Bound form of ``ch02_true_places.manda_correction`` with ``planet="Moon"``.
    """
    return _ch02.manda_correction(NAME, mean_lon_deg, mandocca_deg)


def manda_longitude(mean_lon_deg: float, mandocca_deg: float) -> float:
    """
    The Moon's manda-sphuta longitude after the manda correction, in degrees [0, 360).

    Bound form of ``ch02_true_places.manda_longitude`` with ``planet="Moon"``.
    """
    return _ch02.manda_longitude(NAME, mean_lon_deg, mandocca_deg)


def true_longitude_full(jd: float) -> dict:
    """
    Every step of the Moon's true-longitude computation for a Julian Day, as a dict.

    Bound form of ``ch02_true_places.true_longitude_full`` with ``planet="Moon"``.
    """
    return _ch02.true_longitude_full(NAME, jd)


def planet_latitude(jd: float) -> float:
    """
    The Moon's celestial latitude (shara) in arcminutes, north positive.

    Bound form of ``ch02_true_places.planet_latitude`` with ``planet="Moon"``.
    """
    return _ch02.planet_latitude(NAME, jd)


def compute(year: int, month: int = 1, day: float = 1.0, gregorian: bool = None) -> PlanetPosition:
    """
    Complete position of the Moon for a calendar date.

    Bound form of ``ch02_true_places.compute`` with ``planet="Moon"``.
    """
    return _ch02.compute(NAME, year, month, day, gregorian)


def find_conjunction(other: str, start_jd: float, end_jd: float, step: float = 1.0) -> List[Conjunction]:
    """
    Every conjunction of the Moon with another body between two Julian Days.

    Bound form of ``ch07_conjunctions.find_conjunction`` with ``planet1="Moon"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.find_conjunction(NAME, other, start_jd, end_jd, step)


def planet_planet_conjunction(other: str, year: int, month: int = 1, months: int = 12) -> List[Conjunction]:
    """
    Every conjunction of the Moon with another body over a span of months.

    Bound form of ``ch07_conjunctions.planet_planet_conjunction`` with ``planet1="Moon"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.planet_planet_conjunction(NAME, other, year, month, months)


def nearest_conjunction(other: str, jd: float, search_days: float = 400.0) -> Optional[Conjunction]:
    """
    The conjunction of the Moon with another body nearest a Julian Day, or None.

    Bound form of ``ch07_conjunctions.nearest_conjunction`` with ``planet1="Moon"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.nearest_conjunction(NAME, other, jd, search_days)


def planet_star_conjunction(star_name: str, year: int, months: int = 12) -> List[Conjunction]:
    """
    Conjunctions of the Moon with a yogatara (junction star) over a span of months.

    Bound form of ``ch07_conjunctions.planet_star_conjunction`` with ``planet="Moon"``.
    """
    return _ch07.planet_star_conjunction(NAME, star_name, year, months)


def orbit_yojanas() -> float:
    """
    The Moon's orbit (kakshya) in yojanas (SS xii.82, 85-90).

    Bound form of ``ch12_cosmography.orbit_yojanas`` with ``body="Moon"``.
    """
    return _ch12.orbit_yojanas(NAME)


def daily_motion_arcmin() -> float:
    """
    The Moon's apparent daily motion in arcminutes (SS xii.83).

    Bound form of ``ch12_cosmography.daily_motion_arcmin`` with ``body="Moon"``.
    """
    return _ch12.daily_motion_arcmin(NAME)


def orbit_diameter() -> float:
    """
    Diameter of the Moon's orbit in yojanas (SS xii.84).

    Bound form of ``ch12_cosmography.orbit_diameter`` with ``body="Moon"``.
    """
    return _ch12.orbit_diameter(NAME)


def mean_distance() -> float:
    """
    The Moon's distance from the earth's surface in yojanas (SS xii.84).

    Bound form of ``ch12_cosmography.mean_distance`` with ``body="Moon"``.
    """
    return _ch12.mean_distance(NAME)
