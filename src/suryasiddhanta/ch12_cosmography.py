"""
Chapter 12: Cosmography (Bhugoladhikara)
=======================================

"Cosmogony, Geography, and Dimensions of the Creation" — the chapter in
which Maya asks nine questions about the shape of the world and the Sun
answers them.

Chapters 1-11 compute quantities that vary with time. This one states
the fixed dimensions of the world and the rules that follow from them,
so almost everything here is a derivation from three stated numbers
rather than a search through Julian Days:

    the earth's diameter        1600 yojanas       (SS i.59, iv.1)
    the earth's circumference   1600 * sqrt(10)    (SS i.59)
    the Moon's orbit            324,000 yojanas    (SS xii.85)

Those, with the revolution counts of Ch.1, give every other figure the
chapter states. The load-bearing idea is SS xii.82's: **every planet
covers the same linear distance in a yuga**, so an orbit's size is
simply proportional to the time the body takes to go round it. Burgess
is blunt that this is false — only the Moon's orbit was arrived at by a
genuine calculation, and the rest are manufactured from it — but it is
what the text computes, and so it is what this module computes.

The descriptive half of the chapter, which cannot be derived from
anything, lives in `data/cosmography_catalog.json`: Maya's inquiries,
the creation sequence, the elements, the seven patalas, the reference
places, and the orbital order. Note that the Surya Siddhanta names seven
patalas below the earth but gives them no names, and has no table of
upper lokas at all; the familiar Puranic names belong to other works and
are deliberately absent.

Three of the functions here — `earth_circumference`,
`corrected_circumference` and the desantara pair — implement verses of
Chapter 1 (i.59-61) rather than Chapter 12. They belong to Chapter 1 by
number but `ch01_mean_motions` never implemented them, and verses 59-69
of this chapter cannot work without them.

Reference: SS Ch.12; Burgess (1860) pp.293-332
"""

from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Optional

from suryasiddhanta._types import CosmicPlace, OrbitInfo
from suryasiddhanta.ch01_mean_motions import (
    BHAGANA, CIVIL_DAYS_CREATION_TO_KALI, CIVIL_DAYS_PER_MAHAYUGA, KALPA,
    LANKA_MERIDIAN_LONGITUDE, LUNAR_MONTHS_PER_MAHAYUGA, KALI_EPOCH_JD, SIDEREAL_YEAR_DAYS, YEARS_CREATION_TO_KALI, from_julian_day,
    kali_years_elapsed, vara,
)
from suryasiddhanta.ch02_true_places import OBLIQUITY_DEGREES, compute
from suryasiddhanta.ch03_direction_place_time import declination
from suryasiddhanta.ch04_lunar_eclipses import (
    EARTH_DIAMETER_YOJANA, YOJANA_PER_ARCMIN,
)


# ─────────────────────────────────────────────────────────────────
#  THE TERRESTRIAL SPHERE — SS i.59-60
# ─────────────────────────────────────────────────────────────────

#: The Surya Siddhanta's value for pi, used only for the earth's
#: circumference (SS i.59). Elsewhere the treatise uses 3438-based sines,
#: which imply a closer 3.1416; the two are not reconciled in the text.
PI_ROOT_TEN = math.sqrt(10.0)

#: Days in a kalpa. The orbits of SS xii.82 are reckoned per Aeon, not
#: per Age, and using the Age would make every figure a thousand times
#: too small.
CIVIL_DAYS_PER_KALPA = CIVIL_DAYS_PER_MAHAYUGA * 1000

#: Mean synodic month, the day of the Fathers (SS xii.5, xii.74).
SYNODIC_MONTH_DAYS = CIVIL_DAYS_PER_MAHAYUGA / LUNAR_MONTHS_PER_MAHAYUGA


def earth_circumference() -> float:
    """
    The earth's greatest circumference in yojanas (SS i.59).

    "Twice eight hundred yojanas are the diameter of the earth: the
    square root of ten times the square of that is the earth's
    circumference" — that is, 1600 * sqrt(10) = 5059.644 yojanas.

    Returns:
        The equatorial circumference in yojanas.
    """
    return EARTH_DIAMETER_YOJANA * PI_ROOT_TEN


