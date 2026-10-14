"""
The Sun, gathered from every chapter that computes it.

A planet-wise view of the chapter modules: each function here is either a
chapter function with ``planet="Sun"`` already bound, under the same name
and with the remaining parameters unchanged, or a Sun chapter function
re-exported as it is. The chapter modules stay the one implementation;
nothing is computed here.

Functions that need the Sun and the Moon together sit where a reader
would look for them: the solar eclipse and parallax are here, the lunar
eclipse and the phases are in ``moon``, and the tithi/yoga/karana,
panchanga, patas and eclipse projection are in both.

The Sun has no sighra correction and no latitude, and its rising and
setting are in ch03 rather than ch09, so those bound forms are absent.

Chapters drawn on: 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14.

Example::

    from suryasiddhanta.planets import sun
    sun.compute(2024, 4, 9).true_longitude
    sun.sankrantis(2024)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from suryasiddhanta import ch01_mean_motions as _ch01
from suryasiddhanta import ch02_true_places as _ch02
from suryasiddhanta import ch07_conjunctions as _ch07
from suryasiddhanta import ch12_cosmography as _ch12
from suryasiddhanta.ch01_mean_motions import (
    masa_from_sun_longitude,
    ritu_from_sun_longitude,
    tithi_from_elongation,
    yoga_from_longitudes,
    karana_from_elongation,
    compute_panchanga,
)
from suryasiddhanta.ch03_direction_place_time import (
    gnomon_shadow,
    solar_altitude_from_shadow,
    sunrise_hour_angle,
    sunrise_sunset_offset,
    day_length_ghatis,
    night_length_ghatis,
    dik_from_gnomon,
    latitude_from_noon_shadow,
)
from suryasiddhanta.ch04_lunar_eclipses import (
    apparent_diameter_sun,
    SUN_DIAMETER_YOJANA,
    SUN_DAILY_MOTION_DEG,
)
from suryasiddhanta.ch05_solar_eclipses import (
    SUN_HP_ARCMIN,
    lambana_correction,
    nati_correction,
    find_new_moon,
    compute_solar_eclipse,
    compute_solar_eclipse_topocentric,
)
from suryasiddhanta.ch06_eclipse_projection import (
    eclipse_contact_points,
    project_eclipse_path,
    eclipse_diagram_data,
    plot_eclipse,
)
from suryasiddhanta.ch11_pata import (
    sun_declination,
    longitude_sum,
    find_patas,
    find_next_pata,
    active_pata,
    VYATIPATA_SUM,
    VAIDHRITA_SUM,
    PATA_KINDS,
)
from suryasiddhanta.ch12_cosmography import (
    polar_day_limit,
    invisibility_limits,
    solar_overhead_band,
    solar_year_start,
    solar_month_start,
    sun_crossing_jd,
)
from suryasiddhanta.ch13_instruments import (
    solar_diurnal_hoops,
    clepsydra_day,
    time_from_altitude,
    nara_yantra_time,
    cakra_time,
    dhanus_time,
    yashti_chord,
    yashti_time,
    instrument_time,
    SOLAR_HOOP_LONGITUDES,
    INSTRUMENT_METHODS,
)
from suryasiddhanta.ch14_reckoning_time import (
    punyakala_nadis,
    sankrantis,
    ayanas,
    visuvats,
    shadasitimukhas,
    solar_year,
    SHADASITIMUKHA_ARC,
    SHADASITIMUKHA_LONGITUDES,
    VIRGO_REMAINDER,
)

if TYPE_CHECKING:
    from suryasiddhanta._types import PlanetPosition
    from suryasiddhanta.ch07_conjunctions import Conjunction

# Name of the body.
NAME = "Sun"

# Revolutions in a mahayuga (SS i.29-34).
REVOLUTIONS_PER_MAHAYUGA = _ch01.BHAGANA[NAME]
# Mean daily motion, degrees per civil day.
MEAN_DAILY_MOTION = _ch01.MEAN_DAILY_MOTION[NAME]
# Revolutions of the mandocca in a kalpa (SS i.41-42).
MANDOCCA_REVOLUTIONS_KALPA = _ch01.MANDOCCA_REVOLUTIONS_KALPA[NAME]
# Mandocca longitude at the Kali epoch, degrees.
MANDOCCA_AT_EPOCH = _ch01.MANDOCCA_AT_EPOCH[NAME]
# Manda epicycle at the even and odd quadrants, degrees (SS ii.34-37).
MANDA_EPICYCLE = _ch02.MANDA_EPICYCLE[NAME]

__all__ = [
    "NAME",
    "REVOLUTIONS_PER_MAHAYUGA",
    "MEAN_DAILY_MOTION",
    "MANDOCCA_REVOLUTIONS_KALPA",
    "MANDOCCA_AT_EPOCH",
    "MANDA_EPICYCLE",
    "mean_longitude",
    "mandocca_longitude",
    "corrected_manda_epicycle",
    "manda_correction",
    "manda_longitude",
    "true_longitude_full",
    "compute",
    "find_conjunction",
    "planet_planet_conjunction",
    "nearest_conjunction",
    "planet_star_conjunction",
    "orbit_yojanas",
    "daily_motion_arcmin",
    "orbit_diameter",
    "mean_distance",
    "masa_from_sun_longitude",
    "ritu_from_sun_longitude",
    "tithi_from_elongation",
    "yoga_from_longitudes",
    "karana_from_elongation",
    "compute_panchanga",
    "gnomon_shadow",
    "solar_altitude_from_shadow",
    "sunrise_hour_angle",
    "sunrise_sunset_offset",
    "day_length_ghatis",
    "night_length_ghatis",
    "dik_from_gnomon",
    "latitude_from_noon_shadow",
    "apparent_diameter_sun",
    "SUN_DIAMETER_YOJANA",
    "SUN_DAILY_MOTION_DEG",
    "SUN_HP_ARCMIN",
    "lambana_correction",
    "nati_correction",
    "find_new_moon",
    "compute_solar_eclipse",
    "compute_solar_eclipse_topocentric",
    "eclipse_contact_points",
    "project_eclipse_path",
    "eclipse_diagram_data",
    "plot_eclipse",
    "sun_declination",
    "longitude_sum",
    "find_patas",
    "find_next_pata",
    "active_pata",
    "VYATIPATA_SUM",
    "VAIDHRITA_SUM",
    "PATA_KINDS",
    "polar_day_limit",
    "invisibility_limits",
    "solar_overhead_band",
    "solar_year_start",
    "solar_month_start",
    "sun_crossing_jd",
    "solar_diurnal_hoops",
    "clepsydra_day",
    "time_from_altitude",
    "nara_yantra_time",
    "cakra_time",
    "dhanus_time",
    "yashti_chord",
    "yashti_time",
    "instrument_time",
    "SOLAR_HOOP_LONGITUDES",
    "INSTRUMENT_METHODS",
    "punyakala_nadis",
    "sankrantis",
    "ayanas",
    "visuvats",
    "shadasitimukhas",
    "solar_year",
    "SHADASITIMUKHA_ARC",
    "SHADASITIMUKHA_LONGITUDES",
    "VIRGO_REMAINDER",
]


def mean_longitude(jd: float) -> float:
    """
    Mean sidereal longitude of the Sun at a Julian Day, in degrees [0, 360).

    Bound form of ``ch01_mean_motions.mean_longitude`` with ``planet="Sun"``.
    """
    return _ch01.mean_longitude(NAME, jd)


def mandocca_longitude(jd: float) -> float:
    """
    Longitude of the Sun's mandocca (apex of the slow epicycle), in degrees.

    Bound form of ``ch01_mean_motions.mandocca_longitude`` with ``planet="Sun"``.
    """
    return _ch01.mandocca_longitude(NAME, jd)


def corrected_manda_epicycle(kendra_deg: float) -> float:
    """
    Size of the Sun's pulsating manda epicycle at a kendra, in degrees.

    Bound form of ``ch02_true_places.corrected_manda_epicycle`` with ``planet="Sun"``.
    """
    return _ch02.corrected_manda_epicycle(NAME, kendra_deg)


def manda_correction(mean_lon_deg: float, mandocca_deg: float) -> float:
    """
    Manda correction (equation of centre) for the Sun, in degrees.

    Bound form of ``ch02_true_places.manda_correction`` with ``planet="Sun"``.
    """
    return _ch02.manda_correction(NAME, mean_lon_deg, mandocca_deg)


def manda_longitude(mean_lon_deg: float, mandocca_deg: float) -> float:
    """
    The Sun's manda-sphuta longitude after the manda correction, in degrees [0, 360).

    Bound form of ``ch02_true_places.manda_longitude`` with ``planet="Sun"``.
    """
    return _ch02.manda_longitude(NAME, mean_lon_deg, mandocca_deg)


def true_longitude_full(jd: float) -> dict:
    """
    Every step of the Sun's true-longitude computation for a Julian Day, as a dict.

    Bound form of ``ch02_true_places.true_longitude_full`` with ``planet="Sun"``.
    """
    return _ch02.true_longitude_full(NAME, jd)


def compute(year: int, month: int = 1, day: float = 1.0, gregorian: bool = None) -> PlanetPosition:
    """
    Complete position of the Sun for a calendar date.

    Bound form of ``ch02_true_places.compute`` with ``planet="Sun"``.
    """
    return _ch02.compute(NAME, year, month, day, gregorian)


def find_conjunction(other: str, start_jd: float, end_jd: float, step: float = 1.0) -> List[Conjunction]:
    """
    Every conjunction of the Sun with another body between two Julian Days.

    Bound form of ``ch07_conjunctions.find_conjunction`` with ``planet1="Sun"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.find_conjunction(NAME, other, start_jd, end_jd, step)


