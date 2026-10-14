"""Verse-indexed payloads for the React "Book" page of Chapter 2.

Chapter 2 counterpart of ``book.py``: for one date (and a latitude), what does
each computational verse of *Of the True Places of the Planets* yield? The
React page renders one card per entry of ``CARD_ORDER`` in Burgess's own
verse order.

No astronomy lives here. Builders call ``ch01``/``ch02``/``ch03`` and shape
the result; where a card decomposes a verse's own formula (the sighra
hypotenuse, the day-radius) the pieces are the verse's, and tests pin the
result to the library's figures.

Verse numbers follow Burgess as read from the corpus, not the module
docstring of ``ch02_true_places.py``.

Reference: SS Ch.2 v.15-69; Burgess (1860) pp.50-90
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch02_true_places as ch02
from suryasiddhanta import ch03_direction_place_time as ch03

from .schemas import Ch02In, Ch02ProbeIn

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_2_TITLE = "Of the True Places of the Planets"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = [
    "ii.15-27",
    "ii.29-30",
    "ii.31-33",
    "ii.34-38",
    "ii.39",
    "ii.40-42",
    "ii.43-45",
    "ii.60-63",
    "ii.65",
    "ii.66",
    "ii.67-69",
]

#: Bodies with a sighra (conjunction) correction, in the text's order.
_STAR_PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

_ARCMIN_PER_SIGN = 1800


@dataclass
class _Ctx:
    """What a card builder may depend on: the date and the observer's latitude.

    ``positions`` is computed lazily, once per request, so static cards never
    pay for the seven true-longitude pipelines.
    """

    jd: float
    latitude: float

    @cached_property
    def positions(self) -> Dict[str, Dict[str, Any]]:
        """``ch02.true_longitude_full`` for every body on this date."""
        return {b: ch02.true_longitude_full(b, self.jd) for b in ch01.ALL_PLANETS}


def _rashi(longitude: float) -> str:
    """Format a longitude as its sign and the degrees elapsed within it."""
    _, name, deg_in = ch01.rashi_from_longitude(longitude)
    return f"{name} {deg_in:.2f}°"


def _decompose(kendra: float) -> Dict[str, Any]:
    """Split an anomaly into quadrant, bhuja and koti, and their sines (v.29-30)."""
    k = ch02.normalize(kendra)
    bhuja, koti = ch02.get_bhuja_koti(k)
    return {
        "kendra": k,
        "quadrant": ch02.get_quadrant(k),
        "odd": ch02.is_odd_quadrant(k),
        "bhuja": bhuja,
        "koti": koti,
        "bhuja_jya": ch02.jya(bhuja),
        "koti_jya": ch02.jya(koti),
    }


def _interp_forward(arc_deg: float) -> Dict[str, Any]:
    """Interpolate the sine of an arc as v.31-32 direct, step by step.

    Arcminutes divided by 225 give the preceding tabular sine; the remainder
    times the difference to the next, over 225, is added to it. The result
    is what ``ch02.jya`` returns, and is shown beside it. Valid only for arcs
    0..90 degrees (the schema bounds ``arc_deg`` to that range).
    """
    arcmin = arc_deg * 60.0
    step = ch02.JYA_STEP_ARCMIN
    quotient = min(int(arcmin // step), len(ch02.JYA_TABLE))
    remainder = arcmin - quotient * step if quotient < len(ch02.JYA_TABLE) else 0.0
    preceding = ch02.JYA_TABLE[quotient - 1] if quotient > 0 else 0.0
    following = ch02.JYA_TABLE[quotient] if quotient < len(ch02.JYA_TABLE) else float(ch02.R_SINE)
    difference = following - preceding
    part = remainder * difference / step
    return {
        "arc_deg": arc_deg,
        "arcmin": arcmin,
        "quotient": quotient,
        "remainder_arcmin": remainder,
        "preceding": preceding,
        "following": following,
        "difference": difference,
        "part": part,
        "interpolated": preceding + part,
        "library": ch02.jya(arc_deg),
        "exact": ch02.R_SINE * math.sin(math.radians(arc_deg)),
    }


def _interp_inverse(sine: float) -> Dict[str, Any]:
    """Find the arc of a given sine as v.33: the next-less tabular sine, then
    the remainder times 225 over the tabular difference."""
    step = ch02.JYA_STEP_ARCMIN
    value = min(max(sine, 0.0), float(ch02.R_SINE))
    if value <= 0.0:
        return {"sine": value, "count_below": 0, "less": 0.0, "difference": 0.0,
                "arcmin": 0.0, "arc_deg": 0.0, "library_deg": 0.0}
    if value >= ch02.R_SINE:
        return {"sine": value, "count_below": len(ch02.JYA_TABLE) - 1,
                "less": float(ch02.JYA_TABLE[-2]), "difference": float(ch02.JYA_TABLE[-1] - ch02.JYA_TABLE[-2]),
                "arcmin": 90.0 * 60.0, "arc_deg": 90.0, "library_deg": 90.0}
    below = sum(1 for x in ch02.JYA_TABLE if x < value)
    less = ch02.JYA_TABLE[below - 1] if below > 0 else 0.0
    difference = ch02.JYA_TABLE[below] - less
    arcmin = below * step + (value - less) * step / difference
    return {
        "sine": value,
        "count_below": below,
        "less": less,
        "difference": difference,
        "arcmin": arcmin,
        "arc_deg": arcmin / 60.0,
        "library_deg": ch02.arcjya(value),
    }


def _epicycle_at(body: str, kendra: float) -> Dict[str, Any]:
    """The pulsating epicycle sizes at one anomaly (v.38): even + (odd-even)·sin(bhuja)."""
    k = ch02.normalize(kendra)
    bhuja, _ = ch02.get_bhuja_koti(k)
    sighra = None
    if body in ch02.SIGHRA_EPICYCLE:
        sighra = ch02.corrected_sighra_epicycle(body, k)
    return {
        "body": body,
        "kendra": k,
        "bhuja": bhuja,
        "sin_bhuja": ch02.jya(bhuja) / ch02.R_SINE,
        "manda": ch02.corrected_manda_epicycle(body, k),
        "sighra": sighra,
    }


# ─────────────────────────────  static cards  ─────────────────────────────

def _card_sine_table(_ctx: _Ctx) -> Dict[str, Any]:
    """ii.15-27: the 24 tabular sines and versed sines, with first differences.

    The v.15-16 construction rule is deliberately not computed: its two
    natural readings do not reproduce the tabulated values, so only the
    first sine (a sign's minutes divided by eight) is stated.
    """
    rows, previous = [], 0
    for i, value in enumerate(ch02.JYA_TABLE):
        degrees = (i + 1) * ch02.JYA_STEP_ARCMIN / 60.0
        modern = ch02.R_SINE * math.sin(math.radians(degrees))
        rows.append({
            "index": i + 1,
            "arcmin": (i + 1) * ch02.JYA_STEP_ARCMIN,
            "degrees": degrees,
            "jya": value,
            "difference": value - previous,
            "utkrama": ch02.utkrama_jya(degrees),
            "modern": round(modern, 2),
            "error": round(abs(value - modern), 2),
        })
        previous = value
    return {
        "radius": ch02.R_SINE,
        "step_arcmin": ch02.JYA_STEP_ARCMIN,
        "sign_arcmin": _ARCMIN_PER_SIGN,
        "first_sine": _ARCMIN_PER_SIGN / 8,
        "rows": rows,
        "note": "The v.15-16 rule for building the table is stated in the text but not computed here.",
    }


def _card_interpolation(_ctx: _Ctx) -> Dict[str, Any]:
    """ii.31-33: interpolation of a sine or arc, seeded with one worked case each."""
    return {
        "step_arcmin": ch02.JYA_STEP_ARCMIN,
        "forward": _interp_forward(30.0),
        "inverse": _interp_inverse(1000.0),
    }


def _card_epicycles(_ctx: _Ctx) -> Dict[str, Any]:
    """ii.34-38: epicycle sizes at the even and odd quadrant ends, and at a sample kendra."""
    rows = []
    for body in ch01.ALL_PLANETS:
        manda = ch02.MANDA_EPICYCLE[body]
        sighra = ch02.SIGHRA_EPICYCLE.get(body)
        rows.append({
            "body": body,
            "manda_even": manda.even,
            "manda_odd": manda.odd,
            "sighra_even": None if sighra is None else sighra.even,
            "sighra_odd": None if sighra is None else sighra.odd,
            "sample": _epicycle_at(body, 45.0),
        })
    return {"rows": rows, "sample_kendra": 45.0}


# ─────────────────────────────  date-dependent cards  ─────────────────────────────

def _card_bhuja_koti(ctx: _Ctx) -> Dict[str, Any]:
    """ii.29-30: each body's manda and sighra kendra split into bhuja and koti."""
    rows = []
    for body in ch01.ALL_PLANETS:
        pos = ctx.positions[body]
        sighra_kendra = pos.get("sighra_kendra")
        rows.append({
            "body": body,
            "manda": _decompose(pos["manda_kendra"]),
            "sighra": None if sighra_kendra is None else _decompose(sighra_kendra),
        })
    return {"rows": rows, "sample": _decompose(45.0)}


def _card_manda(ctx: _Ctx) -> Dict[str, Any]:
    """ii.39: the equation of the apsis, one step applied to the mean place."""
    rows = []
    for body in ch01.ALL_PLANETS:
        mean = ch01.mean_longitude(body, ctx.jd)
        apsis = ch01.mandocca_longitude(body, ctx.jd)
        parts = _decompose(mean - apsis)
        size = ch02.corrected_manda_epicycle(body, parts["kendra"])
        phala = ch02.manda_correction(body, mean, apsis)
        rows.append({
            "body": body,
            "mean": mean,
            "mandocca": apsis,
            **parts,
            "epicycle": size,
            "phala": phala,
            "corrected": ch02.manda_longitude(body, mean, apsis),
            "corrected_rashi": _rashi(ch02.manda_longitude(body, mean, apsis)),
        })
    return {"rows": rows}


def _card_sighra(ctx: _Ctx) -> Dict[str, Any]:
    """ii.40-42: the equation of the conjunction, as the true-place pipeline takes it.

    Built from the pipeline's own step 4 (``ch02.true_longitude_full``): the
    place already corrected by the whole manda (``ms2``), the conjunction
    anomaly measured from it, and the whole sighra correction. So the anomaly
    agrees with the ii.29-30 card and the phala with the last stage of
    ii.43-45. The verse's pieces (koti- and bhuja-phala, hypotenuse) are
    decomposed from that anomaly. Sun and Moon have no sighra epicycle and
    are named in ``no_sighra`` rather than given rows.
    """
    rows = []
    for body in _STAR_PLANETS:
        pos = ctx.positions[body]
        parts = _decompose(pos["sighra_kendra"])
        size = ch02.corrected_sighra_epicycle(body, parts["kendra"])
        r = size / 360.0
        sin_bhuja = parts["bhuja_jya"] / ch02.R_SINE
        cos_bhuja = math.sqrt(max(0.0, 1.0 - sin_bhuja ** 2))
        cos_k = -cos_bhuja if 90.0 < parts["kendra"] < 270.0 else cos_bhuja
        rows.append({
            "body": body,
            "manda_sphuta": pos["ms2"],
            "sighrocca": pos["sighrocca"],
            **parts,
            "epicycle": size,
            "kotiphala": r * cos_k,
            "bhujaphala": r * sin_bhuja,
            "hypotenuse": math.sqrt((1.0 + r * cos_k) ** 2 + (r * sin_bhuja) ** 2),
            "phala": pos["sighra_corr2"],
        })
    return {"rows": rows, "no_sighra": ["Sun", "Moon"]}


def _card_true_place(ctx: _Ctx) -> Dict[str, Any]:
    """ii.43-45: the four-step true place, with the longitude after each step."""
    rows = []
    for body in ch01.ALL_PLANETS:
        pos = ctx.positions[body]
        mean = pos["mean_lon"]
        if body in ("Sun", "Moon"):
            stages = [
                {"label": "Mean place", "correction": None, "longitude": mean},
                {"label": "Manda (whole)", "correction": pos["manda_corr"], "longitude": pos["true_longitude"]},
            ]
        else:
            half_sighra = ch02.normalize(mean + pos["sighra_corr1"] / 2.0)
            stages = [
                {"label": "Mean place", "correction": None, "longitude": mean},
                {"label": "Half sighra", "correction": pos["sighra_corr1"] / 2.0, "longitude": half_sighra},
                {"label": "Half manda", "correction": pos["manda_corr1"] / 2.0, "longitude": pos["ms1"]},
                {"label": "Whole manda, on the mean", "correction": pos["manda_corr2"], "longitude": pos["ms2"]},
                {"label": "Whole sighra", "correction": pos["sighra_corr2"], "longitude": pos["true_longitude"]},
            ]
        rows.append({
            "body": body,
            "true_longitude": pos["true_longitude"],
            "rashi": _rashi(pos["true_longitude"]),
            "stages": stages,
        })
    return {"rows": rows}


def _day_length(latitude: float, sun_tropical: float) -> Dict[str, Any]:
    """Declination, day-radius and the lengths of day and night (v.60-63).

    The day-radius is the verse's own rule: the radius less the versed sine of
    the declination. Day and night lengths come from ``ch03``, which uses
    the hour-angle formula rather than the text's tabular rule.
    """
    declination = ch03.declination(sun_tropical)
    return {
        "latitude": latitude,
        "sun_tropical": sun_tropical,
        "declination": declination,
        "direction": "north" if declination >= 0 else "south",
        "sine_declination": ch02.jya(declination),
        "versed_sine": ch02.utkrama_jya(declination),
        "day_radius": ch02.R_SINE - ch02.utkrama_jya(declination),
        "day_ghatis": ch03.day_length_ghatis(latitude, sun_tropical),
        "night_ghatis": ch03.night_length_ghatis(latitude, sun_tropical),
    }


def _card_day_length(ctx: _Ctx) -> Dict[str, Any]:
    """ii.60-63: day-radius and length of day for this date's true Sun."""
    sun = ctx.positions["Sun"]["true_longitude"]
    return _day_length(ctx.latitude, ch02.sidereal_to_tropical(sun, ctx.jd))


def _sun_moon(ctx: _Ctx) -> Tuple[float, float]:
    """The date's true Sun and Moon longitudes, which v.65-69 all start from."""
    return ctx.positions["Sun"]["true_longitude"], ctx.positions["Moon"]["true_longitude"]


def _card_yoga(ctx: _Ctx) -> Dict[str, Any]:
    """ii.65: the yoga, from the sum of the Sun's and Moon's longitudes."""
    sun, moon = _sun_moon(ctx)
    number, name = ch01.yoga_from_longitudes(sun, moon)
    span = 800.0 / 60.0
    combined = (sun + moon) % 360.0
    return {
        "sun": sun, "moon": moon, "sum": combined,
        "sum_arcmin": combined * 60.0, "span_deg": span,
        "number": number, "name": name,
        "fraction": (combined / span) % 1.0,
        "names": ch01.YOGA_NAMES,
    }


def _card_tithi(ctx: _Ctx) -> Dict[str, Any]:
    """ii.66: the lunar day, from the Moon's elongation from the Sun."""
    sun, moon = _sun_moon(ctx)
    number, fraction = ch01.tithi_from_elongation(moon, sun)
    return {
        "sun": sun, "moon": moon,
        "elongation": (moon - sun) % 360.0,
        "span_deg": 12.0,
        "number": number, "fraction": fraction,
        "paksha": "shukla" if number <= 15 else "krishna",
        "name": ch01.TITHI_NAMES[number - 1],
    }


def _card_karana(ctx: _Ctx) -> Dict[str, Any]:
    """ii.67-69: the karana, half a tithi, fixed or recurring."""
    sun, moon = _sun_moon(ctx)
    number, name, kind = ch01.karana_from_elongation(moon, sun)
    return {
        "sun": sun, "moon": moon,
        "elongation": (moon - sun) % 360.0,
        "span_deg": 6.0,
        "number": number, "name": name, "kind": kind,
        "half_of_tithi": 1 if number % 2 == 1 else 2,
        "recurring": ch01.KARANA_NAMES_RECURRING,
        "fixed": ch01.KARANA_NAMES_FIXED,
    }


# ─────────────────────────────  registry and route  ─────────────────────────────

#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "ii.15-27": (
        "15-27", "The table of sines",
        "The 24 tabular sines and versed sines of R = 3438, with their first differences.",
        False, _card_sine_table,
    ),
    "ii.31-33": (
        "31-33", "Interpolating a sine or an arc",
        "Between two tabular sines: the quotient, the remainder and the proportional part.",
        False, _card_interpolation,
    ),
    "ii.34-38": (
        "34-38", "The epicycles",
        "The sizes of the manda and sighra epicycles, and how they pulsate with the anomaly.",
        False, _card_epicycles,
    ),
    "ii.29-30": (
        "29-30", "Bhuja and koti of the anomaly",
        "The anomaly split by quadrant into its base (bhuja) and perpendicular (koti).",
        True, _card_bhuja_koti,
    ),
    "ii.39": (
        "39", "The equation of the apsis",
        "The manda correction: the epicycle's sine applied to the mean place.",
        True, _card_manda,
    ),
    "ii.40-42": (
        "40-42", "The equation of the conjunction",
        "The sighra correction, from the koti- and bhuja-phala and their hypotenuse.",
        True, _card_sighra,
    ),
    "ii.43-45": (
        "43-45", "The true place",
        "Half sighra, half manda, whole manda, whole sighra: the true longitude in four steps.",
        True, _card_true_place,
    ),
    "ii.60-63": (
        "60-63", "The day-radius and the length of the day",
        "From the Sun's declination: the day-radius, and the lengths of day and night.",
        True, _card_day_length,
    ),
    "ii.65": (
        "65", "The yoga",
        "The sum of the Sun's and Moon's longitudes, divided by 13°20′.",
        True, _card_yoga,
    ),
    "ii.66": (
        "66", "The lunar day",
        "The Moon's elongation from the Sun, divided by 12°.",
        True, _card_tithi,
    ),
    "ii.67-69": (
        "67-69", "The karana",
        "Half a lunar day: four fixed karanas and seven recurring ones.",
        True, _card_karana,
    ),
}


