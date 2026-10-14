"""
Chapter 14: Of the Different Modes of Reckoning Time (Manadhyaya)
================================================================

The text's calendar chapter. It lists the nine *manas*, the modes of
measuring time, says which are used in practice, and then describes the
solar year in some detail.

Much of what it enumerates is already computed elsewhere in the library
(civil days and the tithi in Ch.1, the gods' and Brahma's days and the
regents in Ch.12, heliacal events in Ch.9), so this module composes those
rather than repeating them. What is new here:

- **The nine manas as one system** (v.1-2, 12-13, 18-21): `manas`, `mana`,
  `convert` and `reckon`.
- **The solar year** (v.3-11): the twelve sankrantis, the sankranti
  punyakala, the ayanas and visuvats, the shadasitimukhas and the ritus.
- **The Fathers' clock** (v.14): a lunar month is one day and night of the
  Fathers, new moon their midday and full moon their midnight.
- **Months and asterisms** (v.15-16).
- **Jupiter's twelve-year cycle** (v.17), named from his asterism. Separate
  from, and not replacing, `ch01.samvatsara`, the sixty-year cycle of i.55.

Longitudes are sidereal, as everywhere. The nine unit lengths are in civil
days, so `convert` is a ratio.

Two limits worth knowing. `ch04.apparent_diameter_sun` returns a constant,
so the punyakala varies with the Sun's daily motion but not with his
distance, where the text implies both; the fix belongs in Ch.4. And xiv.17 is
a single terse verse: both the mean and the heliacal methods of naming a
Jovian year are reconstructions, marked `source="commentary"`.

Reference: SS Ch.14; Burgess (1860) pp.333-346
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from suryasiddhanta._types import (
    BarhaspatyaYear, Mana, ManaReading, PitryaClock, ReckoningPanorama,
    SankrantiEvent, SolarYearStructure,
)
from suryasiddhanta.ch01_mean_motions import (
    BHAGANA, CIVIL_DAYS_PER_KALPA, CIVIL_DAYS_PER_MAHAYUGA, KRITA_YUGA,
    MAHAYUGA, RASHIS, RITU_NAMES, RITU_NAMES_EN,
    SIDEREAL_DAYS_PER_MAHAYUGA, SIDEREAL_YEAR_DAYS, TITHI_NAMES,
    YEARS_CREATION_TO_KALI, ahargana, from_julian_day, julian_day,
    kali_era_year, kali_years_elapsed, masa_from_sun_longitude,
    mean_longitude, nakshatra_from_longitude, samvatsara, vara,
    VARA_NAMES_EN,
)
from suryasiddhanta.ch02_true_places import ayanamsha, compute
from suryasiddhanta.ch04_lunar_eclipses import apparent_diameter_sun
from suryasiddhanta.ch12_cosmography import (
    SYNODIC_MONTH_DAYS, _bisect, brahma_day_elapsed, day_of_the_gods,
    sun_crossing_jd,
)

#: Years the solver accepts. The library's point is that old dates work,
#: but a year far out cannot be bracketed by the crossing solver.
MIN_YEAR, MAX_YEAR = -3000, 5000

#: Sidereal longitudes (degrees) of the four shadasitimukhas, v.4-6: 86
#: degrees apart from Libra (180), leaving 16 at the end of Virgo.
SHADASITIMUKHA_ARC = 86
SHADASITIMUKHA_LONGITUDES = (266, 352, 78, 164)
VIRGO_REMAINDER = 16


# ─────────────────────────────────────────────────────────────────
#  THE CATALOG
# ─────────────────────────────────────────────────────────────────

_CATALOG: Optional[dict] = None


def load_catalog() -> dict:
    """
    Load the mana catalog from the bundled JSON file.

    Returns:
        The catalog: the nine manas, the months-and-asterisms table and
        the shadasitimukha notes.
    """
    global _CATALOG
    if _CATALOG is None:
        path = os.path.join(os.path.dirname(__file__), "data", "mana_catalog.json")
        with open(path, encoding="utf-8") as handle:
            _CATALOG = json.load(handle)
    return _CATALOG


# ─────────────────────────────────────────────────────────────────
#  THE NINE MANAS — SS xiv.1-2, 12-13, 18-21
# ─────────────────────────────────────────────────────────────────

def _unit_days() -> Dict[str, float]:
    """Each mana's unit length in civil days (see the design for the sources)."""
    return {
        "savana": 1.0,
        "naksatra": CIVIL_DAYS_PER_MAHAYUGA / SIDEREAL_DAYS_PER_MAHAYUGA,
        "candra": SYNODIC_MONTH_DAYS / 30.0,
        "saura": SIDEREAL_YEAR_DAYS / 360.0,
        "pitrya": SYNODIC_MONTH_DAYS,
        "daiva": SIDEREAL_YEAR_DAYS,
        "barhaspatya": CIVIL_DAYS_PER_MAHAYUGA / BHAGANA["Jupiter"] / 12.0,
        "prajapatya": 71.0 * CIVIL_DAYS_PER_MAHAYUGA,
        "brahma": float(CIVIL_DAYS_PER_KALPA),
    }