def corrected_circumference(latitude_deg: float) -> float:
    """
    The earth's circumference on the parallel of a given latitude
    (SS i.60), in yojanas.

    "This, multiplied by the sine of the co-latitude of any place and
    divided by radius, is the corrected circumference of the earth at
    that place" — the sine of the co-latitude over radius being simply
    the cosine of the latitude.

    Args:
        latitude_deg: Latitude of the place in degrees; the sign is
            immaterial, since a parallel north and its counterpart south
            are the same size.

    Returns:
        The circumference of that parallel in yojanas, zero at the poles.
    """
    return earth_circumference() * math.cos(math.radians(abs(latitude_deg)))


def desantara_yojanas(latitude_deg: float, longitude_deg: float,
                      reference_longitude_deg: float = LANKA_MERIDIAN_LONGITUDE,
                      ) -> float:
    """
    The difference of longitude in yojanas (SS i.60-61).

    The arc of the place's own parallel lying between it and the prime
    meridian — the meridian of Lanka, which passes through Ujjayini.

    Args:
        latitude_deg: Latitude of the place in degrees.
        longitude_deg: Longitude of the place in degrees, east positive.
        reference_longitude_deg: Longitude of the meridian measured from,
            east of Greenwich; by default the meridian of Lanka, which
            passes through Ujjayini (about 75.78 deg E, SS i.62).

    Returns:
        The distance in yojanas, always positive.
    """
    delta = abs(_wrap180(longitude_deg - reference_longitude_deg))
    return corrected_circumference(latitude_deg) * delta / 360.0


def desantara_correction(daily_motion_arcmin_value: float,
                         latitude_deg: float, longitude_deg: float,
                         reference_longitude_deg: float = LANKA_MERIDIAN_LONGITUDE,
                         ) -> float:
    """
    The longitude correction to a planet's mean place (SS i.61), in
    arcminutes.

    "As the circumference of the earth at the latitude of the point of
    observation is to the part of it intercepted between that point and
    the prime meridian, so is the whole daily motion of a planet to the
    correction." The quotient is subtracted east of the meridian and
    added west, because a place to the east reaches a given midnight
    before the meridian does.

    The latitude cancels — the corrected circumference appears in both
    the numerator and the denominator — so the result depends only on the
    difference of longitude. The latitude is nonetheless taken as an
    argument, because that cancellation is a property of the rule and not
    an assumption this function is entitled to make on the text's behalf.

    Args:
        daily_motion_arcmin_value: The planet's whole daily motion in
            arcminutes.
        latitude_deg: Latitude of the place in degrees.
        longitude_deg: Longitude of the place in degrees, east positive.
        reference_longitude_deg: Longitude of the prime meridian, east of
            Greenwich; by default the meridian of Lanka (SS i.62).

    Returns:
        Arcminutes to add to the mean place: negative east of the prime
        meridian, positive west, zero on it and at either pole, where
        every meridian meets and the correction is meaningless.
    """
    parallel = corrected_circumference(latitude_deg)
    if parallel <= 0.0:
        return 0.0
    yojanas = desantara_yojanas(
        latitude_deg, longitude_deg, reference_longitude_deg)
    magnitude = daily_motion_arcmin_value * yojanas / parallel
    east = _wrap180(longitude_deg - reference_longitude_deg) > 0.0
    return -magnitude if east else magnitude


# ─────────────────────────────────────────────────────────────────
#  ORBITS AND DISTANCES — SS xii.80-90
# ─────────────────────────────────────────────────────────────────

#: The Moon's orbit (SS xii.85). The one figure in the whole table that
#: Burgess allows was reached by a real calculation from real data.
MOON_ORBIT_YOJANAS = 324_000

#: Revolutions in a kalpa, from Ch.1's revolutions per mahayuga.
REVOLUTIONS_PER_KALPA: Dict[str, int] = {
    body: count * 1000 for body, count in BHAGANA.items()
}

#: The orbit of the ether — the sphere of the Brahma-egg, and the limit
#: of the Sun's rays (SS xii.81). The text states the result outright in
#: xii.90 as 18,712,080,864,000,000 yojanas.
ETHER_ORBIT_YOJANAS = REVOLUTIONS_PER_KALPA["Moon"] * MOON_ORBIT_YOJANAS


