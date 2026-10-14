"""
Mars, gathered from every chapter that computes it.

A planet-wise view of the chapter modules: each function here is either a
chapter function with ``planet="Mars"`` already bound, under the same
name and with the remaining parameters unchanged, or a Mars-only
chapter function re-exported as it is. The chapter modules stay the one
implementation; nothing is computed here.

Chapters drawn on: 1 (mean, mandocca, sighrocca, node), 2 (true
place and latitude), 7 (conjunctions), 9 (heliacal risings and settings),
12 (orbit).

Example::

    from suryasiddhanta.planets import mars
    mars.compute(2024, 4, 9).true_longitude
    mars.next_heliacal(2460410.5, "rising")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from suryasiddhanta import ch01_mean_motions as _ch01
from suryasiddhanta import ch02_true_places as _ch02
from suryasiddhanta import ch07_conjunctions as _ch07
from suryasiddhanta import ch09_heliacal as _ch09
from suryasiddhanta import ch12_cosmography as _ch12

if TYPE_CHECKING:
    from suryasiddhanta._types import PlanetPosition
    from suryasiddhanta.ch07_conjunctions import Conjunction
    from suryasiddhanta.ch09_heliacal import HeliacalEvent

# Name of the body.
NAME = "Mars"

# Revolutions in a mahayuga (SS i.29-34).
REVOLUTIONS_PER_MAHAYUGA = _ch01.BHAGANA[NAME]
# Mean daily motion, degrees per civil day.
MEAN_DAILY_MOTION = _ch01.MEAN_DAILY_MOTION[NAME]
# Revolutions of the mandocca in a kalpa (SS i.41-42).
MANDOCCA_REVOLUTIONS_KALPA = _ch01.MANDOCCA_REVOLUTIONS_KALPA[NAME]
# Mandocca longitude at the Kali epoch, degrees.
MANDOCCA_AT_EPOCH = _ch01.MANDOCCA_AT_EPOCH[NAME]
# Revolutions of the node in a kalpa, retrograde (SS i.43-44).
NODE_REVOLUTIONS_KALPA = _ch01.NODE_REVOLUTIONS_KALPA[NAME]
# Node longitude at the Kali epoch, degrees.
NODE_AT_EPOCH = _ch01.NODE_AT_EPOCH[NAME]
# Manda epicycle at the even and odd quadrants, degrees (SS ii.34-37).
MANDA_EPICYCLE = _ch02.MANDA_EPICYCLE[NAME]
# Sighra epicycle at the even and odd quadrants, degrees (SS ii.34-37).
SIGHRA_EPICYCLE = _ch02.SIGHRA_EPICYCLE[NAME]
# Greatest latitude, arcminutes (SS i.68-70).
MADHYAMA_VIKSHEPA_ARCMIN = _ch02.MADHYAMA_VIKSHEPA_ARCMIN[NAME]
# Degrees of time for heliacal visibility (SS ix.6-9).
VISIBILITY_THRESHOLDS = _ch09.VISIBILITY_THRESHOLDS[NAME]

__all__ = [
    "NAME",
    "REVOLUTIONS_PER_MAHAYUGA",
    "MEAN_DAILY_MOTION",
    "MANDOCCA_REVOLUTIONS_KALPA",
    "MANDOCCA_AT_EPOCH",
    "NODE_REVOLUTIONS_KALPA",
    "NODE_AT_EPOCH",
    "MANDA_EPICYCLE",
    "SIGHRA_EPICYCLE",
    "MADHYAMA_VIKSHEPA_ARCMIN",
    "VISIBILITY_THRESHOLDS",
    "mean_longitude",
    "mandocca_longitude",
    "sighrocca_longitude",
    "planet_node_longitude",
    "corrected_manda_epicycle",
    "manda_correction",
    "manda_longitude",
    "corrected_sighra_epicycle",
    "sighra_correction",
    "sighra_karna",
    "true_longitude_full",
    "planet_latitude",
    "compute",
    "find_conjunction",
    "planet_planet_conjunction",
    "nearest_conjunction",
    "planet_star_conjunction",
    "sun_elongation",
    "is_planet_visible",
    "heliacal_rising",
    "heliacal_setting",
    "visibility_events",
    "next_heliacal",
    "orbit_yojanas",
    "daily_motion_arcmin",
    "orbit_diameter",
    "mean_distance",
]


def mean_longitude(jd: float) -> float:
    """
    Mean sidereal longitude of Mars at a Julian Day, in degrees [0, 360).

    Bound form of ``ch01_mean_motions.mean_longitude`` with ``planet="Mars"``.
    """
    return _ch01.mean_longitude(NAME, jd)


def mandocca_longitude(jd: float) -> float:
    """
    Longitude of Mars's mandocca (apex of the slow epicycle), in degrees.

    Bound form of ``ch01_mean_motions.mandocca_longitude`` with ``planet="Mars"``.
    """
    return _ch01.mandocca_longitude(NAME, jd)


def sighrocca_longitude(jd: float) -> float:
    """
    Longitude of Mars's sighrocca (apex of the fast epicycle), in degrees.

    Bound form of ``ch01_mean_motions.sighrocca_longitude`` with ``planet="Mars"``.
    """
    return _ch01.sighrocca_longitude(NAME, jd)


def planet_node_longitude(jd: float) -> float:
    """
    Longitude of Mars's ascending node, in degrees (SS i.43-44).

    Bound form of ``ch01_mean_motions.planet_node_longitude`` with ``planet="Mars"``.
    """
    return _ch01.planet_node_longitude(NAME, jd)


def corrected_manda_epicycle(kendra_deg: float) -> float:
    """
    Size of Mars's pulsating manda epicycle at a kendra, in degrees.

    Bound form of ``ch02_true_places.corrected_manda_epicycle`` with ``planet="Mars"``.
    """
    return _ch02.corrected_manda_epicycle(NAME, kendra_deg)


def manda_correction(mean_lon_deg: float, mandocca_deg: float) -> float:
    """
    Manda correction (equation of centre) for Mars, in degrees.

    Bound form of ``ch02_true_places.manda_correction`` with ``planet="Mars"``.
    """
    return _ch02.manda_correction(NAME, mean_lon_deg, mandocca_deg)


def manda_longitude(mean_lon_deg: float, mandocca_deg: float) -> float:
    """
    Mars's manda-sphuta longitude after the manda correction, in degrees [0, 360).

    Bound form of ``ch02_true_places.manda_longitude`` with ``planet="Mars"``.
    """
    return _ch02.manda_longitude(NAME, mean_lon_deg, mandocca_deg)


def corrected_sighra_epicycle(kendra_deg: float) -> float:
    """
    Size of Mars's pulsating sighra epicycle at a kendra, in degrees.

    Bound form of ``ch02_true_places.corrected_sighra_epicycle`` with ``planet="Mars"``.
    """
    return _ch02.corrected_sighra_epicycle(NAME, kendra_deg)


def sighra_correction(manda_sphuta_deg: float, sighrocca_deg: float) -> float:
    """
    Sighra correction for Mars, in degrees.

    Bound form of ``ch02_true_places.sighra_correction`` with ``planet="Mars"``.
    """
    return _ch02.sighra_correction(NAME, manda_sphuta_deg, sighrocca_deg)


def sighra_karna(manda_sphuta_deg: float, sighrocca_deg: float) -> float:
    """
    Mars's sighra hypotenuse (karna) in SS units, deferent radius R_SINE.

    Bound form of ``ch02_true_places.sighra_karna`` with ``planet="Mars"``.
    """
    return _ch02.sighra_karna(NAME, manda_sphuta_deg, sighrocca_deg)


def true_longitude_full(jd: float) -> dict:
    """
    Every step of Mars's true-longitude computation for a Julian Day, as a dict.

    Bound form of ``ch02_true_places.true_longitude_full`` with ``planet="Mars"``.
    """
    return _ch02.true_longitude_full(NAME, jd)


def planet_latitude(jd: float) -> float:
    """
    Mars's celestial latitude (shara) in arcminutes, north positive.

    Bound form of ``ch02_true_places.planet_latitude`` with ``planet="Mars"``.
    """
    return _ch02.planet_latitude(NAME, jd)


def compute(year: int, month: int = 1, day: float = 1.0, gregorian: bool = None) -> PlanetPosition:
    """
    Complete position of Mars for a calendar date.

    Bound form of ``ch02_true_places.compute`` with ``planet="Mars"``.
    """
    return _ch02.compute(NAME, year, month, day, gregorian)


def find_conjunction(other: str, start_jd: float, end_jd: float, step: float = 1.0) -> List[Conjunction]:
    """
    Every conjunction of Mars with another body between two Julian Days.

    Bound form of ``ch07_conjunctions.find_conjunction`` with ``planet1="Mars"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.find_conjunction(NAME, other, start_jd, end_jd, step)


