"""Verse-indexed payloads for the React "Book" page of Chapter 14.

Chapter 14 counterpart of ``book_ch13.py``: for a date, a conversion and a
choice of Jupiter method, what does each computational verse of *Of the
Different Modes of Reckoning Time* yield?

The nine manas (v.1-2) are shown with the date expressed in each; the solar
year (v.4-11) is that of the date's Gregorian year, with the shadasitimukhas
(v.4-6) and the sankrantis, ayanas, visuvats, ritus and punyakala (v.7-11);
v.12-14 is the Fathers' clock; v.15-16 the months and their asterisms with the
Moon's place; v.17 Jupiter's twelve-year cycle; and v.18-21 a converter over
the nine units with the kalpa's structure of manvantaras and sandhis.

Every card that rests on commentary says so. The shadasitimukhas' purpose is
not in the text (Burgess's note to v.6), and the heliacal naming of a Jovian
year is a reconstruction, shown only on request and marked ``commentary``.

Not laid out: v.22-27, the closing narrative, and v.28-30, which are Burgess's
own appendix matter, not the text.

Reference: SS Ch.14 v.1-21; Burgess (1860) pp.333-346
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, Tuple

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch14_reckoning_time as ch14

from .schemas import Ch14In

router = APIRouter(prefix="/book", tags=["book"])

CHAPTER_14_TITLE = "Of the Different Modes of Reckoning Time"

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER = ["xiv.1-2", "xiv.4-6", "xiv.7-11", "xiv.12-14", "xiv.15-16", "xiv.17", "xiv.18-21"]


def _date_of(jd: float) -> Dict[str, Any]:
    """Year, month and fractional day of a Julian Day."""
    year, month, day, frac = ch01.from_julian_day(jd)
    return {"year": year, "month": month, "day": day + frac}


@dataclass
class _Ctx:
    """The date, the conversion asked for and the Jupiter method."""

    year: int
    month: int
    day: float
    value: float
    from_mana: str
    to_mana: str
    heliacal: bool

    @cached_property
    def jd(self) -> float:
        """Julian Day of the date asked for."""
        return ch01.julian_day(self.year, self.month, self.day)

    @cached_property
    def solar_year(self) -> Any:
        """The solar year of the date's Gregorian year."""
        return ch14.solar_year(self.year)


def _with_date(row: Dict[str, Any], key: str = "jd", out: str = "date") -> Dict[str, Any]:
    """A copy of a dict with a calendar date beside one of its Julian Days."""
    return {**row, out: _date_of(row[key])}


# ─────────────────────────────  card builders  ─────────────────────────────

def _card_manas(ctx: _Ctx) -> Dict[str, Any]:
    """xiv.1-2: the nine modes, each with the date expressed in it."""
    panorama = ch14.reckon(ctx.jd)
    readings = {r.key: r for r in panorama.readings}
    return {
        "manas": [
            {**m.to_dict(), "count": readings[m.key].count,
             "reading_unit": readings[m.key].unit,
             "description": readings[m.key].description}
            for m in ch14.manas()
        ],
        "details": panorama.details,
    }


def _card_shadasitimukhas(ctx: _Ctx) -> Dict[str, Any]:
    """xiv.4-6: four points 86 degrees apart from Libra, and the sixteen degrees of Virgo."""
    return {
        "marks": [_with_date(m) for m in ch14.shadasitimukhas(ctx.year)],
        "note": ch14.load_catalog()["shadasitimukhas"]["note"],
    }


def _card_sankrantis(ctx: _Ctx) -> Dict[str, Any]:
    """xiv.7-11: the sign entries with punyakala, the ayanas and visuvats, and the six ritus."""
    sy = ctx.solar_year
    return {
        "year_days": sy.year_days,
        "sankrantis": [_with_date(e.to_dict()) for e in sy.sankrantis],
        "ayanas": {k: _with_date(v) for k, v in sy.ayanas.items()},
        "visuvats": {k: _with_date(v) for k, v in sy.visuvats.items()},
        "ritus": [
            {**r, "start": _date_of(r["start_jd"]), "end": _date_of(r["end_jd"])}
            for r in sy.ritus
        ],
    }


def _card_fathers(ctx: _Ctx) -> Dict[str, Any]:
    """xiv.12-14: the tithi, and where the moment falls in the Fathers' day."""
    clock = ch14.pitrya_clock(ctx.jd)
    return {
        **{k: v for k, v in clock.to_dict().items() if k not in ("next_noon_jd", "next_midnight_jd")},
        "tithi_name": ch01.TITHI_NAMES[clock.tithi - 1],
        "next_noon": _date_of(clock.next_noon_jd),
        "next_midnight": _date_of(clock.next_midnight_jd),
        "month_days": ch14.mana("pitrya").unit_days,
    }


def _card_asterisms(ctx: _Ctx) -> Dict[str, Any]:
    """xiv.15-16: the months and their asterisms, with the Moon's place at the date."""
    year, month, day, frac = ch01.from_julian_day(ctx.jd)
    from suryasiddhanta.ch02_true_places import compute

    moon = compute("Moon", year, month, day + frac).true_longitude
    _, asterism, pada, _ = ch01.nakshatra_from_longitude(moon)
    return {
        "months": ch14.month_asterisms(),
        "moon_longitude": moon,
        "moon_asterism": asterism,
        "moon_month": ch14.asterism_month(asterism),
    }