def _build_orbits() -> Dict[str, float]:
    """
    Build the table of orbits in yojanas (SS xii.82, 86, 80).

    Every revolving body's orbit is the ether orbit divided by its
    revolutions in an Aeon. Mercury and Venus are then given the Sun's
    orbit, because in this system they carry the Sun's mean longitude and
    only their sighroccas revolve on their own; and the sphere of the
    asterisms is the Sun's circuit times sixty.
    """
    orbits = {body: ETHER_ORBIT_YOJANAS / revolutions
              for body, revolutions in REVOLUTIONS_PER_KALPA.items()}
    orbits["Mercury"] = orbits["Sun"]
    orbits["Venus"] = orbits["Sun"]
    orbits["Asterisms"] = orbits["Sun"] * 60.0
    orbits["Ether"] = float(ETHER_ORBIT_YOJANAS)
    return orbits


ORBIT_YOJANAS: Dict[str, float] = _build_orbits()

#: The order in which all_orbits() reports, innermost first. The Ether is
#: left out: it is the bound of the Sun's rays, not a circuit any body
#: travels.
_ORBIT_REPORT_ORDER = (
    "Moon", "Mercury_sighrocca", "Venus_sighrocca", "Sun", "Mercury",
    "Venus", "Mars", "Moon_apogee", "Jupiter", "Moon_node", "Saturn",
    "Asterisms",
)


def orbit_yojanas(body: str) -> float:
    """
    The orbit (kakshya) of a body in yojanas (SS xii.82, 85-90).

    Args:
        body: "Moon", "Sun", "Mars", "Mercury", "Venus", "Jupiter",
            "Saturn", "Mercury_sighrocca", "Venus_sighrocca",
            "Moon_apogee", "Moon_node", "Asterisms" or "Ether".

    Returns:
        The circumference of that orbit in yojanas.

    Raises:
        KeyError: if the chapter gives no orbit for that body.
    """
    try:
        return ORBIT_YOJANAS[body]
    except KeyError:
        raise KeyError(
            f"No orbit for {body!r}. Known: {sorted(ORBIT_YOJANAS)}") from None


def daily_linear_motion() -> float:
    """
    The daily eastward motion in yojanas, the same for every planet
    (SS xii.82).

    "Divide this by the number of terrestrial days, and the result is the
    daily eastward motion of them all" — 11,858.717 yojanas. That the
    figure is the same for every planet is the assumption from which the
    whole table of orbits was manufactured.

    Returns:
        Yojanas travelled per civil day.
    """
    return ETHER_ORBIT_YOJANAS / CIVIL_DAYS_PER_KALPA


def daily_motion_arcmin(body: str) -> float:
    """
    A body's apparent daily motion in arcminutes (SS xii.83).

    "Multiply this number of yojanas of daily motion by the orbit of the
    moon, and divide by a planet's own orbit; the result is, when divided
    by fifteen, its daily motion in minutes." The fifteen is the same
    yojanas-per-arcminute that Ch.4 uses on the Moon's diameter.

    The rule is exact rather than approximate: the Moon's orbit over
    fifteen is 21,600, which is the number of arcminutes in a circle, so
    this reduces identically to Ch.1's mean daily motion.

    Args:
        body: Any body `orbit_yojanas` accepts.

    Returns:
        Arcminutes per day.

    Raises:
        KeyError: if the chapter gives no orbit for that body.
    """
    return (daily_linear_motion() * MOON_ORBIT_YOJANAS
            / orbit_yojanas(body) / YOJANA_PER_ARCMIN)


def orbit_diameter(body: str) -> float:
    """
    The diameter of a body's orbit in yojanas (SS xii.84).

    "Any orbit, multiplied by the earth's diameter and divided by the
    earth's circumference, gives the diameter of that orbit." Since the
    circumference is the diameter times the square root of ten, this is a
    division by sqrt(10) — the treatise's own value for pi, applied
    consistently with i.59.

    Args:
        body: Any body `orbit_yojanas` accepts.

    Returns:
        The orbit's diameter in yojanas.

    Raises:
        KeyError: if the chapter gives no orbit for that body.
    """
    return (orbit_yojanas(body) * EARTH_DIAMETER_YOJANA
            / earth_circumference())