def planet_planet_conjunction(other: str, year: int, month: int = 1, months: int = 12) -> List[Conjunction]:
    """
    Every conjunction of Mars with another body over a span of months.

    Bound form of ``ch07_conjunctions.planet_planet_conjunction`` with ``planet1="Mars"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.planet_planet_conjunction(NAME, other, year, month, months)


def nearest_conjunction(other: str, jd: float, search_days: float = 400.0) -> Optional[Conjunction]:
    """
    The conjunction of Mars with another body nearest a Julian Day, or None.

    Bound form of ``ch07_conjunctions.nearest_conjunction`` with ``planet1="Mars"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.nearest_conjunction(NAME, other, jd, search_days)


def planet_star_conjunction(star_name: str, year: int, months: int = 12) -> List[Conjunction]:
    """
    Conjunctions of Mars with a yogatara (junction star) over a span of months.

    Bound form of ``ch07_conjunctions.planet_star_conjunction`` with ``planet="Mars"``.
    """
    return _ch07.planet_star_conjunction(NAME, star_name, year, months)


def sun_elongation(jd: float) -> float:
    """
    Mars's signed elongation from the Sun at a Julian Day, in degrees.

    Bound form of ``ch09_heliacal.sun_elongation`` with ``planet="Mars"``.
    """
    return _ch09.sun_elongation(NAME, jd)


