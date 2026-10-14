"""Verse-indexed payloads for the React "Book" pages.

Where ``calc.py`` answers task-shaped questions ("what is the Moon's
position"), this module answers verse-shaped ones: for one date, what does
each computational verse of a chapter yield? The React chapter page renders
one card per entry of ``CARD_ORDER``, in the book's own verse order.

The shaping lives here rather than in ``chatbot/tools.py`` for the same
reason the planet-position, all-planets and stars routes shape their own
results: these are UI-facing field sets, and twelve more entries in the
agent's tool list would serve no chatbot answer.

Reference: SS Ch.1 v.11-58; Burgess (1860) pp.1-38
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List

from fastapi import APIRouter, HTTPException

from suryasiddhanta import ch01_mean_motions as ch01

from .calc import _tool
from .schemas import Ch01In

router = APIRouter(prefix="/book", tags=["book"])

#: Card ids in the order the chapter states them. The React page walks this.
CARD_ORDER: List[str] = [
    "i.11-13",
    "i.15-22",
    "i.23-24",
    "i.29-34",
    "i.35-37",
    "i.41-42",
    "i.43-44",
    "i.48-51",
    "i.52-vara",
    "i.52-54",
    "i.55",
    "i.56-58",
]

CHAPTER_1_TITLE = "Of the Mean Motions of the Planets"

#: The five star-planets, in the text's own order (v.29-34).
_STAR_PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def _dms(degrees: float) -> str:
    """Format a longitude in degrees as ``d° m' s"``, normalized to [0, 360)."""
    deg = degrees % 360.0
    d = int(deg)
    minutes_total = (deg - d) * 60.0
    m = int(minutes_total)
    s = (minutes_total - m) * 60.0
    return f"{d}° {m:02d}' {s:05.2f}\""


def _rashi(longitude: float) -> str:
    """Format a longitude as its sign and the degrees elapsed within it."""
    _, name, deg_in = ch01.rashi_from_longitude(longitude)
    return f"{name} {deg_in:.2f}°"


#: The two reckonings of i.11-13, each in ascending order, with the step
#: from one unit to the next. The card's converter scales by ``seconds``;
#: the steps are what let it show the chain as the text states it
#: ("six respirations make a vinadi").
_TIME_CHAINS = [
    {
        "key": "ss",
        "label": "The text's own reckoning",
        "verses": "11-12",
        "source": "verse",
        "sequence": ["prana", "vinadi", "nadi", "ahoratra"],
        "aliases": {"vinadi": "pala", "nadi": "ghatika", "ahoratra": "day and night"},
    },
    {
        "key": "puranic",
        "label": "Subdivisions from later authorities",
        "verses": "11",
        "source": "commentary",
        "sequence": ["truti", "tatpara", "nimesha", "kashtha", "kala", "nadi", "muhurta"],
        "aliases": {"nadi": "ghatika"},
    },
    {
        "key": "long",
        "label": "Longer measures",
        "verses": "12-13",
        "source": "verse",
        "sequence": ["ahoratra", "paksha", "masa", "ritu", "ayana", "samvatsara"],
        "aliases": {
            "ahoratra": "day and night", "paksha": "half-month",
            "masa": "month", "ritu": "season", "ayana": "half-year",
            "samvatsara": "sidereal year",
        },
    },
]


def _card_time_units() -> Dict[str, Any]:
    """The divisions of time, i.11-13, as a convertible chain.

    Ships every unit's length in seconds so the card's slider can convert
    between any two of them in the browser without a round trip: a
    conversion is a ratio of these two numbers and nothing more.

    Three chains, not one. The text gives the respiration upward (v.11-12)
    and the longer measures (v.12-13); the truti-to-kala subdivisions come
    from Burgess's note, which is why they carry ``source: commentary``.
    """
    units = {**ch01.TIME_UNITS_NON_SS_SEC, **ch01.TIME_UNITS_SS_SEC}
    chains = []
    for chain in _TIME_CHAINS:
        steps = []
        for i, name in enumerate(chain["sequence"]):
            seconds = units[name]
            nxt = chain["sequence"][i + 1] if i + 1 < len(chain["sequence"]) else None
            steps.append({
                "unit": name,
                "alias": chain["aliases"].get(name),
                "seconds": seconds,
                "days": seconds / 86400.0,
                "next": nxt,
                "per_next": None if nxt is None else round(units[nxt] / seconds, 6),
                "in_ss_text": name in ch01.TIME_UNITS_SS_SEC,
            })
        chains.append({
            "key": chain["key"], "label": chain["label"],
            "verses": chain["verses"], "source": chain["source"],
            "units": steps,
        })

    return {
        "chains": chains,
        "units_seconds": units,
        "ghatis_per_day": ch01.GHATIS_PER_DAY,
        "palas_per_ghati": ch01.PALAS_PER_GHATI,
        "vipalas_per_pala": ch01.VIPALAS_PER_PALA,
        "ghati_minutes": ch01.ghati_to_minutes(1.0),
        "note": (
            "The text itself stops at the respiration (prana): v.11 names "
            "the truti only to say the unreal measures begin there. Truti "
            "through kala come from Burgess's note, and are reckoned down "
            "from the nadi so that thirty kalas make one ghatika exactly."
        ),
    }