def manas() -> List[Mana]:
    """
    The nine modes of reckoning time, in the order of verse 1.

    Returns:
        One Mana per mode: Brahma, the gods, the Fathers, Prajapati,
        Jupiter, solar, civil, lunar, sidereal.
    """
    days = _unit_days()
    return [Mana(unit_days=days[row["key"]], **row) for row in load_catalog()["manas"]]


def mana(key: str) -> Mana:
    """
    One mana by key.

    Raises:
        ValueError: if the key is not one of the nine, naming them.
    """
    for entry in manas():
        if entry.key == str(key).lower():
            return entry
    raise ValueError(f"Unknown mana {key!r}. Known: {', '.join(m.key for m in manas())}")


def convert(value: float, from_mana: str, to_mana: str) -> float:
    """
    Convert an amount from one mana's unit to another's.

    A ratio of unit lengths in civil days, so a round trip is exact to
    floating-point tolerance.

    Raises:
        ValueError: for an unknown mana key.
    """
    return value * mana(from_mana).unit_days / mana(to_mana).unit_days


def _sun_moon(jd: float):
    """The Sun's and Moon's true places at a Julian Day."""
    year, month, day, frac = from_julian_day(jd)
    return compute("Sun", year, month, day + frac), compute("Moon", year, month, day + frac)


def manvantara_position(jd: float) -> dict:
    """
    Where a Julian Day falls among the fourteen manvantaras (xiv.21, i.15-18).

    A kalpa opens with a sandhi of one krita yuga, then each of the fourteen
    manvantaras of 71 mahayugas is followed by another sandhi.

    Args:
        jd: Julian Day.

    Returns:
        number (1-14), year_within (years into that manvantara, or into the
        sandhi after it), in_sandhi, and the manvantara's length in years.
    """
    elapsed = YEARS_CREATION_TO_KALI + kali_years_elapsed(jd) - KRITA_YUGA
    length = 71 * MAHAYUGA
    cycle = length + KRITA_YUGA
    index, within = divmod(max(elapsed, 0.0), cycle)
    in_sandhi = within >= length
    return {
        "number": int(index) + 1,
        "year_within": within - length if in_sandhi else within,
        "in_sandhi": in_sandhi,
        "length_years": length,
    }


