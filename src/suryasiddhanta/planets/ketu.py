"""
Ketu, the Moon's descending node.

No chapter function computes Ketu: the Surya Siddhanta reckons the
Moon's node as one point (Rahu, ``ch01_mean_motions.moon_node_longitude``).
Ketu here is the conventional opposite point, Rahu + 180 degrees, a
derived convention rather than a rule of the text. Its revolutions and
daily motion are Rahu's.

Example::

    from suryasiddhanta.planets import ketu
    ketu.mean_longitude(2460410.5)
"""

from __future__ import annotations

from suryasiddhanta import ch01_mean_motions as _ch01
from suryasiddhanta.ch02_true_places import normalize as _normalize

# Name of the body.
NAME = "Ketu"
# Key for the node in the chapter tables.
CHAPTER_KEY = "Moon_node"

# Revolutions in a mahayuga, retrograde; the same as Rahu's.
REVOLUTIONS_PER_MAHAYUGA = _ch01.BHAGANA[CHAPTER_KEY]
# Mean daily motion, degrees per civil day; negative, the same as Rahu's.
MEAN_DAILY_MOTION = _ch01.MEAN_DAILY_MOTION[CHAPTER_KEY]

__all__ = [
    "NAME",
    "CHAPTER_KEY",
    "REVOLUTIONS_PER_MAHAYUGA",
    "MEAN_DAILY_MOTION",
    "mean_longitude",
]


def mean_longitude(jd: float) -> float:
    """
    Mean sidereal longitude of Ketu (the Moon's descending node) at a
    Julian Day, in degrees [0, 360): Rahu + 180 degrees.

    Derived convention: no chapter function computes Ketu.
    """
    return _normalize(_ch01.moon_node_longitude(jd) + 180.0)