def _card_yugas() -> Dict[str, Any]:
    """The Ages, the Aeon, and the day counts of an Age, i.15-22 with v.37-40."""
    return {
        "ages": [
            {"name": "Krita", "years": ch01.KRITA_YUGA},
            {"name": "Treta", "years": ch01.TRETA_YUGA},
            {"name": "Dvapara", "years": ch01.DVAPARA_YUGA},
            {"name": "Kali", "years": ch01.KALI_YUGA},
        ],
        "mahayuga_years": ch01.MAHAYUGA,
        "kalpa_years": ch01.KALPA,
        "mahayugas_per_kalpa": ch01.KALPA // ch01.MAHAYUGA,
        "civil_days_per_mahayuga": ch01.CIVIL_DAYS_PER_MAHAYUGA,
        "sidereal_days_per_mahayuga": ch01.SIDEREAL_DAYS_PER_MAHAYUGA,
        "lunar_months_per_mahayuga": ch01.LUNAR_MONTHS_PER_MAHAYUGA,
        "civil_days_per_kalpa": ch01.CIVIL_DAYS_PER_KALPA,
        "sidereal_year_days": ch01.SIDEREAL_YEAR_DAYS,
    }


def _card_epoch(jd: float) -> Dict[str, Any]:
    """The Kali epoch and the time elapsed to this date, i.23-24."""
    year, month, day, _ = ch01.from_julian_day(ch01.KALI_EPOCH_JD)
    elapsed = ch01.kali_years_elapsed(jd)
    return {
        "kali_epoch_jd": ch01.KALI_EPOCH_JD,
        "kali_epoch_date": f"{abs(year) + 1} BCE, {month:02d}-{day:02d} (Julian)",
        "jd": jd,
        "ahargana": ch01.ahargana(jd),
        "kali_years_elapsed": elapsed,
        "kali_era_year": ch01.kali_era_year(jd),
        "yuga_elapsed_fraction": ch01.yuga_elapsed_fraction(jd),
        "kali_fraction_elapsed": (elapsed % ch01.KALI_YUGA) / ch01.KALI_YUGA,
        "note": (
            "The Kali epoch stands at 0.9 of the current Age: Krita, Treta "
            "and Dvapara together are 3,888,000 of its 4,320,000 years."
        ),
    }


def _card_bhagana() -> Dict[str, Any]:
    """Revolutions in an Age, and the daily motions that follow, i.29-34."""
    rows = []
    for body, revolutions in ch01.BHAGANA.items():
        motion = ch01.MEAN_DAILY_MOTION[body]
        rows.append({
            "body": body,
            "revolutions": revolutions,
            "daily_motion_deg": motion,
            "daily_motion_arcmin": motion * 60.0,
            "period_days": abs(ch01.CIVIL_DAYS_PER_MAHAYUGA / revolutions),
        })
    return {
        "rows": rows,
        "civil_days_per_mahayuga": ch01.CIVIL_DAYS_PER_MAHAYUGA,
        "note": (
            "Mercury and Venus have no revolutions of their own: v.29 gives "
            "them the Sun's 4,320,000, and the larger counts here belong to "
            "their conjunctions (sighra)."
        ),
    }


