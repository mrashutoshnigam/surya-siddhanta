"""
daily_panchanga/core.py
=======================
Core panchanga computation logic for the daily panchanga app.
Wraps ch01 compute_panchanga with additional formatting and metadata.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Any

from suryasiddhanta.ch01_mean_motions import (
    compute_panchanga, julian_day,
    TITHI_NAMES, VARA_NAMES, VARA_NAMES_EN,
    MASA_NAMES, RITU_NAMES, RITU_NAMES_EN,
    SAMVATSARA_NAMES, YOGA_NAMES,
    KARANA_NAMES_RECURRING, KARANA_NAMES_FIXED,
    _NAKSHATRA_NAMES,
)
from suryasiddhanta.ch02_true_places import compute
from suryasiddhanta.ch10_lunar_horns import (
    illuminated_fraction, phase_name, is_waxing, moon_elongation,
)


NAKSHATRA_DEITIES = [
    "Ashvini Kumaras", "Yama", "Agni", "Brahma", "Soma",
    "Rudra", "Aditi", "Brihaspati", "Sarpa", "Pitrs",
    "Bhaga", "Aryaman", "Savitar", "Tvashtar", "Vayu",
    "Indragni", "Mitra", "Indra", "Nirriti", "Apah",
    "Vishvedeva", "Vishnu", "Vasu", "Varuna", "Ajaikapada",
    "Ahirbudhnya", "Pushan",
]

TITHI_DEITIES = [
    "Agni", "Brahma", "Gauri", "Ganesh", "Sarpa",
    "Kartikeya", "Surya", "Shiva", "Durga", "Dharmaraja",
    "Vishnu", "Hari", "Kamadeva", "Shiva", "Soma",
    "Agni", "Brahma", "Gauri", "Ganesh", "Sarpa",
    "Kartikeya", "Surya", "Shiva", "Durga", "Dharmaraja",
    "Vishnu", "Hari", "Kamadeva", "Shiva", "Pitrs",
]


RASHI_SYMBOLS = [
    "♈", "♉", "♊", "♋", "♌", "♍",
    "♎", "♏", "♐", "♑", "♒", "♓",
]

RASHI_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]


def get_panchanga(year: int, month: int, day: int) -> Dict[str, Any]:
    """Compute full panchanga with extra metadata for display."""
    p = compute_panchanga(year, month, day)
    d = p.to_dict()
    jd = p.jd

    illum = illuminated_fraction(jd)
    phase = phase_name(jd)
    waxing = is_waxing(jd)
    elong = moon_elongation(jd)

    sun_rashi_idx = int(p.sun_lon / 30.0) % 12
    moon_rashi_idx = int(p.moon_lon / 30.0) % 12

    d["moon_phase"] = {
        "name": phase,
        "illumination_pct": round(illum * 100, 1),
        "is_waxing": waxing,
        "elongation": round(elong, 1),
    }
    d["sun_rashi"] = {
        "index": sun_rashi_idx,
        "name": RASHI_NAMES[sun_rashi_idx],
        "symbol": RASHI_SYMBOLS[sun_rashi_idx],
    }
    d["moon_rashi"] = {
        "index": moon_rashi_idx,
        "name": RASHI_NAMES[moon_rashi_idx],
        "symbol": RASHI_SYMBOLS[moon_rashi_idx],
    }

    nak_idx = d["nakshatra"]["number"] - 1
    if 0 <= nak_idx < len(NAKSHATRA_DEITIES):
        d["nakshatra"]["deity"] = NAKSHATRA_DEITIES[nak_idx]

    tithi_idx = d["tithi"]["number"] - 1
    if 0 <= tithi_idx < len(TITHI_DEITIES):
        d["tithi"]["deity"] = TITHI_DEITIES[tithi_idx]

    return d


def get_panchanga_range(start: date, days: int = 7) -> List[Dict[str, Any]]:
    """Compute panchanga for a range of dates."""
    results = []
    for i in range(days):
        dt = start + timedelta(days=i)
        results.append(get_panchanga(dt.year, dt.month, dt.day))
    return results
