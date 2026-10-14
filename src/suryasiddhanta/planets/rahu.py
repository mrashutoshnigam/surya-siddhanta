"""
Rahu, the Moon's ascending node, gathered from the chapters that use it.

The chapter modules have no body called Rahu: the node is
``ch01_mean_motions.moon_node_longitude`` and the key ``"Moon_node"`` in
the revolution and orbit tables. This module names it. The node moves
retrograde, so ``MEAN_DAILY_MOTION`` is negative.

Chapters drawn on: 1 (node longitude), 4 (Moon's latitude from the node,
eclipse limit), 12 (orbit).

Example::

    from suryasiddhanta.planets import rahu
    rahu.mean_longitude(2460410.5)
"""

from __future__ import annotations

from suryasiddhanta import ch01_mean_motions as _ch01
from suryasiddhanta import ch12_cosmography as _ch12
from suryasiddhanta.ch01_mean_motions import (
    moon_node_longitude,
)
from suryasiddhanta.ch04_lunar_eclipses import (
    moon_latitude,
    is_near_node,
)

# Name of the body.
NAME = "Rahu"
# Key for the node in the chapter tables.
CHAPTER_KEY = "Moon_node"

# Revolutions in a mahayuga, retrograde (SS i.29-34).
REVOLUTIONS_PER_MAHAYUGA = _ch01.BHAGANA[CHAPTER_KEY]
# Mean daily motion, degrees per civil day; negative (retrograde).
MEAN_DAILY_MOTION = _ch01.MEAN_DAILY_MOTION[CHAPTER_KEY]

__all__ = [
    "NAME",
    "CHAPTER_KEY",
    "REVOLUTIONS_PER_MAHAYUGA",
    "MEAN_DAILY_MOTION",
    "orbit_yojanas",
    "daily_motion_arcmin",
    "orbit_diameter",
    "mean_distance",
    "moon_node_longitude",
    "moon_latitude",
    "is_near_node",
    "mean_longitude",
]


def mean_longitude(jd: float) -> float:
    """
    Mean sidereal longitude of Rahu (the Moon's ascending node) at a Julian
    Day, in degrees [0, 360). Moves retrograde.

    Same as ``ch01_mean_motions.moon_node_longitude``.
    """
    return _ch01.moon_node_longitude(jd)


def orbit_yojanas() -> float:
    """
    Rahu's orbit (kakshya) in yojanas (SS xii.82, 85-90).

    Bound form of ``ch12_cosmography.orbit_yojanas`` with ``body="Moon_node"``.
    """
    return _ch12.orbit_yojanas(CHAPTER_KEY)


def daily_motion_arcmin() -> float:
    """
    Rahu's apparent daily motion in arcminutes (SS xii.83).

    Bound form of ``ch12_cosmography.daily_motion_arcmin`` with ``body="Moon_node"``.
    """
    return _ch12.daily_motion_arcmin(CHAPTER_KEY)


def orbit_diameter() -> float:
    """
    Diameter of Rahu's orbit in yojanas (SS xii.84).

    Bound form of ``ch12_cosmography.orbit_diameter`` with ``body="Moon_node"``.
    """
    return _ch12.orbit_diameter(CHAPTER_KEY)


def mean_distance() -> float:
    """
    Rahu's distance from the earth's surface in yojanas (SS xii.84).

    Bound form of ``ch12_cosmography.mean_distance`` with ``body="Moon_node"``.
    """
    return _ch12.mean_distance(CHAPTER_KEY)