def _card_mean_longitude_rule(jd: float) -> Dict[str, Any]:
    """The rule for a mean place, i.35-37, worked with this date's own terms."""
    a = ch01.ahargana(jd)
    worked = []
    for body in ["Sun", "Moon", "Mars", "Jupiter", "Saturn"]:
        revolutions = ch01.BHAGANA[body]
        turns = revolutions * a / ch01.CIVIL_DAYS_PER_MAHAYUGA
        longitude = ch01.mean_longitude(body, jd)
        worked.append({
            "body": body,
            "revolutions": revolutions,
            "turns_elapsed": turns,
            "fraction_of_turn": turns % 1.0,
            "longitude": longitude,
            "longitude_dms": _dms(longitude),
        })
    return {
        "formula": "mean longitude = frac(bhagana × ahargana ÷ civil days in an Age) × 360°",
        "bhagana": dict(ch01.BHAGANA),
        "ahargana": a,
        "civil_days_per_mahayuga": ch01.CIVIL_DAYS_PER_MAHAYUGA,
        "sidereal_year_days": ch01.SIDEREAL_YEAR_DAYS,
        "worked": worked,
    }


def _card_apsides(jd: float) -> Dict[str, Any]:
    """The apsides (mandocca) and where they now stand, i.41-42 with v.33.

    The Moon's apsis is the odd one: it is reckoned per Age (v.33), the
    other six per Aeon (v.41-42), so its revolution count is a thousand
    times faster than the column beside it suggests.
    """
    rows = [{
        "planet": "Moon",
        "revolutions": ch01.BHAGANA["Moon_apogee"],
        "per": "Age",
        "epoch_longitude": ch01.MANDOCCA_AT_EPOCH["Moon"],
        "daily_motion": ch01.BHAGANA["Moon_apogee"] * 360.0 / ch01.CIVIL_DAYS_PER_MAHAYUGA,
        "longitude": ch01.mandocca_longitude("Moon", jd),
    }]
    for planet in ["Sun"] + _STAR_PLANETS:
        revolutions = ch01.MANDOCCA_REVOLUTIONS_KALPA[planet]
        rows.append({
            "planet": planet,
            "revolutions": revolutions,
            "per": "Aeon",
            "epoch_longitude": ch01.MANDOCCA_AT_EPOCH[planet],
            "daily_motion": revolutions * 360.0 / ch01.CIVIL_DAYS_PER_KALPA,
            "longitude": ch01.mandocca_longitude(planet, jd),
        })
    for row in rows:
        row["longitude_dms"] = _dms(row["longitude"])
        row["rashi"] = _rashi(row["longitude"])
    return {"rows": rows, "ahargana": ch01.ahargana(jd)}


def _card_nodes(jd: float) -> Dict[str, Any]:
    """The nodes and where they now stand, i.43-44 with v.33.

    Every node moves retrograde. The Moon's is reckoned per Age, the five
    star-planets' per Aeon.
    """
    moon_node = ch01.moon_node_longitude(jd)
    rows = [{
        "planet": "Moon",
        "revolutions": ch01.BHAGANA["Moon_node"],
        "per": "Age",
        "epoch_longitude": 180.0,
        "daily_motion": -ch01.BHAGANA["Moon_node"] * 360.0 / ch01.CIVIL_DAYS_PER_MAHAYUGA,
        "longitude": moon_node,
    }]
    for planet in _STAR_PLANETS:
        revolutions = ch01.NODE_REVOLUTIONS_KALPA[planet]
        rows.append({
            "planet": planet,
            "revolutions": revolutions,
            "per": "Aeon",
            "epoch_longitude": ch01.NODE_AT_EPOCH[planet],
            "daily_motion": -revolutions * 360.0 / ch01.CIVIL_DAYS_PER_KALPA,
            "longitude": ch01.planet_node_longitude(planet, jd),
        })
    for row in rows:
        row["longitude_dms"] = _dms(row["longitude"])
        row["rashi"] = _rashi(row["longitude"])
    return {"rows": rows, "direction": "retrograde", "ahargana": ch01.ahargana(jd)}