def mean_distance(body: str) -> float:
    """
    A body's distance from the earth's surface in yojanas (SS xii.84).

    "And this, being diminished by the earth's diameter and halved, gives
    the distance of the planet" — the orbit's radius less the earth's.

    Args:
        body: Any body `orbit_yojanas` accepts.

    Returns:
        The distance in yojanas; about 50,428 for the Moon.

    Raises:
        KeyError: if the chapter gives no orbit for that body.
    """
    return (orbit_diameter(body) - EARTH_DIAMETER_YOJANA) / 2.0


def all_orbits() -> List[OrbitInfo]:
    """
    Every orbit the chapter gives, innermost first (SS xii.80-90).

    Each entry carries both the derived orbit and the figure the text
    states in v.85-89, so a caller can show how far the text's own
    rounding takes it from its own rule — never more than about 1.3
    yojanas, the worst case being Mercury's sighrocca.

    Returns:
        One OrbitInfo per revolving body, ordered by orbit size. The
        ether is excluded: it bounds the Sun's rays rather than carrying
        a body.
    """
    stated = {row["body"]: row for row in load_catalog()["stated_orbits"]}
    infos = []
    for body in _ORBIT_REPORT_ORDER:
        row = stated.get(body, {})
        infos.append(OrbitInfo(
            body=body,
            orbit_yojanas=orbit_yojanas(body),
            revolutions_per_kalpa=_revolutions_for_report(body),
            orbit_diameter_yojanas=orbit_diameter(body),
            distance_yojanas=mean_distance(body),
            daily_motion_arcmin=daily_motion_arcmin(body),
            stated_yojanas=row.get("yojanas"),
            verse=row.get("verse"),
        ))
    return infos


def _revolutions_for_report(body: str) -> int:
    """
    Revolutions in a kalpa for a body that may not have its own bhagana.

    Mercury and Venus take the Sun's, since they carry his mean
    longitude; the sphere of the asterisms takes the Sun's divided by
    sixty, which is what its orbit being sixty times the Sun's amounts to.
    """
    if body in REVOLUTIONS_PER_KALPA:
        return REVOLUTIONS_PER_KALPA[body]
    if body in ("Mercury", "Venus"):
        return REVOLUTIONS_PER_KALPA["Sun"]
    if body == "Asterisms":
        return REVOLUTIONS_PER_KALPA["Sun"] // 60
    raise KeyError(f"No revolution count for {body!r}")


def orbital_order() -> List[dict]:
    """
    The order of the spheres outward from the earth (SS xii.29-31).

    Clouds, the Possessors of Knowledge and the Perfected, then the seven
    planets from the Moon to Saturn, then the asterisms, the ether and
    the shell of the Brahma-egg. The planetary part of this order is what
    makes the regency of the weekdays come out as it does.

    Returns:
        The catalog's entries, each with a rank, a name and its verse.
    """
    return load_catalog()["orbital_order"]


# ─────────────────────────────────────────────────────────────────
#  LATITUDE AND THE VARYING DAY — SS xii.42-72
# ─────────────────────────────────────────────────────────────────

def yojanas_from_declination(declination_deg: float) -> float:
    """
    The distance from the equator answering to a declination (SS xii.59).

    "Multiply the earth's circumference by the sun's declination in
    degrees, and divide by the number of degrees in a circle."

    Args:
        declination_deg: A declination, or any arc, in degrees.

    Returns:
        The corresponding arc of the equator in yojanas.
    """
    return earth_circumference() * declination_deg / 360.0


def latitude_from_yojanas(yojanas: float) -> float:
    """
    The inverse of `yojanas_from_declination`: degrees from yojanas.

    Args:
        yojanas: A distance along a great circle of the earth.

    Returns:
        The arc in degrees.
    """
    return 360.0 * yojanas / earth_circumference()


def polar_day_limit() -> dict:
    """
    The parallel where the day first reaches sixty nadis (SS xii.60-61).

    "Subtract from a quarter of the earth's circumference the number of
    yojanas derived from the greatest declination: at the distance of the
    remaining number of yojanas there occurs once, at the end of the
    sun's half-revolution from solstice to solstice, a day of sixty
    nadis." With the treatise's obliquity of 24 degrees that parallel is
    at 90 - 24 = 66 degrees — the arctic circle of the text.

    Returns:
        A dict with the latitude in degrees, the distance from the
        equator and the distance from the pole, both in yojanas.
    """
    quarter = earth_circumference() / 4.0
    from_pole = yojanas_from_declination(OBLIQUITY_DEGREES)
    from_equator = quarter - from_pole
    return {
        "latitude": latitude_from_yojanas(from_equator),
        "yojanas_from_equator": from_equator,
        "yojanas_from_pole": from_pole,
        "obliquity": OBLIQUITY_DEGREES,
        "verse": "SS.12.60",
    }


