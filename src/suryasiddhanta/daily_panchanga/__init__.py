"""
daily_panchanga — Surya Siddhanta Daily Panchanga
==================================================
Hindu almanac (panchanga) for any date, with display metadata
(deities, rashi symbols), served by the API's /calc/daily-panchanga routes.
"""

from .core import get_panchanga, get_panchanga_range

__all__ = ["get_panchanga", "get_panchanga_range"]