def _luni_solar_triple(jd: float) -> Dict[str, int]:
    """Elapsed years, luni-solar months and tithis for a date, from mean places.

    The i.48-51 route takes a luni-solar date, not a Julian Day, so one has
    to be derived to drive the card from the page's date picker. Everything
    here comes from Chapter 1 itself: the year from the elapsed Kali years,
    the months from the mean Sun's distance round the circle, the tithis
    from the mean elongation of Moon and Sun at twelve degrees each.

    These are *mean* elements, so the triple is the mean luni-solar date,
    which is what the mean-motion chapter can state. It is not the true
    panchanga date of Chapter 2.

    The month count runs one ahead of the Sun's completed signs, because
    the luni-solar months are counted from Chaitra and the solar from
    Vaishakha — the same offset ``masa_from_sun_longitude`` applies. That
    reproduces Burgess's own triple for Jan 1, 1860 (4960 y., 9 m., 7 d.).

    It is a derivation, not an inversion: within a few days of a month
    boundary the count can land one month out, and the card shows the
    resulting gap against the ahargana rather than hiding it. The card's
    own inputs are there to be moved off this starting point.
    """
    a = ch01.ahargana(jd)
    sun_revolutions = ch01.BHAGANA["Sun"] * a / ch01.CIVIL_DAYS_PER_MAHAYUGA
    synodic = (
        (ch01.BHAGANA["Moon"] - ch01.BHAGANA["Sun"]) * a
        / ch01.CIVIL_DAYS_PER_MAHAYUGA
    )
    years = int(sun_revolutions)
    months = 0 if a <= 0 else int((sun_revolutions - years) * 12.0) + 1
    tithis = int((synodic - int(synodic)) * 30.0)
    return {"years": years, "months": months, "tithis": tithis}


def _card_ahargana_route(jd: float) -> Dict[str, Any]:
    """The ahargana by the text's own route, i.48-51.

    Reuses ``tools.compute_ahargana_verse_route`` — the same shaping the
    ``/calc/ahargana-verse`` route serves — so the intermediates are stated
    once in the codebase. The direct subtraction from the epoch is carried
    alongside for comparison: the two agree when the luni-solar triple is
    the exact one, and the difference shown here is the error in the mean
    triple derived above, not a disagreement between the two methods.
    """
    triple = _luni_solar_triple(jd)
    route = _tool(
        "compute_ahargana_verse_route",
        years=triple["years"], months=triple["months"], tithis=triple["tithis"],
        from_creation=False,
    )
    direct = ch01.ahargana(jd)
    by_route = route.get("civil_days")
    return {
        "input": triple,
        "route": route,
        "direct_ahargana": direct,
        "difference_days": None if by_route is None else by_route - direct,
        "solar_months_per_mahayuga": ch01.SOLAR_MONTHS_PER_MAHAYUGA,
        "adhimasa_per_mahayuga": ch01.ADHIMASA_PER_MAHAYUGA,
        "lunar_days_per_mahayuga": ch01.LUNAR_DAYS_PER_MAHAYUGA,
        "tithikshaya_per_mahayuga": ch01.TITHIKSHAYA_PER_MAHAYUGA,
        "note": (
            "The elapsed years, months and tithis are derived from this "
            "date's mean places, so they are the mean luni-solar date. Give "
            "the exact triple and the route returns the ahargana exactly."
        ),
    }


def _card_vara(jd: float) -> Dict[str, Any]:
    """The lord of the day, i.52."""
    index, name = ch01.vara(jd)
    return {
        "number": index,
        "name": name,
        "name_en": ch01.VARA_NAMES_EN[index],
        "order": [
            {"number": i, "name": n, "name_en": ch01.VARA_NAMES_EN[i]}
            for i, n in enumerate(ch01.VARA_NAMES)
        ],
    }