def reckon(jd: float) -> ReckoningPanorama:
    """
    One moment expressed in each of the nine modes at once.

    Args:
        jd: Julian Day.

    Returns:
        A panorama: one reading per mana, in verse 1's order, and a
        `details` dict with the civil weekday, the solar month and day, the
        lunar tithi, the Fathers' hour, the manvantara and Brahma's day.
    """
    days = _unit_days()
    elapsed_days = ahargana(jd)
    sun, moon = _sun_moon(jd)
    sun_lon = sun.true_longitude
    t_num = int(((moon.true_longitude - sun_lon) % 360.0) / 12.0) + 1
    t_num = min(t_num, 30)
    paksha = "Shukla" if t_num <= 15 else "Krishna"
    _, masa = masa_from_sun_longitude(sun_lon)
    solar_day = int((sun_lon % 30.0)) + 1
    weekday = VARA_NAMES_EN[vara(jd)[0]]
    clock = pitrya_clock(jd)
    manv = manvantara_position(jd)
    brahma = brahma_day_elapsed(jd)
    years = kali_years_elapsed(jd)
    gods_fraction = years % 1.0

    counts = {k: elapsed_days / d for k, d in days.items()}
    counts["prajapatya"] = (YEARS_CREATION_TO_KALI + years) / MAHAYUGA / 71.0
    counts["brahma"] = brahma["fraction"]
    descriptions = {
        "brahma": f"{brahma['fraction'] * 100:.2f}% of Brahma's day elapsed",
        "daiva": f"{gods_fraction * 100:.1f}% through the gods' day",
        "pitrya": f"hour {clock.hour:.1f} of the Fathers' day ({clock.phase})",
        "prajapatya": f"manvantara {manv['number']}, year {manv['year_within']:,.0f}",
        "barhaspatya": f"{counts['barhaspatya']:.2f} Jovian years since the epoch",
        "saura": f"Kali year {kali_era_year(jd)}, {masa}, solar day {solar_day}",
        "savana": f"ahargana {elapsed_days:,.2f}, {weekday}",
        "candra": f"tithi {t_num} ({TITHI_NAMES[t_num - 1]}), {paksha} paksha",
        "naksatra": f"{counts['naksatra']:,.2f} sidereal days since the epoch",
    }
    # The solar mana counts elapsed solar years here, not solar days, so the
    # epoch reads zero in both the civil and the solar reading.
    counts["saura"] = years
    units = {m.key: m.unit for m in manas()}
    units["saura"] = "solar year (Kali years elapsed)"
    units["prajapatya"] = "manvantaras elapsed"
    units["brahma"] = "fraction of Brahma's day"
    readings = [
        ManaReading(m.key, counts[m.key], units[m.key], descriptions[m.key])
        for m in manas()
    ]
    return ReckoningPanorama(
        jd=jd, readings=readings,
        details={
            "ahargana": elapsed_days, "weekday": weekday,
            "kali_year": kali_era_year(jd), "solar_month": masa,
            "solar_day": solar_day, "tithi": t_num, "paksha": paksha,
            "gods_day_fraction": gods_fraction,
            "day_of_the_gods": day_of_the_gods(),
            "fathers_hour": clock.hour, "manvantara": manv,
            "brahma_day": brahma,
        },
    )


# ─────────────────────────────────────────────────────────────────
#  THE SOLAR YEAR — SS xiv.3-11
# ─────────────────────────────────────────────────────────────────

def _check_year(year: int) -> int:
    """Raise ValueError for a year the crossing solver cannot bracket."""
    if not MIN_YEAR <= int(year) <= MAX_YEAR:
        raise ValueError(f"Year {year} is outside {MIN_YEAR} to {MAX_YEAR}")
    return int(year)


def _sun_lon(jd: float) -> float:
    """The Sun's true sidereal longitude at a Julian Day."""
    return _sun_moon(jd)[0].true_longitude


def _next_crossing(after_jd: float, target_deg: float) -> float:
    """
    The first Julian Day after `after_jd` the Sun reaches `target_deg`.

    The Sun's mean rate gives an estimate; probing five days past it (more
    than the equation of the centre can move a crossing) lets the
    last-crossing solver find the instant.
    """
    delta = (target_deg - _sun_lon(after_jd)) % 360.0
    probe = after_jd + delta * SIDEREAL_YEAR_DAYS / 360.0 + 5.0
    return sun_crossing_jd(probe, target_deg % 360.0)


def _mesha_entry(year: int) -> float:
    """The Sun's entry into Aries that falls in a Gregorian year."""
    return sun_crossing_jd(julian_day(year, 12, 31.0), 0.0)


def _crossings(year: int) -> List[float]:
    """Julian Days of 14 successive sign entries from Mesha (30 degrees apart, 0..390)."""
    jds = [_mesha_entry(_check_year(year))]
    for k in range(1, 14):
        jds.append(_next_crossing(jds[-1], 30.0 * k))
    return jds


def punyakala_nadis(jd: float) -> float:
    """
    The time the Sun's disk takes to cross a sign boundary, in nadis (xiv.11).

    "Multiply the number of minutes in the sun's measure by sixty, and
    divide by his daily motion." Half of this is propitious before the
    entry and half after. The disk is the constant of
    `ch04.apparent_diameter_sun`, so only the daily motion varies.

    Args:
        jd: Julian Day, for the Sun's daily motion.

    Returns:
        The whole crossing time in nadis (about 33).
    """
    daily = ((_sun_lon(jd + 0.5) - _sun_lon(jd - 0.5) + 180.0) % 360.0 - 180.0) * 60.0
    return apparent_diameter_sun(jd) * 60.0 / daily