def invisibility_limits() -> List[dict]:
    """
    The parallels beyond which the Sun is lost for whole signs
    (SS xii.63-66).

    The same subtraction as `polar_day_limit`, but with the declination
    reached at one sign and at two signs of longitude instead of the
    greatest declination. Beyond the two-sign parallel the Sun is not seen
    while he is in the two signs beginning with Sagittarius; beyond the
    one-sign parallel, while he is in the four beginning with Scorpio.

    Returns:
        Two dicts, the two-sign case first, each giving the longitude of
        the sign used, the declination it yields, the resulting latitude,
        the distance from the equator in yojanas, and how many signs of
        the Sun's course are lost there.
    """
    quarter = earth_circumference() / 4.0
    limits = []
    for sign_longitude, signs_invisible, verse in (
            (60.0, 2, "SS.12.63"), (30.0, 4, "SS.12.65")):
        dec = declination(sign_longitude)
        from_equator = quarter - yojanas_from_declination(dec)
        limits.append({
            "sign_longitude": sign_longitude,
            "declination": dec,
            "latitude": latitude_from_yojanas(from_equator),
            "yojanas_from_equator": from_equator,
            "signs_invisible": signs_invisible,
            "verse": verse,
        })
    return limits


def solar_overhead_band() -> dict:
    """
    The band across which the Sun passes directly overhead (SS xii.68).

    "The sun, during his northern and southern progresses, revolves
    directly over a fifteenth part of the earth's circumference, on the
    side both of the gods and of the demons." A fifteenth of a circle is
    24 degrees, which is exactly the obliquity: these are the tropics.

    Returns:
        A dict with the band's half-width in yojanas and in degrees.
    """
    return {
        "yojanas": earth_circumference() / 15.0,
        "degrees": 360.0 / 15.0,
        "verse": "SS.12.68",
    }


def pole_altitude(latitude_deg: float) -> float:
    """
    The elevation of the pole above the horizon (SS xii.44, 72).

    The text equates it with the latitude: at the cities of no latitude
    there is no elevation of the pole, both pole stars lying in the
    horizon, and at Meru the degrees of latitude are ninety.

    Args:
        latitude_deg: Latitude in degrees.

    Returns:
        The pole's altitude in degrees, always positive — at southern
        latitudes it is the southern pole star that is raised.
    """
    return abs(latitude_deg)


def sphere_aspect(latitude_deg: float) -> dict:
    """
    How the sphere of the asterisms turns at a given latitude
    (SS xii.42-44, 53-56, 72).

    The chapter distinguishes three situations. At no latitude the
    asterisms pass directly overhead, both pole stars lie in the horizon,
    and day and night are thirty nadis each. At Meru and Vadavamukha a
    pole is overhead and the asterisms circle the horizon — to the gods
    toward the right, to the demons toward the left. Everywhere between,
    the pole is raised by the latitude and day and night depart from
    thirty nadis by the ascensional difference of Ch.3.

    Args:
        latitude_deg: Latitude in degrees, north positive.

    Returns:
        A dict naming the situation ("right", "oblique" or "parallel"),
        the pole's altitude, the co-latitude, the hemisphere, and for the
        equator the thirty-nadi day the text states there. `day_ghatis`
        is None away from the equator, where the day depends on the Sun's
        declination as well and Ch.3 must be asked instead.
    """
    latitude = abs(latitude_deg)
    if latitude < 1e-9:
        kind, description = "right", (
            "No latitude (niraksha): the asterisms pass directly overhead, "
            "both pole stars lie in the horizon, and day and night are "
            "thirty nadis each.")
        day_ghatis: Optional[float] = 30.0
    elif abs(latitude - 90.0) < 1e-9:
        kind = "parallel"
        seat = "Meru, the gods" if latitude_deg > 0 else "Vadavamukha, the demons"
        description = (
            f"A pole ({seat}): the pole star is overhead, the asterisms "
            "circle the horizon, and the sun once risen is seen for half "
            "a year.")
        day_ghatis = None
    else:
        kind, day_ghatis = "oblique", None
        description = (
            "Toward Meru the pole rises and the circle of asterisms is "
            "depressed; day and night depart from thirty nadis by the "
            "ascensional difference.")
    return {
        "latitude": latitude_deg,
        "kind": kind,
        "pole_altitude": pole_altitude(latitude_deg),
        "colatitude": 90.0 - latitude,
        "hemisphere": ("gods" if latitude_deg > 0 else
                       "demons" if latitude_deg < 0 else "neither"),
        "day_ghatis": day_ghatis,
        "description": description,
        "verse": "SS.12.42-44, SS.12.53-56",
    }