def _card_mean_places(jd: float) -> Dict[str, Any]:
    """Mean places of the planets for this date, i.52-54."""
    positions = ch01.compute_all_mean_positions(jd)
    rows = []
    for planet in ch01.ALL_PLANETS:
        longitude = getattr(positions, planet)
        row = {
            "planet": planet,
            "longitude": longitude,
            "longitude_dms": _dms(longitude),
            "rashi": _rashi(longitude),
            "sighrocca": None,
            "sighrocca_dms": None,
        }
        if planet != "Sun" and planet != "Moon":
            sighrocca = ch01.sighrocca_longitude(planet, jd)
            row["sighrocca"] = sighrocca
            row["sighrocca_dms"] = _dms(sighrocca)
        rows.append(row)
    for label, longitude in [
        ("Moon's apsis", positions.Moon_apogee),
        ("Moon's node", positions.Moon_node),
    ]:
        rows.append({
            "planet": label,
            "longitude": longitude,
            "longitude_dms": _dms(longitude),
            "rashi": _rashi(longitude),
            "sighrocca": None,
            "sighrocca_dms": None,
        })
    return {
        "rows": rows,
        "ahargana": ch01.ahargana(jd),
        "civil_days_per_mahayuga": ch01.CIVIL_DAYS_PER_MAHAYUGA,
        # What a slider needs to re-evaluate v.35 for another ahargana
        # without asking the server: the revolution count, where the body
        # stood at the epoch, and which way it moves (v.57-58).
        "bodies": [
            {"planet": "Sun", "bhagana": ch01.BHAGANA["Sun"], "epoch": 0.0, "retrograde": False},
            {"planet": "Moon", "bhagana": ch01.BHAGANA["Moon"], "epoch": 0.0, "retrograde": False},
            {"planet": "Mars", "bhagana": ch01.BHAGANA["Mars"], "epoch": 0.0, "retrograde": False},
            {"planet": "Mercury", "bhagana": ch01.BHAGANA["Sun"], "epoch": 0.0, "retrograde": False},
            {"planet": "Jupiter", "bhagana": ch01.BHAGANA["Jupiter"], "epoch": 0.0, "retrograde": False},
            {"planet": "Venus", "bhagana": ch01.BHAGANA["Sun"], "epoch": 0.0, "retrograde": False},
            {"planet": "Saturn", "bhagana": ch01.BHAGANA["Saturn"], "epoch": 0.0, "retrograde": False},
            {"planet": "Moon's apsis", "bhagana": ch01.BHAGANA["Moon_apogee"],
             "epoch": 90.0, "retrograde": False},
            {"planet": "Moon's node", "bhagana": ch01.BHAGANA["Moon_node"],
             "epoch": 180.0, "retrograde": True},
        ],
        "sighrocca": [
            {"planet": "Mercury", "bhagana": ch01.BHAGANA["Mercury_sighrocca"]},
            {"planet": "Venus", "bhagana": ch01.BHAGANA["Venus_sighrocca"]},
            {"planet": "Mars", "bhagana": ch01.BHAGANA["Sun"]},
            {"planet": "Jupiter", "bhagana": ch01.BHAGANA["Sun"]},
            {"planet": "Saturn", "bhagana": ch01.BHAGANA["Sun"]},
        ],
        "note": (
            "Mercury and Venus take the Sun's mean place; their own motion "
            "enters through the sighrocca column."
        ),
    }


def _card_samvatsara(jd: float) -> Dict[str, Any]:
    """The current year of Jupiter's sixty-year cycle, i.55."""
    index, name = ch01.samvatsara(jd)
    revolutions = ch01.BHAGANA["Jupiter"] * ch01.ahargana(jd) / ch01.CIVIL_DAYS_PER_MAHAYUGA
    return {
        "number": index + 1,
        "name": name,
        "jupiter_revolutions": revolutions,
        "jovian_years_elapsed": int(revolutions * 12.0),
        "counted_from": "Vijaya",
        "names": ch01.SAMVATSARA_NAMES,
        "vijaya_index": ch01.SAMVATSARA_NAMES.index("Vijaya"),
        "jupiter_bhagana": ch01.BHAGANA["Jupiter"],
        "civil_days_per_mahayuga": ch01.CIVIL_DAYS_PER_MAHAYUGA,
        "ahargana": ch01.ahargana(jd),
        "note": (
            "v.55 counts the remainder from Vijaya, the 27th year of the "
            "cycle as popularly numbered from Prabhava."
        ),
    }