def _build_card(card_id: str, ctx: _Ctx) -> Dict[str, Any]:
    """Build one card's full payload, chrome fields included."""
    verses, title, does, date_dependent, builder = _CARDS[card_id]
    return {
        "id": card_id,
        "verses": verses,
        "title": title,
        "does": does,
        "date_dependent": date_dependent,
        **builder(ctx),
    }


@router.post("/chapter/2")
def chapter_2(body: Ch02In) -> Dict[str, Any]:
    """Every computational verse of Chapter 2, evaluated for one date."""
    try:
        jd = ch01.julian_day(body.year, body.month, float(body.day))
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    ctx = _Ctx(jd=jd, latitude=body.latitude)
    return {
        "chapter": 2,
        "title": CHAPTER_2_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "latitude": body.latitude,
        "order": CARD_ORDER,
        "rashis": ch01.RASHIS,
        "cards": {c: _build_card(c, ctx) for c in CARD_ORDER},
    }


def _need(value: Any, name: str, card: str) -> Any:
    """Return ``value`` or raise 422 naming the field ``card`` requires."""
    if value is None:
        raise HTTPException(status_code=422, detail=f"{card} needs '{name}'")
    return value


@router.post("/chapter/2/probe")
def chapter_2_probe(body: Ch02ProbeIn) -> Dict[str, Any]:
    """Evaluate one card's slider input against the library.

    Returns the same shape the card ships for its default case, so the React
    card can swap the probe's answer in without reshaping it.
    """
    card = body.card
    if card == "ii.29-30":
        return _decompose(_need(body.kendra, "kendra", card))
    if card == "ii.31-33":
        mode = _need(body.mode, "mode", card)
        if mode == "forward":
            return _interp_forward(_need(body.arc_deg, "arc_deg", card))
        return _interp_inverse(_need(body.sine, "sine", card))
    if card == "ii.34-38":
        planet = _need(body.body, "body", card)
        if planet not in ch01.ALL_PLANETS:
            raise HTTPException(status_code=422, detail=f"Unknown body '{planet}'")
        return _epicycle_at(planet, _need(body.kendra, "kendra", card))
    if card == "ii.60-63":
        return _day_length(
            _need(body.latitude, "latitude", card),
            _need(body.sun_longitude, "sun_longitude", card),
        )
    raise HTTPException(status_code=422, detail=f"No probe for card '{card}'")