def reference_places() -> List[CosmicPlace]:
    """
    The fixed places of the chapter's geography (SS xii.34-44, i.62).

    Meru and Vadavamukha at the poles, the four cities a quadrant apart
    upon the equator, and Ujjayini, which is what actually fixes the
    prime meridian the treatise names after Lanka.

    Returns:
        One CosmicPlace per place, in the catalog's order.
    """
    return [CosmicPlace(**row) for row in load_catalog()["reference_places"]]


def cities_clock(reference_place: str, hour: float = 12.0) -> Dict[str, float]:
    """
    The local hour at every reference place, given the hour at one
    (SS xii.70-71).

    "When passing overhead at Bhadracva, the sun is rising in Bharata; it
    is moreover, at that time, midnight in Ketumala, and sunset in Kuru."
    In the cities' own names: noon at Yamakoti is six at Lanka, midnight
    at Romaka and eighteen at Siddhapura.

    Args:
        reference_place: Name of the place whose hour is known — any of
            the four cities, or Ujjayini.
        hour: The local hour there, 0 to 24, noon by default.

    Returns:
        A dict of place name to local hour in [0, 24).

    Raises:
        ValueError: if the place is unknown, or is Meru or Vadavamukha,
            where every meridian meets and there is no local hour.
    """
    places = {place.name: place for place in reference_places()}
    anchor = places.get(reference_place)
    if anchor is None:
        raise ValueError(
            f"Unknown place {reference_place!r}. "
            f"Known: {sorted(places)}")
    if anchor.is_pole:
        raise ValueError(
            f"{reference_place} is a pole: every meridian meets there, so "
            "it has no local hour to reckon from.")
    return {
        place.name: (hour + (place.longitude - anchor.longitude) / 15.0) % 24.0
        for place in places.values() if not place.is_pole
    }


# ─────────────────────────────────────────────────────────────────
#  TIME AND ITS REGENTS — SS xii.74, 78-79
# ─────────────────────────────────────────────────────────────────

def day_of_the_gods() -> float:
    """
    The day of the gods and of the demons, in civil days (SS xii.67, 74).

    At Meru the Sun, once risen, is seen through his half-revolution
    beginning with Aries, and at Vadavamukha through the half beginning
    with Libra. Their day and night together are therefore a year.

    Returns:
        The sidereal year in days.
    """
    return SIDEREAL_YEAR_DAYS


def day_of_the_manes() -> float:
    """
    The day of the Fathers, in civil days (SS xii.5, 74).

    The Fathers have their station in the moon, each portion of whose
    surface sees the Sun for half a lunar month; their day and night
    together are a synodic month.

    Returns:
        The mean synodic month in days.
    """
    return SYNODIC_MONTH_DAYS


def day_of_brahma() -> float:
    """
    The day of Brahma, in civil days.

    An Aeon of 4,320,000,000 years, the scale on which Ch.1 reckons the
    revolutions this chapter's orbits are built from.

    Returns:
        The kalpa expressed in days.
    """
    return KALPA * SIDEREAL_YEAR_DAYS


def brahma_day_elapsed(jd: float) -> dict:
    """
    How far into Brahma's present day a given moment falls.

    The Surya Siddhanta places the creation 1,955,880,000 years before
    the Kali epoch — a little under half an Aeon — so every historical
    date lands just past the middle of the current day of Brahma.

    Args:
        jd: Julian Day.

    Returns:
        A dict with the years elapsed since the creation, the years
        remaining, and the elapsed fraction of the Aeon.
    """
    years = YEARS_CREATION_TO_KALI + kali_years_elapsed(jd)
    return {
        "years_elapsed": years,
        "years_remaining": KALPA - years,
        "fraction": years / KALPA,
        "kalpa_years": KALPA,
    }