def _card_epoch_positions() -> Dict[str, Any]:
    """Reckoning from a later epoch, and the positions at the Kali epoch, i.56-58.

    v.57 puts every planet and every conjunction at the first of Aries at
    the end of the Golden Age. The apsides and nodes do not start there, so
    their epoch positions are the ones that have to be carried; they are
    derived from the Aeon rates, and match Burgess's Iron-Age table.
    """
    rows = []
    for planet in ["Sun"] + _STAR_PLANETS:
        rows.append({
            "planet": planet,
            "mandocca": ch01.MANDOCCA_AT_EPOCH[planet],
            "mandocca_dms": _dms(ch01.MANDOCCA_AT_EPOCH[planet]),
            "node": ch01.NODE_AT_EPOCH.get(planet),
            "node_dms": None if planet not in ch01.NODE_AT_EPOCH
            else _dms(ch01.NODE_AT_EPOCH[planet]),
        })
    rows.insert(0, {
        "planet": "Moon",
        "mandocca": ch01.MANDOCCA_AT_EPOCH["Moon"],
        "mandocca_dms": _dms(ch01.MANDOCCA_AT_EPOCH["Moon"]),
        "node": 180.0,
        "node_dms": _dms(180.0),
    })
    return {
        "rows": rows,
        "years_creation_to_kali": ch01.YEARS_CREATION_TO_KALI,
        "civil_days_creation_to_kali": ch01.CIVIL_DAYS_CREATION_TO_KALI,
        "quarter_ages": ch01.YEARS_CREATION_TO_KALI // (ch01.MAHAYUGA // 4),
        "note": (
            "v.56 allows the count to be kept from a later epoch, which is "
            "what reckoning from the Kali epoch rather than from creation "
            "does: it subtracts these civil days."
        ),
    }


#: Card id -> (verse range, title, one-line statement, builder).
#: A builder taking no argument marks a card that does not vary with date.
_CARDS: Dict[str, tuple] = {
    "i.11-13": (
        "11-13", "Divisions of time",
        "The sidereal time units of the text, and the finer ones later authors add.",
        _card_time_units,
    ),
    "i.15-22": (
        "15-22", "The Ages and the Aeon",
        "The lengths of the four Ages, of an Age and an Aeon, and the days in each.",
        _card_yugas,
    ),
    "i.23-24": (
        "23-24", "The Kali epoch and time elapsed",
        "Civil days and sidereal years from the Kali epoch to this date.",
        _card_epoch,
    ),
    "i.29-34": (
        "29-34", "Revolutions in an Age",
        "The revolution counts the whole system rests on, and their daily motions.",
        _card_bhagana,
    ),
    "i.35-37": (
        "35-37", "The rule for a mean place",
        "The v.35 proportion, worked with this date's own ahargana.",
        _card_mean_longitude_rule,
    ),
    "i.41-42": (
        "41-42", "The apsides",
        "Where each apsis (mandocca) stands on this date, from its Aeon rate.",
        _card_apsides,
    ),
    "i.43-44": (
        "43-44", "The nodes",
        "Where each ascending node stands on this date, moving retrograde.",
        _card_nodes,
    ),
    "i.48-51": (
        "48-51", "The ahargana by the text's route",
        "Years to solar months, add the intercalary, to lunar days, drop the omitted.",
        _card_ahargana_route,
    ),
    "i.52-vara": (
        "52", "The lord of the day",
        "The weekday, the first of the two rules v.52 carries.",
        _card_vara,
    ),
    "i.52-54": (
        "52-54", "Mean places of the planets",
        "Every mean longitude for this date, with the conjunctions of the inner planets.",
        _card_mean_places,
    ),
    "i.55": (
        "55", "The year of Jupiter's cycle",
        "The samvatsara, from Jupiter's elapsed revolutions.",
        _card_samvatsara,
    ),
    "i.56-58": (
        "56-58", "Epochs, and positions at the epoch",
        "What the apsides and nodes stood at in 3102 BCE, and what a later epoch costs.",
        _card_epoch_positions,
    ),
}


def _build_card(card_id: str, jd: float) -> Dict[str, Any]:
    """Build one card's full payload, chrome fields included."""
    verses, title, does, builder = _CARDS[card_id]
    date_dependent = builder.__code__.co_argcount > 0
    values: Callable[..., Dict[str, Any]] = builder
    return {
        "id": card_id,
        "verses": verses,
        "title": title,
        "does": does,
        "date_dependent": date_dependent,
        **(values(jd) if date_dependent else values()),
    }


@router.post("/chapter/1")
def chapter_1(body: Ch01In) -> Dict[str, Any]:
    """Every computational verse of Chapter 1, evaluated for one date."""
    try:
        jd = ch01.julian_day(body.year, body.month, float(body.day))
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Bad date: {exc}") from exc

    return {
        "chapter": 1,
        "title": CHAPTER_1_TITLE,
        "jd": jd,
        "date": {"year": body.year, "month": body.month, "day": body.day},
        "order": CARD_ORDER,
        "rashis": ch01.RASHIS,
        "cards": {card_id: _build_card(card_id, jd) for card_id in CARD_ORDER},
    }