def planet_planet_conjunction(other: str, year: int, month: int = 1, months: int = 12) -> List[Conjunction]:
    """
    Every conjunction of the Sun with another body over a span of months.

    Bound form of ``ch07_conjunctions.planet_planet_conjunction`` with ``planet1="Sun"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.planet_planet_conjunction(NAME, other, year, month, months)


def nearest_conjunction(other: str, jd: float, search_days: float = 400.0) -> Optional[Conjunction]:
    """
    The conjunction of the Sun with another body nearest a Julian Day, or None.

    Bound form of ``ch07_conjunctions.nearest_conjunction`` with ``planet1="Sun"``.
    ``other`` is the second body, a name as the chapter modules spell it.
    """
    return _ch07.nearest_conjunction(NAME, other, jd, search_days)


def planet_star_conjunction(star_name: str, year: int, months: int = 12) -> List[Conjunction]:
    """
    Conjunctions of the Sun with a yogatara (junction star) over a span of months.

    Bound form of ``ch07_conjunctions.planet_star_conjunction`` with ``planet="Sun"``.
    """
    return _ch07.planet_star_conjunction(NAME, star_name, year, months)


def orbit_yojanas() -> float:
    """
    The Sun's orbit (kakshya) in yojanas (SS xii.82, 85-90).

    Bound form of ``ch12_cosmography.orbit_yojanas`` with ``body="Sun"``.
    """
    return _ch12.orbit_yojanas(NAME)


def daily_motion_arcmin() -> float:
    """
    The Sun's apparent daily motion in arcminutes (SS xii.83).

    Bound form of ``ch12_cosmography.daily_motion_arcmin`` with ``body="Sun"``.
    """
    return _ch12.daily_motion_arcmin(NAME)


def orbit_diameter() -> float:
    """
    Diameter of the Sun's orbit in yojanas (SS xii.84).

    Bound form of ``ch12_cosmography.orbit_diameter`` with ``body="Sun"``.
    """
    return _ch12.orbit_diameter(NAME)


def mean_distance() -> float:
    """
    The Sun's distance from the earth's surface in yojanas (SS xii.84).

    Bound form of ``ch12_cosmography.mean_distance`` with ``body="Sun"``.
    """
    return _ch12.mean_distance(NAME)