#: The planets in the downward order of SS xii.31 — outermost first.
#: Every regent rule of xii.78-79 counts along this list.
REGENT_ORDER: List[str] = [
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon",
]

#: Lords of the seven weekdays, indexed as ch01's `vara`: 0 is Sunday.
WEEKDAY_LORDS: List[str] = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
]

#: Horas in a day, a month and a year, from which the three regent rules
#: of SS xii.78-79 follow: 24 % 7 = 3 is the text's "fourth counting
#: downward from Saturn"; 720 % 7 = 6 is a step of minus one, the text's
#: "reckoning upward from the moon"; 8640 % 7 = 2 is its "third".
HORAS_PER_DAY = 24
HORAS_PER_MONTH = HORAS_PER_DAY * 30
HORAS_PER_YEAR = HORAS_PER_DAY * 360


def regent_of_day(jd: float) -> str:
    """
    The planet ruling a given day (SS xii.78).

    "Counting downward from Saturn, the fourth successively is regent of
    the day." Burgess's note to xii.79 explains why: the hora is the
    primitive, and a day's lord is the lord of its first hora. Twenty-four
    horas advance the cycle by three places, which counted inclusively is
    the fourth.

    Args:
        jd: Julian Day.

    Returns:
        The ruling planet's name.
    """
    index, _ = vara(jd)
    return WEEKDAY_LORDS[index]


def hora_lord(jd: float, hora: int = 0) -> str:
    """
    The planet ruling a given hora (SS xii.79).

    "The regents of the hours (hora) occur in downward order from
    Saturn." The hora is a twenty-fourth of the day, counted from
    sunrise; the first belongs to the lord of the day, and each following
    one to the next planet inward along `REGENT_ORDER`.

    The function does not locate sunrise: it takes the day that ``jd``
    falls in by ``ch01.vara``, whose days run midnight to midnight in
    Ujjain mean time, and counts ``hora`` from that day's first hour.

    Args:
        jd: Library Julian Day (Ujjain mean time) of the day in question.
        hora: Index of the hora from sunrise, zero-based. Values of 24 and
            above run into following days, which is the mechanism by which
            the day lords succeed one another.

    Returns:
        The ruling planet's name.
    """
    start = REGENT_ORDER.index(regent_of_day(jd))
    return REGENT_ORDER[(start + hora) % len(REGENT_ORDER)]


def _regent_of_period(jd: float, days: int) -> str:
    """
    The lord of the fixed civil period of `days` days containing a moment.

    Burgess (note to i.51-52, repeated at xii.78-79): the month and year
    regents rule "no actual months and years, but periods of thirty and
    three hundred and sixty days, following one another in uniform
    succession", counted from the end of creation, and each period's lord
    is the lord of its first day. The count must start at creation, not
    at the Kali epoch: `CIVIL_DAYS_CREATION_TO_KALI` leaves 17 on division
    by 30 and 347 on division by 360, so a Kali-anchored count would put
    every period boundary in the wrong place.

    Args:
        jd: Julian Day.
        days: Length of the period in civil days (30 or 360).

    Returns:
        The ruling planet's name.
    """
    days_since_creation = CIVIL_DAYS_CREATION_TO_KALI + math.floor(jd - KALI_EPOCH_JD)
    first_day = days_since_creation - days_since_creation % days
    return regent_of_day(KALI_EPOCH_JD + (first_day - CIVIL_DAYS_CREATION_TO_KALI))


def regent_of_month(jd: float) -> str:
    """
    The planet ruling the 30-day civil regent month containing a moment
    (SS xii.79).

    "Reckoning upward from the moon are found, in succession, the regents
    of the months." A month is 720 horas and 720 leaves 6 on division by
    seven, a step of minus one along `REGENT_ORDER` — which is upward.
    The months are fixed 30-day periods counted from creation, not true
    solar months; see `_regent_of_period`.

    Args:
        jd: Julian Day.

    Returns:
        The ruling planet's name.
    """
    return _regent_of_period(jd, 30)


def regent_of_year(jd: float) -> str:
    """
    The planet ruling the 360-day civil regent year containing a moment
    (SS xii.78).

    "The third, in like manner, is declared to be the regent of the
    year." A year is 8640 horas and 8640 leaves 2 on division by seven,
    which counted inclusively is the third. The years are fixed 360-day
    periods counted from creation, not sidereal solar years; see
    `_regent_of_period`.

    Args:
        jd: Julian Day.

    Returns:
        The ruling planet's name.
    """
    return _regent_of_period(jd, 360)