def _event(index: int, jd: float) -> SankrantiEvent:
    """A sankranti event for the entry into sign `index` at `jd`."""
    sign = index % 12
    kind = "visuvat" if sign in (0, 6) else "ayana" if sign in (3, 9) else "plain"
    total = punyakala_nadis(jd)
    ayan = ayanamsha(jd)
    return SankrantiEvent(
        sign_index=sign, sign=RASHIS[sign], masa=masa_from_sun_longitude(30.0 * sign)[1],
        longitude=30.0 * sign, jd=jd, kind=kind,
        tropical_longitude=(30.0 * sign + ayan) % 360.0, ayanamsha=ayan,
        punyakala_total_nadis=total, punyakala_each_side_nadis=total / 2.0,
    )


def sankrantis(year: int) -> List[SankrantiEvent]:
    """
    The twelve entries of the Sun into the signs, from the Aries entry in a year.

    Aries and Libra are the visuvats, Cancer and Capricorn the ayanas
    (v.7: "these four are well known"); each event carries its punyakala.

    Args:
        year: Gregorian year in which the Aries entry falls.

    Returns:
        Twelve events in order of time, Mesha first.

    Raises:
        ValueError: for a year outside MIN_YEAR to MAX_YEAR.
    """
    return [_event(i, jd) for i, jd in enumerate(_crossings(year)[:12])]


def ayanas(year: int) -> dict:
    """
    The two progresses of the Sun (xiv.9).

    Dakshinayana begins at the Cancer entry and uttarayana at the Capricorn
    entry. The text's sidereal reckoning and the tropical solstice differ by
    the ayanamsha, which each event reports.

    Returns:
        dict with `dakshinayana` and `uttarayana` events as dicts.
    """
    events = sankrantis(year)
    return {"dakshinayana": events[3].to_dict(), "uttarayana": events[9].to_dict()}


def visuvats(year: int) -> dict:
    """
    The two equinoxes (xiv.7-8): the Aries entry and the Libra entry.

    Returns:
        dict with `vernal` and `autumnal` events as dicts.
    """
    events = sankrantis(year)
    return {"vernal": events[0].to_dict(), "autumnal": events[6].to_dict()}


def shadasitimukhas(year: int) -> List[dict]:
    """
    The four shadasitimukhas and the remainder of Virgo (xiv.4-6).

    Four points 86 degrees apart from Libra 0 (180), at 266, 352, 78 and
    164, leaving 16 degrees at the end of Virgo: 4 x 86 + 16 = 360. The
    text's "eighty-six days" are eighty-six degrees; the Sun's true motion
    is not uniform, so each interval's `measured_days` runs from about
    85 to 89.5 (slowest near his apogee, in Gemini and Virgo). Burgess finds
    no explanation of what the division is for
    (note to v.6): the longitudes are text, their purpose is not.

    Args:
        year: Gregorian year whose Aries entry begins the solar year; the
            marks run from that year's Libra entry to the next.

    Returns:
        Four dicts for the shadasitimukhas, then one for the sixteen degrees
        of Virgo, each with longitude, arc_degrees, jd, measured_days.
    """
    start = _crossings(year)[6]
    marks, previous = [], start
    for longitude in SHADASITIMUKHA_LONGITUDES:
        jd = _next_crossing(previous, float(longitude))
        marks.append({
            "name": f"Shadasitimukha at {longitude} degrees", "longitude": longitude,
            "arc_degrees": SHADASITIMUKHA_ARC, "jd": jd, "measured_days": jd - previous,
            "source": "verse",
        })
        previous = jd
    libra = _next_crossing(previous, 180.0)
    marks.append({
        "name": "Last sixteen degrees of Virgo", "longitude": SHADASITIMUKHA_LONGITUDES[-1],
        "arc_degrees": VIRGO_REMAINDER, "jd": previous, "measured_days": libra - previous,
        "source": "verse",
        "use": load_catalog()["shadasitimukhas"]["remainder_use"],
    })
    return marks