def is_planet_visible(jd: float, lat_deg: float = 0.0, lon_deg: float = 0.0) -> bool:
    """
    Whether Mars is clear of the Sun's rays at a Julian Day.

    Bound form of ``ch09_heliacal.is_planet_visible`` with ``planet="Mars"``.
    """
    return _ch09.is_planet_visible(NAME, jd, lat_deg, lon_deg)


def heliacal_rising(year: int, lat_deg: float = 0.0, start_month: int = 1) -> Optional[HeliacalEvent]:
    """
    Mars's first heliacal rising from a given month of a year, or None.

    Bound form of ``ch09_heliacal.heliacal_rising`` with ``planet="Mars"``.
    """
    return _ch09.heliacal_rising(NAME, year, lat_deg, start_month)


def heliacal_setting(year: int, lat_deg: float = 0.0, start_month: int = 1) -> Optional[HeliacalEvent]:
    """
    Mars's first heliacal setting from a given month of a year, or None.

    Bound form of ``ch09_heliacal.heliacal_setting`` with ``planet="Mars"``.
    """
    return _ch09.heliacal_setting(NAME, year, lat_deg, start_month)


def visibility_events(year: int, months: int = 12) -> List[HeliacalEvent]:
    """
    Every heliacal rising and setting of Mars over a span of months.

    Bound form of ``ch09_heliacal.visibility_events`` with ``planet="Mars"``.
    """
    return _ch09.visibility_events(NAME, year, months)


def next_heliacal(jd: float, event_type: str = 'rising') -> Optional[HeliacalEvent]:
    """
    Mars's next heliacal event of the given type after a Julian Day, or None.

    Bound form of ``ch09_heliacal.next_heliacal`` with ``planet="Mars"``.
    """
    return _ch09.next_heliacal(NAME, jd, event_type)


def orbit_yojanas() -> float:
    """
    Mars's orbit (kakshya) in yojanas (SS xii.82, 85-90).

    Bound form of ``ch12_cosmography.orbit_yojanas`` with ``body="Mars"``.
    """
    return _ch12.orbit_yojanas(NAME)


def daily_motion_arcmin() -> float:
    """
    Mars's apparent daily motion in arcminutes (SS xii.83).

    Bound form of ``ch12_cosmography.daily_motion_arcmin`` with ``body="Mars"``.
    """
    return _ch12.daily_motion_arcmin(NAME)


def orbit_diameter() -> float:
    """
    Diameter of Mars's orbit in yojanas (SS xii.84).

    Bound form of ``ch12_cosmography.orbit_diameter`` with ``body="Mars"``.
    """
    return _ch12.orbit_diameter(NAME)


def mean_distance() -> float:
    """
    Mars's distance from the earth's surface in yojanas (SS xii.84).

    Bound form of ``ch12_cosmography.mean_distance`` with ``body="Mars"``.
    """
    return _ch12.mean_distance(NAME)