def _card_jupiter(ctx: _Ctx) -> Dict[str, Any]:
    """xiv.17: Jupiter's year by the mean method, a twelve-year cycle, and the heliacal method on request."""
    cycle = ch14.barhaspatya_cycle(ctx.year, 12)
    closing = ch14.barhaspatya_year(cycle[0].jd + 12 * ch14.mana("barhaspatya").unit_days)
    indexes = [y.name_index for y in cycle] + [closing.name_index]
    return {
        "mean": ch14.barhaspatya_year(ctx.jd).to_dict(),
        "heliacal": ch14.barhaspatya_year(ctx.jd, "heliacal").to_dict() if ctx.heliacal else None,
        "cycle": [
            {**y.to_dict(), "date": _date_of(y.jd), "advance": (indexes[i + 1] - indexes[i]) % 12}
            for i, y in enumerate(cycle)
        ],
    }


def _card_converter(ctx: _Ctx) -> Dict[str, Any]:
    """xiv.18-21: a value converted between two modes, every unit's length, and the kalpa's structure."""
    return {
        "value": ctx.value,
        "from_mana": ctx.from_mana,
        "to_mana": ctx.to_mana,
        "result": ch14.convert(ctx.value, ctx.from_mana, ctx.to_mana),
        "units": [
            {"key": m.key, "iast": m.iast, "unit": m.unit, "unit_days": m.unit_days}
            for m in ch14.manas()
        ],
        "structure": {
            "manvantaras": 14,
            "manvantara_years": 71 * ch01.MAHAYUGA,
            "sandhis": 15,
            "sandhi_years": ch01.KRITA_YUGA,
            "total_years": 14 * 71 * ch01.MAHAYUGA + 15 * ch01.KRITA_YUGA,
            "kalpa_years": ch01.KALPA,
        },
    }


#: card id -> (verses, title, does, date_dependent, builder).
_CARDS: Dict[str, Tuple[str, str, str, bool, Callable[[_Ctx], Dict[str, Any]]]] = {
    "xiv.1-2": (
        "1-2", "The nine modes of time",
        "Brahma's, the gods', the Fathers', Prajapati's, Jupiter's, solar, civil, lunar and sidereal time; four are used in practice.",
        True, _card_manas,
    ),
    "xiv.4-6": (
        "4-6", "The shadasitimukhas",
        "Four points at 86-degree intervals from Libra leave sixteen degrees at the end of Virgo. The text gives where they are; Burgess finds nothing on what they are for.",
        True, _card_shadasitimukhas,
    ),
    "xiv.7-11": (
        "7-11", "The solar year and the sign entries",
        "Two equinoxes and two solstices lie on the same diameter; the Sun's entries into the twelve signs divide the year into progresses, seasons and months. The auspicious time at each entry is the time his disk takes to cross the boundary.",
        True, _card_sankrantis,
    ),
    "xiv.12-14": (
        "12-14", "The tithi and the day of the Fathers",
        "A tithi is twelve degrees of elongation, thirty make a lunar month, and a lunar month is one day and night of the Fathers: new moon their midday, full moon their midnight.",
        True, _card_fathers,
    ),
    "xiv.15-16": (
        "15-16", "The months and their asterisms",
        "The months from Kartika take the asterisms from Krittika two by two; the fifth, the last but one and the last take three.",
        True, _card_asterisms,
    ),
    "xiv.17": (
        "17", "Jupiter's years",
        "The years of Jupiter's twelve-year cycle bear the names of the months, from the asterism he stands in. The text's own rule names the year from his heliacal rising.",
        True, _card_jupiter,
    ),
    "xiv.18-21": (
        "18-21", "Civil time, and the times of the gods and of Brahma",
        "Civil time runs from sunrise to sunrise. The gods' day is a year, Prajapati's a manvantara of 71 mahayugas, Brahma's a kalpa; fourteen manvantaras and fifteen sandhis make one.",
        False, _card_converter,
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


@router.post("/chapter/14")
def chapter_14(body: Ch14In) -> Dict[str, Any]:
    """Every computational verse of Chapter 14, for a date, a conversion and a Jupiter method."""
    ctx = _Ctx(
        year=body.year, month=body.month, day=float(body.day), value=body.value,
        from_mana=body.from_mana, to_mana=body.to_mana, heliacal=body.heliacal,
    )
    try:
        jd = ctx.jd
        cards = {c: _build_card(c, ctx) for c in CARD_ORDER}
    except (ValueError, OverflowError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=f"Cannot compute: {exc}") from exc

    return {
        "chapter": 14,
        "title": CHAPTER_14_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "value": body.value,
        "from_mana": body.from_mana,
        "to_mana": body.to_mana,
        "heliacal": body.heliacal,
        "order": CARD_ORDER,
        "cards": cards,
    }