def solar_year(year: int) -> SolarYearStructure:
    """
    The solar year as one structure (xiv.3-11).

    The sankrantis, ayanas, visuvats, shadasitimukhas and the six ritus of
    two signs each (v.10), counted from Capricorn with Shishira first.

    Args:
        year: Gregorian year in which the solar year's Aries entry falls.

    Returns:
        The structure. Ritus are listed from Grishma (Taurus) to the
        following Vasanta (Pisces), each with its start and end Julian Day.

    Raises:
        ValueError: for a year outside MIN_YEAR to MAX_YEAR.
    """
    jds = _crossings(year)
    events = [_event(i, jd) for i, jd in enumerate(jds[:12])]
    order = (2, 3, 4, 5, 0, 1)  # Grishma .. Shishira .. Vasanta, as RITU_NAMES indices
    ritus = []
    for n, ritu in enumerate(order):
        first = 1 + 2 * n
        ritus.append({
            "name": RITU_NAMES[ritu], "english": RITU_NAMES_EN[ritu],
            "start_sign": RASHIS[first % 12], "start_jd": jds[first], "end_jd": jds[first + 2],
            "days": jds[first + 2] - jds[first],
        })
    return SolarYearStructure(
        year=year, year_days=jds[12] - jds[0], sankrantis=events,
        ayanas={"dakshinayana": events[3].to_dict(), "uttarayana": events[9].to_dict()},
        visuvats={"vernal": events[0].to_dict(), "autumnal": events[6].to_dict()},
        shadasitimukhas=shadasitimukhas(year), ritus=ritus,
    )


# ─────────────────────────────────────────────────────────────────
#  THE FATHERS' CLOCK — SS xiv.14
# ─────────────────────────────────────────────────────────────────

def _elongation(jd: float) -> float:
    """Moon's longitude less the Sun's, in [0, 360)."""
    sun, moon = _sun_moon(jd)
    return (moon.true_longitude - sun.true_longitude) % 360.0


def _next_elongation_jd(jd: float, target_deg: float) -> float:
    """The first Julian Day after `jd` when the elongation reaches `target_deg`."""
    delta = (target_deg - _elongation(jd)) % 360.0
    estimate = jd + delta / 360.0 * SYNODIC_MONTH_DAYS

    def offset(t: float) -> float:
        wrapped = (_elongation(t) - target_deg) % 360.0
        return wrapped - 360.0 if wrapped >= 180.0 else wrapped

    for window in (2.5, 5.0, 8.0):
        lo, hi = estimate - window, estimate + window
        if offset(lo) < 0.0 <= offset(hi):
            return _bisect(offset, lo, hi)
    raise RuntimeError(f"No elongation crossing of {target_deg} bracketed near JD {estimate}")


def pitrya_clock(jd: float) -> PitryaClock:
    """
    Where a moment falls in the day of the Fathers (xiv.14).

    A lunar month is one day and night of the Fathers. "The end of the
    month is their midday, and the end of the half-month their midnight":
    the new moon is noon on their clock and the full moon midnight, so
    their hour is 12 + elongation / 15 (mod 24).

    Args:
        jd: Julian Day.

    Returns:
        The elapsed hour (0-24, noon is 12), ghati, fraction of the day since
        their midnight, the tithi and paksha, and the Julian Days of their
        next noon (new moon) and next midnight (full moon).
    """
    elong = _elongation(jd)
    hour = (12.0 + elong / 15.0) % 24.0
    tithi = min(int(elong / 12.0), 29) + 1
    if min(elong, 360.0 - elong) < 1.0:
        phase = "midday"
    elif abs(elong - 180.0) < 1.0:
        phase = "midnight"
    elif 0.0 < elong < 180.0:
        phase = "afternoon"
    else:
        phase = "forenoon"
    return PitryaClock(
        jd=jd, elongation=elong, hour=hour, ghati=hour / 24.0 * 60.0,
        day_fraction=hour / 24.0, tithi=tithi,
        paksha="Shukla" if tithi <= 15 else "Krishna", phase=phase,
        next_noon_jd=_next_elongation_jd(jd + 1e-6, 0.0),
        next_midnight_jd=_next_elongation_jd(jd + 1e-6, 180.0),
    )


# ─────────────────────────────────────────────────────────────────
#  MONTHS AND ASTERISMS — SS xiv.15-16
# ─────────────────────────────────────────────────────────────────

def month_asterisms() -> List[dict]:
    """
    The months Karttika to Asvina with their asterisms (xiv.15-16).

    "To the months Karttika etc. belong the asterisms Krttika etc., two by
    two; but three months, the last, the next to the last, and the fifth,
    have triple asterisms": 9 x 2 + 3 x 3 = 27. Each month holds its own
    namesake asterism, which is what confirms the reading.

    Returns:
        Twelve dicts: month, namesake, asterisms.
    """
    return [dict(row) for row in load_catalog()["month_asterisms"]["months"]]