def solar_year_start(jd: float) -> float:
    """
    The Julian Day on which the current sidereal solar year began.

    The moment the Sun's true longitude last crossed zero — his entry
    into Aries. This astronomical year differs from the fixed 360-day
    period used for `regent_of_year`.

    Args:
        jd: Julian Day.

    Returns:
        The Julian Day of that crossing.
    """
    return _last_crossing(jd, 0.0)


def solar_month_start(jd: float) -> float:
    """
    The Julian Day on which the current sidereal solar month began.

    The Sun's last entry into a sign — the sankranti. This astronomical
    month differs from the fixed 30-day period used for `regent_of_month`.

    Args:
        jd: Julian Day.

    Returns:
        The Julian Day of that crossing.
    """
    return _last_crossing(jd, math.floor(_sun_longitude(jd) / 30.0) * 30.0)


# ─────────────────────────────────────────────────────────────────
#  THE CATALOG
# ─────────────────────────────────────────────────────────────────

_CATALOG: Optional[dict] = None


def load_catalog() -> dict:
    """
    Load the cosmography catalog from the bundled JSON file.

    Holds what the chapter states but no rule can derive: Maya's nine
    inquiries, the creation sequence, the elements and the planets said
    to arise from them, the seven patalas, the reference places, the
    orbital order, the orbits as the text states them, the regent rules
    and the day-and-night table of the orders of beings. Every entry
    cites its verse in the corpus's `SS.<chapter>.<verse>` form.

    Cached after the first call.

    Returns:
        The parsed catalog.
    """
    global _CATALOG
    if _CATALOG is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        path = os.path.join(data_dir, "cosmography_catalog.json")
        with open(path, "r", encoding="utf-8") as handle:
            _CATALOG = json.load(handle)
    return _CATALOG


# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────

def _wrap180(degrees: float) -> float:
    """Wrap an angle into [-180, 180), so it crosses zero cleanly."""
    wrapped = degrees % 360.0
    return wrapped - 360.0 if wrapped >= 180.0 else wrapped


def _sun_longitude(jd: float) -> float:
    """The Sun's true sidereal longitude at a Julian Day, in degrees."""
    year, month, day, frac = from_julian_day(jd)
    return compute("Sun", year, month, day + frac).true_longitude


def sun_crossing_jd(jd: float, target_deg: float) -> float:
    """
    The Julian Day the Sun's longitude last crossed a given degree.

    Public because Chapter 14's sankrantis and shadasitimukhas are all
    longitude crossings of exactly this kind.

    The Sun's mean rate gives a first estimate of how long ago the
    crossing was; the true instant is then bisected inside a window about
    it, widened if the equation of the centre has carried the crossing
    outside. Ten days is already several times the largest displacement
    the SS equation can produce.

    Args:
        jd: Julian Day to search back from.
        target_deg: The longitude crossed, in degrees.

    Returns:
        The Julian Day of the crossing.

    Raises:
        RuntimeError: if no crossing is bracketed, which would mean the
            Sun's longitude is not behaving monotonically over a month.
    """
    elapsed = (_sun_longitude(jd) - target_deg) % 360.0
    estimate = jd - elapsed * SIDEREAL_YEAR_DAYS / 360.0

    offset = lambda t: _wrap180(_sun_longitude(t) - target_deg)  # noqa: E731
    for window in (10.0, 20.0, 40.0):
        lo, hi = estimate - window, estimate + window
        if offset(lo) < 0.0 <= offset(hi):
            return _bisect(offset, lo, hi)
    raise RuntimeError(
        f"No crossing of {target_deg} deg bracketed near JD {estimate}")


#: Kept so existing callers within this module keep working.
_last_crossing = sun_crossing_jd


def _bisect(fn, lo: float, hi: float, steps: int = 40) -> float:
    """Bisect a sign-changing function of Julian Day between two bounds."""
    f_lo = fn(lo)
    for _ in range(steps):
        mid = (lo + hi) / 2.0
        f_mid = fn(mid)
        if (f_lo < 0.0) == (f_mid < 0.0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return (lo + hi) / 2.0
