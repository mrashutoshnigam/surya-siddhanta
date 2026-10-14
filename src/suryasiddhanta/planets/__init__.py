"""
Planet-wise view of the Surya Siddhanta library.

The chapter modules (``ch01_mean_motions`` ... ``ch14_reckoning_time``)
follow the book. This package regroups the same functions by graha, so
that everything about one body is a single import away::

    from suryasiddhanta.planets import sun, mars

    sun.compute(2024, 4, 9).true_longitude   # planet="Sun" already bound
    sun.sankrantis(2024)                     # Sun-only function, re-exported
    mars.next_heliacal(2460410.5)            # planet="Mars" already bound

Each planet module holds three kinds of name:

  - **bound wrappers**: a chapter function that takes a planet, under the
    same name, with the planet filled in and the other parameters
    unchanged (``ch07``'s second body is called ``other``);
  - **re-exports**: a chapter function or constant that concerns only
    that body (or, for the Sun and the Moon, both of them), the chapter's
    own object under its own name;
  - **constants**: that body's entries in the chapter tables, under
    uniform names (``REVOLUTIONS_PER_MAHAYUGA``, ``MANDA_EPICYCLE``, ...).

Nothing is computed here: the chapter modules stay the one
implementation, apart from Ketu, which no chapter computes (see ``ketu``).
"""

from __future__ import annotations

from types import ModuleType
from typing import Dict

from suryasiddhanta.planets import (
    jupiter, ketu, mars, mercury, moon, rahu, saturn, sun, venus,
)

# The nine grahas in the traditional order, name -> module.
GRAHAS: Dict[str, ModuleType] = {
    m.NAME: m
    for m in (sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu)
}

__all__ = [
    "GRAHAS",
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
    "rahu", "ketu",
]