def asterism_month(nakshatra: str) -> str:
    """
    The month an asterism belongs to.

    Raises:
        ValueError: for a name not in the table.
    """
    for row in month_asterisms():
        if str(nakshatra) in row["asterisms"]:
            return row["month"]
    raise ValueError(f"Unknown asterism {nakshatra!r}")


# ─────────────────────────────────────────────────────────────────
#  JUPITER'S YEARS — SS xiv.17
# ─────────────────────────────────────────────────────────────────

BARHASPATYA_METHODS = ("mean", "heliacal")


def _name_for_longitude(longitude: float) -> tuple:
    """(month index 0-11, month name, asterism name) for a sidereal longitude."""
    asterism = nakshatra_from_longitude(longitude)[1]
    for i, row in enumerate(month_asterisms()):
        if asterism in row["asterisms"]:
            return i, row["month"], asterism
    raise ValueError(f"Asterism {asterism!r} is not in the month table")


def _latest_jupiter_rising(jd: float):
    """The most recent heliacal rising of Jupiter at or before `jd` (scans Ch.9's visibility day by day)."""
    from suryasiddhanta.ch09_heliacal import next_heliacal

    latest = next_heliacal("Jupiter", jd - 420.0, "rising")
    while latest is not None:
        following = next_heliacal("Jupiter", latest.jd + 1.0, "rising")
        if following is None or following.jd > jd:
            break
        latest = following
    return latest


def barhaspatya_year(jd: float, method: str = "mean") -> BarhaspatyaYear:
    """
    The year of Jupiter's cycle a moment falls in (xiv.17).

    The years bear the names of the twelve months, taken from the
    asterism Jupiter stands in. Separate from `ch01.samvatsara`, the
    sixty-year cycle by i.55 (reported alongside).

    Both methods are marked source "commentary": the verse names the year
    from Jupiter's heliacal setting and rising, and gives no rule for
    either reckoning. `method="mean"` (fast) uses Jupiter's mean longitude,
    Burgess's reading of the twelve-year cycle as a sidereal revolution cut
    into twelve. `method="heliacal"` (slower) uses his place at his latest
    heliacal rising, found with Ch.9, which is closer to the verse's
    wording but inherits Ch.9's visibility thresholds. If the two methods name different years
    the note says so.

    Args:
        jd: Julian Day.
        method: "mean" or "heliacal".

    Returns:
        The BarhaspatyaYear.

    Raises:
        ValueError: for an unknown method, naming the valid ones.
    """
    if method not in BARHASPATYA_METHODS:
        raise ValueError(f"Unknown method {method!r}. Known: {', '.join(BARHASPATYA_METHODS)}")
    jovian_years = int(BHAGANA["Jupiter"] * ahargana(jd) / CIVIL_DAYS_PER_MAHAYUGA * 12.0)
    mean_lon = mean_longitude("Jupiter", jd)
    index, name, asterism = _name_for_longitude(mean_lon)
    longitude, note, source = mean_lon, "", "commentary"
    if method == "heliacal":
        rising = _latest_jupiter_rising(jd)
        if rising is None:
            note = "No heliacal rising found; the mean method's name is shown."
        else:
            year, month, day, frac = from_julian_day(rising.jd)
            longitude = compute("Jupiter", year, month, day + frac).true_longitude
            h_index, h_name, h_asterism = _name_for_longitude(longitude)
            if h_name != name:
                note = (f"The mean method names this year {name}; the heliacal method "
                        f"names it {h_name}.")
            index, name, asterism = h_index, h_name, h_asterism
    return BarhaspatyaYear(
        jd=jd, method=method, source=source, jovian_years_elapsed=jovian_years,
        name=name, name_index=index, asterism=asterism, longitude=longitude,
        sixty_year_name=samvatsara(jd)[1], note=note,
    )


def barhaspatya_cycle(start_year: int, n: int = 12) -> List[BarhaspatyaYear]:
    """
    Consecutive Jovian years, each a twelfth of Jupiter's revolution.

    Steps are exact Jovian years from 1 January of `start_year`, so each is
    30 degrees of mean longitude. A name spans two or three asterisms
    (27 to 40 degrees), so a step advances the name by 0, 1 or 2 places;
    twelve steps return to the starting asterism.

    Args:
        start_year: Gregorian year of the first step.
        n: How many years to list.

    Returns:
        n years, mean method.
    """
    start = julian_day(start_year, 1, 1.0)
    unit = _unit_days()["barhaspatya"]
    return [barhaspatya_year(start + i * unit) for i in range(n)]
