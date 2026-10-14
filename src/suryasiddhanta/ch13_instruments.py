"""
Chapter 13: Of the Armillary Sphere and other Instruments (Jyotishopanishad)
===========================================================================

The "lection of the astronomical Upanishad": the teacher builds for the
pupil a sphere of hoops about a wooden earth, sets it turning, and then
names the instruments by which time is measured.

The chapter has three parts, and this module has one cluster for each:

- **The armillary sphere** (v.1-16). A Meru staff through a wooden globe;
  two supporting hoops (the colures); diurnal hoops for the Sun at the
  sign boundaries and for the stars; the equator; the ecliptic, laid off
  by chords of thirty degrees; the three lagnas, the day-measure and the
  ascensional-difference sine; the horizon, with the half below it cased
  in cloth. `armillary_sphere` assembles all of it for a place and moment.
- **The clepsydra** (v.23). A copper bowl with a hole in the bottom, set in
  water, sinks sixty times in a day and night — one ghati a sinking.
- **Time from instruments** (v.20-24). The man-instrument (a gnomon) is
  the treatise's own; the staff, wheel and arc are explained only in the
  commentary Burgess summarizes from Shripati's Siddhanta-Shekhara
  (Bhaskara set it aside). Every result says which (`source` = "verse" or "commentary").

Geometry is in the equatorial frame: z along the Meru axis toward the
north pole, x toward the vernal equinox, y toward right ascension 90 deg.
Quantities the text names as sines — the day-radius, carajya, kujya,
antya, agra and the chord of thirty — use the R = 3438 table of Ch.2;
angles (hour angle, declination) use exact trigonometry, as Ch.3 does.

Stellar hoops follow the text's polar coordinates. SS ii.58 finds a true
declination by adding the latitude to the declination of the ecliptic
point, and for a latitude measured along the circle of declination (as
the Surya Siddhanta's are) that rule is exact. `ch08_stars.star_position`
instead treats the catalog latitude as ecliptic, which differs by degrees
for far-northern Abhijit; Chapter 13 follows the text and ch08 is left
as it is.

The seven fixed stars of v.8-9 that are not junction stars — Agastya,
Mrgavyadha, Agni, Brahmahrdaya, Prajapati, Apamvatsa, Apas — come from
viii.10-12 and 20-21, whose Burgess text survives in the corpus under the
misaligned record SS.8.24. They live in `data/instruments_catalog.json`.

Reference: SS Ch.13; Burgess (1860) pp.297-310
"""

from __future__ import annotations

import dataclasses
import json
import math
import os
from typing import Callable, Dict, List, Optional, Tuple

from suryasiddhanta._types import (
    ArmillarySphere, ClepsydraReading, InstrumentTime, SphereHoop, SpherePoint,
)
from suryasiddhanta.ch01_mean_motions import RASHIS, from_julian_day
from suryasiddhanta.ch02_true_places import (
    OBLIQUITY_DEGREES, R_SINE, ayanamsha, compute, jya, koti, normalize,
)
from suryasiddhanta.ch03_direction_place_time import (
    declination, local_sidereal_time, right_ascension,
    solar_altitude_from_shadow, sunrise_hour_angle,
)
from suryasiddhanta.ch08_stars import ABHIJIT, NAKSHATRA_DATA

Vector = Tuple[float, float, float]


# ─────────────────────────────────────────────────────────────────
#  THE CATALOG
# ─────────────────────────────────────────────────────────────────

_CATALOG: Optional[dict] = None


def load_catalog() -> dict:
    """
    Load the instruments catalog from the bundled JSON file.

    Holds what the chapter states but no rule computes: the parts of the
    sphere, the definitions of the points on it, the seven fixed stars and
    the Seven Sages, the eleven instruments, and the clepsydra's vessel as
    the commentary specifies it. Every entry cites its verse in the
    corpus's `SS.<chapter>.<verse>` form.

    Cached after the first call.

    Returns:
        The parsed catalog.
    """
    global _CATALOG
    if _CATALOG is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        path = os.path.join(data_dir, "instruments_catalog.json")
        with open(path, "r", encoding="utf-8") as handle:
            _CATALOG = json.load(handle)
    return _CATALOG


def fixed_star(name: str) -> dict:
    """
    Look up one of the seven fixed stars of SS viii.10-12, 20-21 by name.

    Args:
        name: Star name, case-insensitive (e.g. "Agastya").

    Returns:
        The catalog entry, with polar longitude and latitude in degrees
        (latitude negative south).

    Raises:
        KeyError: if the name is not one of the seven.
    """
    for star in load_catalog()["fixed_stars"]:
        if star["name"].lower() == str(name).lower():
            return star
    known = ", ".join(s["name"] for s in load_catalog()["fixed_stars"])
    raise KeyError(f"Unknown fixed star {name!r}. Known: {known}")


def get_instrument(key: str) -> dict:
    """
    Look up one of the instruments of SS xiii.3-24 by key.

    Args:
        key: Catalog key, case-insensitive (e.g. "ghati", "yashti").

    Returns:
        The catalog entry.

    Raises:
        KeyError: if no instrument has that key.
    """
    for instrument in load_catalog()["instruments"]:
        if instrument["key"] == str(key).lower():
            return instrument
    known = ", ".join(i["key"] for i in load_catalog()["instruments"])
    raise KeyError(f"Unknown instrument {key!r}. Known: {known}")


# ─────────────────────────────────────────────────────────────────
#  SHARED HELPERS
# ─────────────────────────────────────────────────────────────────

_ENGLISH_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _check_latitude(latitude_deg: float) -> float:
    """
    Reject a latitude at or beyond a pole.

    The sphere's sines and the time-finding rules all divide by
    cos(latitude); at the poles the horizon is the equator and the rules
    of Ch.3 have no meaning.

    Raises:
        ValueError: if |latitude| >= 90.
    """
    lat = float(latitude_deg)
    if not -90.0 < lat < 90.0:
        raise ValueError(f"Latitude must lie strictly between -90 and 90, got {lat}")
    return lat


def equatorial_vector(ra_deg: float, dec_deg: float) -> Vector:
    """
    Unit vector of a point on the sphere, in the equatorial frame.

    Args:
        ra_deg: Right ascension (degrees).
        dec_deg: Declination (degrees).

    Returns:
        (x, y, z) with x toward the vernal equinox and z toward the north
        pole.
    """
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    return (math.cos(dec) * math.cos(ra),
            math.cos(dec) * math.sin(ra),
            math.sin(dec))


def _sun(jd: float):
    """The Sun's PlanetPosition at a Julian Day (true place, SS Ch.2)."""
    year, month, day, frac = from_julian_day(jd)
    return compute("Sun", year, month, day + frac)


def sun_declination(jd: float) -> float:
    """
    The Sun's declination at a Julian Day, north positive (degrees).

    Declination is reckoned from the tropical longitude — the sidereal
    true place with the ayanamsha added (SS iii.9-12) — as
    `ch11_pata.sun_declination` does.
    """
    return declination(_sun(jd).tropical_longitude)


def _ecliptic_point(key: str, name: str, tropical_lon: float,
                    sidereal_lon: float, verse: str,
                    note: str = "") -> SpherePoint:
    """Build a SpherePoint for an ecliptic longitude (zero latitude)."""
    ra = right_ascension(tropical_lon)
    dec = declination(tropical_lon)
    return SpherePoint(
        key=key, name=name,
        tropical_longitude=normalize(tropical_lon),
        sidereal_longitude=normalize(sidereal_lon),
        right_ascension=ra, declination=dec,
        vector=equatorial_vector(ra, dec),
        verse=verse, note=note,
    )


# ─────────────────────────────────────────────────────────────────
#  THE HOOPS OF THE SPHERE — SS xiii.4-16
# ─────────────────────────────────────────────────────────────────

#: Sun's longitudes at the ends of Aries, Taurus and Gemini, whose
#: diurnal hoops serve also, inversely, for Cancer, Leo and Virgo (xiii.7).
SOLAR_HOOP_LONGITUDES: Tuple[float, ...] = (30.0, 60.0, 90.0)


def great_hoops() -> List[SphereHoop]:
    """
    The four great circles of the sphere (SS xiii.4, 9-12).

    The two supporting hoops fastened to the axis at right angles — the
    equinoctial colure through the equinoxes and poles, the solstitial
    colure through the solstices and poles — then the equator "in the
    midst of all", then the ecliptic running obliquely from solstice to
    solstice at the obliquity of 24 degrees. The meridian is not among
    them: Burgess notes the text has no name for it and does not put it
    on the instrument.

    Returns:
        Hoops keyed equinoctial_colure, solstitial_colure, equator, ecliptic.
    """
    eps = math.radians(OBLIQUITY_DEGREES)
    return [
        SphereHoop(
            key="equinoctial_colure", name="Equinoctial colure",
            kind="great", group="great_circles", normal=(0.0, 1.0, 0.0),
            offset=0.0, declination=None, day_radius=None, verse="SS.13.4",
            note="Supporting hoop through the equinoxes and the poles.",
        ),
        SphereHoop(
            key="solstitial_colure", name="Solstitial colure",
            kind="great", group="great_circles", normal=(1.0, 0.0, 0.0),
            offset=0.0, declination=None, day_radius=None, verse="SS.13.4",
            note="Supporting hoop through the solstices and the poles.",
        ),
        SphereHoop(
            key="equator", name="Equator (vaishuvati)",
            kind="great", group="great_circles", normal=(0.0, 0.0, 1.0),
            offset=0.0, declination=0.0, day_radius=float(R_SINE),
            verse="SS.13.9",
        ),
        SphereHoop(
            key="ecliptic", name="Ecliptic (krantivrtta)",
            kind="great", group="great_circles",
            normal=(0.0, -math.sin(eps), math.cos(eps)),
            offset=0.0, declination=None, day_radius=None, verse="SS.13.11",
            note="Laid through the sign divisions fixed by chords of 30 deg.",
        ),
    ]


def horizon_hoop(latitude_deg: float, lst_deg: float) -> SphereHoop:
    """
    The horizon hoop, set midway of the sphere about the observer (xiii.15-16).

    "Having turned upward one's own place, the circle of the horizon is
    midway of the sphere": its pole is the zenith, which in the equatorial
    frame lies at declination = latitude and right ascension = local
    sidereal time. The half below is cased in cloth (v.16).

    Args:
        latitude_deg: Observer latitude (degrees).
        lst_deg: Local sidereal time (degrees).

    Returns:
        The horizon hoop, flagged `cased_below`.
    """
    lat = _check_latitude(latitude_deg)
    return SphereHoop(
        key="horizon", name="Horizon (kshitija)", kind="horizon",
        group="horizon", normal=equatorial_vector(lst_deg, lat), offset=0.0,
        declination=None, day_radius=None, verse="SS.13.15",
        note="The part below is covered with cloth (SS.13.16).",
        cased_below=True,
    )


def solar_diurnal_hoops() -> List[SphereHoop]:
    """
    The six diurnal hoops of the Sun at the sign boundaries (SS xiii.5-8).

    Three north of the equator for the Sun at the ends of Aries, Taurus
    and Gemini — serving also for the beginnings of Virgo, Leo and Cancer,
    which share their declinations — and three south for Libra, Scorpio
    and Sagittarius, serving inversely for Pisces, Aquarius and Capricorn.
    Each is sized by its day-radius (dyujya) and set at the Sun's
    declination on the graduated supporting hoops.

    Returns:
        Northern hoops (outward from the equator), then southern.
    """
    hoops: List[SphereHoop] = []
    for hemisphere, base in (("north", 0.0), ("south", 180.0)):
        for lon in SOLAR_HOOP_LONGITUDES:
            start = base + lon
            end_sign = _ENGLISH_SIGNS[int(start // 30) - 1]
            # The longitude sharing this declination: 180 - start.
            mirror = _ENGLISH_SIGNS[int(((180.0 - start) % 360.0) // 30) % 12]
            dec = declination(start)
            hoops.append(SphereHoop(
                key=f"sun_{hemisphere}_{int(lon)}",
                name=f"Sun: end of {end_sign} / beginning of {mirror}",
                kind="solar_diurnal", group="solar",
                normal=(0.0, 0.0, 1.0), offset=math.sin(math.radians(dec)),
                declination=dec, day_radius=koti(dec), verse="SS.13.7",
                note=f"Sun's longitude {start:.0f} deg; declination {dec:.2f} deg.",
            ))
    return hoops


def star_polar_declination(polar_lon: float, polar_lat: float, jd: float) -> float:
    """
    Declination of a star from the text's polar coordinates (SS ii.58).

    The polar longitude names the ecliptic point on the star's circle of
    declination, and the polar latitude is measured along that same
    circle, so the star's declination is simply the declination of that
    ecliptic point (reckoned tropically, with the ayanamsha) plus the
    latitude — "increased when of like direction, diminished when of
    different direction".

    Args:
        polar_lon: Sidereal polar longitude (dhruvaka), degrees.
        polar_lat: Polar latitude (vikshepa), degrees, north positive.
        jd: Julian Day, for the ayanamsha.

    Returns:
        Declination in degrees, clamped to [-90, 90].
    """
    dec = declination(polar_lon + ayanamsha(jd)) + polar_lat
    return max(-90.0, min(90.0, dec))


def _star_hoop(key: str, name: str, group: str, polar_lon: float,
               polar_lat: float, jd: float, verse: str, note: str) -> SphereHoop:
    """Build the diurnal hoop for a star given in polar coordinates."""
    dec = star_polar_declination(polar_lon, polar_lat, jd)
    ra = right_ascension(polar_lon + ayanamsha(jd))
    return SphereHoop(
        key=key, name=name, kind="star_diurnal", group=group,
        normal=(0.0, 0.0, 1.0), offset=math.sin(math.radians(dec)),
        declination=dec, day_radius=koti(dec), verse=verse, note=note,
        marker=equatorial_vector(ra, dec),
    )


def star_diurnal_hoops(jd: float) -> List[SphereHoop]:
    """
    Diurnal hoops of the stars (SS xiii.8-9).

    The junction-stars of the twenty-seven asterisms and Abhijit, from
    `ch08_stars`, and the seven other fixed stars of viii.10-12 and 20-21
    from the catalog. The Seven Sages, also named in v.9, have no stated
    positions and so no hoop.

    Args:
        jd: Julian Day, for the ayanamsha that places each star's
            circle of declination.

    Returns:
        28 junction-star hoops, then 7 fixed-star hoops.
    """
    hoops = [
        _star_hoop(
            key="star_" + n.name.lower().replace(" ", "_"), name=n.name,
            group="junction_stars", polar_lon=n.longitude,
            polar_lat=n.latitude, jd=jd, verse="SS.13.8",
            note=f"Junction star {n.star}; polar {n.longitude} deg, "
                 f"{n.latitude:+} deg.",
        )
        for n in list(NAKSHATRA_DATA) + [ABHIJIT]
    ]
    for star in load_catalog()["fixed_stars"]:
        hoops.append(_star_hoop(
            key="star_" + star["name"].lower(), name=star["name"],
            group="fixed_stars", polar_lon=star["polar_longitude"],
            polar_lat=star["polar_latitude"], jd=jd, verse=star["hoop_verse"],
            note=f"{star['identification']}; polar {star['polar_longitude']} "
                 f"deg, {star['polar_latitude']:+} deg ({star['verse']}).",
        ))
    return hoops


# ─────────────────────────────────────────────────────────────────
#  POINTS ON THE SPHERE — SS xiii.10-15
# ─────────────────────────────────────────────────────────────────

def chord_of_thirty() -> float:
    """
    Chord of 30 degrees, in the text's R = 3438 units (SS xiii.11).

    Burgess reads tiryagjya in v.11 as "oblique chord": the chord of a
    sign, laid off obliquely from the equinox to each successive solar
    hoop, fixes the division points of the twelve signs through which the
    ecliptic hoop is passed. chord(30) = 2 * jya(15).
    """
    return 2.0 * jya(15.0)


def ecliptic_sign_points() -> List[SpherePoint]:
    """
    The twelve sign-division points on the ecliptic hoop (SS xiii.11).

    On the instrument the signs are counted from the equinox, so the
    longitudes here are those of the sphere itself; no ayanamsha applies.

    Returns:
        Points at 0, 30, ... 330 degrees, keyed by the Sanskrit sign name.
    """
    return [
        _ecliptic_point(
            key=RASHIS[i].lower(), name=f"{RASHIS[i]} ({_ENGLISH_SIGNS[i]})",
            tropical_lon=i * 30.0, sidereal_lon=i * 30.0, verse="SS.13.11",
        )
        for i in range(12)
    ]


def cardinal_points() -> List[SpherePoint]:
    """
    The equinoxes and solstices (SS xiii.10).

    The equinoxes sit where the equator crosses the equinoctial colure; the
    solstices on the solstitial colure, 24 degrees above and below the
    equator.
    """
    names = (("vernal_equinox", "Vernal equinox", 0.0),
             ("summer_solstice", "Summer solstice", 90.0),
             ("autumnal_equinox", "Autumnal equinox", 180.0),
             ("winter_solstice", "Winter solstice", 270.0))
    return [_ecliptic_point(key, name, lon, lon, "SS.13.10")
            for key, name, lon in names]


def meridian_ecliptic_point(lst_deg: float) -> float:
    """
    Meridian ecliptic-point (madhya-lagna) for a local sidereal time (xiii.14).

    The ecliptic point at mid-heaven has right ascension equal to the
    local sidereal time. Inverting tan(RA) = tan(lon) * cos(obliquity):

        lon = atan2(sin RA, cos RA * cos obliquity)

    which keeps the quadrant, since cos(lon) and cos(RA) share a sign.

    Args:
        lst_deg: Local sidereal time (degrees).

    Returns:
        Tropical longitude of the meridian ecliptic-point, [0, 360).
    """
    ra = math.radians(lst_deg)
    eps = math.radians(OBLIQUITY_DEGREES)
    return normalize(math.degrees(math.atan2(math.sin(ra),
                                             math.cos(ra) * math.cos(eps))))


def orient_ecliptic_point(lst_deg: float, latitude_deg: float) -> float:
    """
    Orient ecliptic-point (lagna) for a local sidereal time and latitude (xiii.13).

    The point of the ecliptic on the eastern horizon:

        lon = atan2(cos LST, -(sin LST cos(obliquity) + tan(lat) sin(obliquity)))

    This is the exact form of the rising-times reckoning of SS iii.46-48.
    It is computed here rather than taken from `ch03.lagna`, whose
    accumulation of rising times starts Aries rising at sidereal time
    zero — where in fact the Cancer region is rising — and so does not put
    its lagna on the horizon of the sphere this module builds.

    Args:
        lst_deg: Local sidereal time (degrees).
        latitude_deg: Observer latitude (degrees).

    Returns:
        Tropical longitude of the rising ecliptic point, [0, 360).
    """
    lat = _check_latitude(latitude_deg)
    t = math.radians(lst_deg)
    eps = math.radians(OBLIQUITY_DEGREES)
    return normalize(math.degrees(math.atan2(
        math.cos(t),
        -(math.sin(t) * math.cos(eps) + math.tan(math.radians(lat)) * math.sin(eps)),
    )))


def sphere_sines(latitude_deg: float, declination_deg: float) -> Dict[str, float]:
    """
    The sines of xiii.14-15 for a latitude and the Sun's declination.

    In the text's R = 3438 units (SS iii.34-36):

    - krantijya, the sine of declination, and dyujya, the day-radius;
    - kujya, the earth-sine = krantijya * tan(latitude) (the equinoctial
      shadow over the gnomon is tan(latitude));
    - carajya, the sine of ascensional difference = kujya * R / dyujya,
      clamped to +/-R where the Sun never sets or never rises;
    - antya, the day-measure. The treatise's own antya is the great-circle
      quantity R + carajya; xiii.14 describes instead its counterpart in
      the Sun's small circle, antya * dyujya / R. Burgess calls the verse
      a blunder; both are returned.

    Args:
        latitude_deg: Observer latitude (degrees).
        declination_deg: Sun's declination (degrees).

    Returns:
        dict of krantijya, dyujya, kujya, carajya, antya_great_circle,
        antya_small_circle.
    """
    lat = _check_latitude(latitude_deg)
    krantijya = jya(declination_deg)
    dyujya = koti(declination_deg)
    kujya = krantijya * math.tan(math.radians(lat))
    carajya = kujya * R_SINE / dyujya if dyujya else math.copysign(R_SINE, kujya)
    carajya = max(-float(R_SINE), min(float(R_SINE), carajya))
    antya = R_SINE + carajya
    return {
        "krantijya": krantijya,
        "dyujya": dyujya,
        "kujya": kujya,
        "carajya": carajya,
        "antya_great_circle": antya,
        "antya_small_circle": antya * dyujya / R_SINE,
    }


def sphere_points(jd: float, latitude_deg: float,
                  longitude_deg: float) -> List[SpherePoint]:
    """
    The three lagnas and the Sun at a moment and place (SS xiii.13-14).

    - lagna, the orient ecliptic-point, from `orient_ecliptic_point`;
    - asta-lagna, the occident point "determined in a corresponding
      manner" — the ecliptic point on the western horizon, opposite the
      lagna;
    - madhya-lagna, the meridian ecliptic-point, from the local sidereal
      time;
    - the Sun's true place.

    Args:
        jd: Julian Day.
        latitude_deg: Observer latitude (degrees).
        longitude_deg: Observer longitude, east positive (degrees).

    Returns:
        Points keyed lagna, asta_lagna, madhya_lagna, sun.
    """
    lat = _check_latitude(latitude_deg)
    ayan = ayanamsha(jd)
    lst = local_sidereal_time(jd, longitude_deg)
    rising = orient_ecliptic_point(lst, lat)
    setting = normalize(rising + 180.0)
    meridian = meridian_ecliptic_point(lst)
    sun = _sun(jd)
    return [
        _ecliptic_point("lagna", "Lagna (orient point)", rising,
                        rising - ayan, "SS.13.13"),
        _ecliptic_point("asta_lagna", "Asta-lagna (occident point)", setting,
                        setting - ayan, "SS.13.13",
                        note="Named here only; opposite the lagna."),
        _ecliptic_point("madhya_lagna", "Madhya-lagna (meridian point)",
                        meridian, meridian - ayan, "SS.13.14"),
        _ecliptic_point("sun", "Sun", sun.tropical_longitude,
                        sun.true_longitude, "SS.13.12",
                        note="The Sun revolves constantly on the ecliptic."),
    ]


def armillary_sphere(jd: float, latitude_deg: float, longitude_deg: float,
                     include_stars: bool = True) -> ArmillarySphere:
    """
    Assemble the armillary sphere for a place and moment (SS xiii.3-16).

    Great circles, the horizon, the Sun's six diurnal hoops and (optionally)
    the thirty-five stellar hoops; the sign divisions, the equinoxes and
    solstices, the lagnas and the Sun; and the sines of v.14-15 for the
    Sun's declination. The sphere is turned to the local sidereal time and
    its pole raised to the latitude.

    Args:
        jd: Julian Day.
        latitude_deg: Observer latitude (degrees), strictly inside +/-90.
        longitude_deg: Observer longitude, east positive (degrees).
        include_stars: Whether to add the stellar hoops.

    Returns:
        The assembled ArmillarySphere.

    Raises:
        ValueError: if the latitude is at or beyond a pole.
    """
    lat = _check_latitude(latitude_deg)
    lst = local_sidereal_time(jd, longitude_deg)
    hoops = great_hoops() + [horizon_hoop(lat, lst)] + solar_diurnal_hoops()
    if include_stars:
        hoops += star_diurnal_hoops(jd)
    return ArmillarySphere(
        jd=jd, latitude=lat, longitude=float(longitude_deg), lst_deg=lst,
        ayanamsha=ayanamsha(jd), zenith=equatorial_vector(lst, lat),
        hoops=hoops, sign_points=ecliptic_sign_points(),
        cardinal_points=cardinal_points(),
        points=sphere_points(jd, lat, longitude_deg),
        sines=sphere_sines(lat, sun_declination(jd)),
        chord_of_thirty=chord_of_thirty(),
    )


# ─────────────────────────────────────────────────────────────────
#  THE CLEPSYDRA — SS xiii.23
# ─────────────────────────────────────────────────────────────────

#: "sinks sixty times in a day and night" (xiii.23).
SINKINGS_PER_DAY = 60

#: One sinking is one ghati: a sixtieth of 1440 minutes.
MINUTES_PER_SINKING = 24.0


def clepsydra_elapsed(sinkings: int, partial: float = 0.0) -> ClepsydraReading:
    """
    Time elapsed after a number of sinkings of the bowl (SS xiii.23).

    Args:
        sinkings: Whole sinkings counted since the start.
        partial: How far the bowl has filled toward the next sinking,
            in [0, 1).

    Returns:
        The reading in ghatis, palas and vipalas, and in clock time.

    Raises:
        ValueError: for negative or non-integer sinkings, or a fill
            fraction outside [0, 1).
    """
    if isinstance(sinkings, bool) or int(sinkings) != sinkings or sinkings < 0:
        raise ValueError(f"Sinkings must be a non-negative whole number, got {sinkings}")
    if not 0.0 <= partial < 1.0:
        raise ValueError(f"Partial fill must lie in [0, 1), got {partial}")
    ghatis = int(sinkings) + float(partial)

    total_palas = ghatis * 60.0
    palas_whole = int(math.floor(total_palas + 1e-9))
    palas = palas_whole - int(ghatis) * 60
    vipalas = max(0.0, (total_palas - palas_whole) * 60.0)

    total_minutes = ghatis * MINUTES_PER_SINKING
    total_seconds = round(total_minutes * 60.0, 6)
    hours, rem = divmod(total_seconds, 3600.0)
    minutes, seconds = divmod(rem, 60.0)
    return ClepsydraReading(
        sinkings=int(sinkings), partial=float(partial), ghatis=ghatis,
        palas=palas, vipalas=vipalas, hours=int(hours), minutes=int(minutes),
        seconds=seconds, total_minutes=total_minutes,
    )


def clepsydra_sinkings(ghatis: float) -> ClepsydraReading:
    """
    Sinkings of the bowl that measure a span of ghatis — the inverse of
    `clepsydra_elapsed`.

    Args:
        ghatis: Elapsed time in ghatis (non-negative).

    Returns:
        The reading: whole sinkings plus the fraction of the current fill.

    Raises:
        ValueError: for a negative span.
    """
    if ghatis < 0:
        raise ValueError(f"Ghatis must be non-negative, got {ghatis}")
    whole = int(math.floor(ghatis + 1e-12))
    partial = min(max(0.0, ghatis - whole), 1.0 - 1e-12)
    return clepsydra_elapsed(whole, partial)


def clepsydra_day(jd: float, latitude_deg: float) -> dict:
    """
    Sinkings of the bowl between sunrise and sunset, and sunset and sunrise.

    The day length comes from `ch03.day_length_ghatis` with the Sun's
    tropical longitude; the night is the rest of the sixty.

    Args:
        jd: Julian Day.
        latitude_deg: Observer latitude (degrees).

    Returns:
        dict with day and night lengths in ghatis, their sinking readings,
        and the Sun's longitude and declination used.
    """
    from suryasiddhanta.ch03_direction_place_time import day_length_ghatis

    lat = _check_latitude(latitude_deg)
    sun = _sun(jd)
    day = day_length_ghatis(lat, sun.tropical_longitude)
    night = SINKINGS_PER_DAY - day
    return {
        "latitude": lat,
        "sun_tropical_longitude": sun.tropical_longitude,
        "sun_declination": declination(sun.tropical_longitude),
        "day_ghatis": day,
        "night_ghatis": night,
        "day_sinkings": clepsydra_sinkings(day).to_dict(),
        "night_sinkings": clepsydra_sinkings(night).to_dict(),
        "verse": "SS.13.23",
    }


def clepsydra_drift(observed_per_day: float) -> dict:
    """
    Error of a bowl that does not sink exactly sixty times a day.

    Burgess notes such a vessel "could not be accurately constructed from
    measurements alone" and must be tested by use. A bowl sinking N times
    a day takes 1440/N minutes a sinking, so each sinking is off by
    1440/N - 24 minutes (negative: the bowl runs fast), and after a true
    day it reads N - 60 ghatis too many.

    Args:
        observed_per_day: Sinkings counted in one day and night (> 0).

    Returns:
        dict of minutes per sinking, error per sinking, and reading error
        per day in ghatis and minutes (positive: reads ahead).

    Raises:
        ValueError: if the count is not positive.
    """
    if observed_per_day <= 0:
        raise ValueError(f"Observed sinkings must be positive, got {observed_per_day}")
    minutes = 1440.0 / observed_per_day
    ahead = observed_per_day - SINKINGS_PER_DAY
    return {
        "observed_per_day": observed_per_day,
        "minutes_per_sinking": minutes,
        "error_minutes_per_sinking": minutes - MINUTES_PER_SINKING,
        "reading_error_ghatis_per_day": ahead,
        "reading_error_minutes_per_day": ahead * MINUTES_PER_SINKING,
        "verse": "SS.13.23",
    }


# ─────────────────────────────────────────────────────────────────
#  TIME FROM INSTRUMENTS — SS xiii.20-24
# ─────────────────────────────────────────────────────────────────

#: Instruments with a time-finding rule, in the order of xiii.20-24.
INSTRUMENT_METHODS: Tuple[str, ...] = ("nara", "cakra", "dhanus", "yashti")


def _rising_hour_angle(jd: float, lat: float) -> Tuple[float, float]:
    """
    The Sun's declination and its hour angle at sunrise.

    Raises:
        ValueError: if the Sun does not both rise and set that day.
    """
    dec = sun_declination(jd)
    product = math.tan(math.radians(lat)) * math.tan(math.radians(dec))
    if abs(product) >= 1.0:
        raise ValueError(
            f"The Sun does not rise and set at latitude {lat} with "
            f"declination {dec:.2f} deg")
    return dec, sunrise_hour_angle(lat, dec)


def _altitude(hour_angle_deg: float, dec_deg: float, lat_deg: float) -> float:
    """The Sun's altitude for an hour angle, declination and latitude."""
    lat, dec, h = map(math.radians, (lat_deg, dec_deg, hour_angle_deg))
    sin_alt = (math.sin(lat) * math.sin(dec)
               + math.cos(lat) * math.cos(dec) * math.cos(h))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))


def _timed(instrument: str, reading: float, unit: str, arc_from_horizon: float,
           h_rise: float, dec: float, lat: float, forenoon: bool,
           source: str, verse: str, extra: Dict[str, float]) -> InstrumentTime:
    """
    Build an InstrumentTime from the arc of the diurnal circle between the
    Sun and the horizon.

    Before noon the arc is measured from the point of sunrise, after noon
    to the point of sunset, as the commentary to xiii.20 prescribes.
    """
    hour_angle = h_rise - arc_from_horizon
    near = arc_from_horizon / 6.0
    far = (h_rise + hour_angle) / 6.0
    return InstrumentTime(
        instrument=instrument, reading=reading, reading_unit=unit,
        ghatis_since_sunrise=near if forenoon else far,
        ghatis_to_sunset=far if forenoon else near,
        sun_altitude_deg=_altitude(hour_angle, dec, lat),
        hour_angle_deg=-hour_angle if forenoon else hour_angle,
        sun_declination_deg=dec, half_day_ghatis=h_rise / 6.0,
        forenoon=forenoon, source=source, verse=verse, extra=extra,
    )


def time_from_altitude(altitude_deg: float, jd: float, latitude_deg: float,
                       forenoon: bool = True) -> InstrumentTime:
    """
    Time since sunrise, or until sunset, from the Sun's altitude (SS iii.34-39).

    The rule behind every shadow- and altitude-instrument of the chapter.
    The hour angle follows from

        cos H = (sin a - sin(lat) sin(dec)) / (cos(lat) cos(dec))

    and the time from the horizon is (H_rise - H) / 6 ghatis, since the
    Sun turns six degrees in a ghati. An altitude is met twice a day, so
    `forenoon` says which side of noon it was taken.

    Args:
        altitude_deg: Sun's altitude (degrees, above 0).
        jd: Julian Day of the observation (the date fixes the declination).
        latitude_deg: Observer latitude (degrees).
        forenoon: True if the reading was taken before noon.

    Returns:
        InstrumentTime labelled as the altitude rule of Ch.3.

    Raises:
        ValueError: for a non-positive altitude, an altitude above the
            Sun's noon altitude, or a Sun that does not rise and set.
    """
    lat = _check_latitude(latitude_deg)
    if not math.isfinite(altitude_deg) or not 0.0 < altitude_deg <= 90.0:
        raise ValueError(f"The Sun's altitude must be in (0, 90] degrees, got {altitude_deg}")
    dec, h_rise = _rising_hour_angle(jd, lat)
    lat_r, dec_r = math.radians(lat), math.radians(dec)
    cos_h = ((math.sin(math.radians(altitude_deg)) - math.sin(lat_r) * math.sin(dec_r))
             / (math.cos(lat_r) * math.cos(dec_r)))
    if cos_h > 1.0 + 1e-12:
        noon = 90.0 - abs(lat - dec)
        raise ValueError(
            f"Altitude {altitude_deg} deg exceeds the Sun's noon altitude "
            f"of {noon:.3f} deg on this date")
    hour_angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_h))))
    return _timed(
        instrument="altitude", reading=float(altitude_deg), unit="degrees",
        arc_from_horizon=h_rise - hour_angle, h_rise=h_rise, dec=dec, lat=lat,
        forenoon=forenoon, source="verse", verse="SS.3.34", extra={},
    )


def nara_yantra_time(shadow: float, jd: float, latitude_deg: float,
                     gnomon: float = 12.0, forenoon: bool = True) -> InstrumentTime:
    """
    Time from the shadow of the man-instrument (nara-yantra, SS xiii.24).

    "The man-instrument is good in the day-time, when the Sun is clear":
    a gnomon, whose shadow gives the altitude (tan a = gnomon / shadow)
    and so the time, by the rules of the third chapter.

    Args:
        shadow: Shadow length, in the gnomon's units (non-negative).
        jd: Julian Day of the observation.
        latitude_deg: Observer latitude (degrees).
        gnomon: Gnomon height (default the text's twelve digits).
        forenoon: True if the shadow was measured before noon.

    Returns:
        InstrumentTime, `source` "verse".

    Raises:
        ValueError: for a negative shadow or gnomon, or as
            `time_from_altitude`.
    """
    if shadow < 0 or gnomon <= 0:
        raise ValueError(f"Shadow must be non-negative and gnomon positive, "
                         f"got {shadow} and {gnomon}")
    altitude = solar_altitude_from_shadow(shadow, gnomon)
    base = time_from_altitude(altitude, jd, latitude_deg, forenoon)
    return dataclasses.replace(
        base, instrument="nara", reading=float(shadow), reading_unit="shadow",
        source="verse", verse="SS.13.24",
        extra={"gnomon": float(gnomon), "altitude_deg": altitude},
    )


def cakra_time(altitude_deg: float, jd: float, latitude_deg: float,
               forenoon: bool = True) -> InstrumentTime:
    """
    Time from the wheel (cakra) — commentary to SS xiii.20.

    A wheel graduated to degrees hangs by a string with its edge turned to
    the Sun; the shadow of the central peg falls on the rim at the Sun's
    altitude, from which the time follows (SS iii.37-39).

    Args:
        altitude_deg: Altitude read on the rim (degrees).
        jd: Julian Day of the observation.
        latitude_deg: Observer latitude (degrees).
        forenoon: True if read before noon.

    Returns:
        InstrumentTime, `source` "commentary".
    """
    base = time_from_altitude(altitude_deg, jd, latitude_deg, forenoon)
    return dataclasses.replace(
        base, instrument="cakra", reading=float(altitude_deg),
        reading_unit="degrees", source="commentary", verse="SS.13.20",
        extra={"zenith_distance_deg": 90.0 - altitude_deg},
    )


def dhanus_time(altitude_deg: float, jd: float, latitude_deg: float,
                forenoon: bool = True) -> InstrumentTime:
    """
    Time from the arc (dhanus) — commentary to SS xiii.20.

    The lower half, or a quadrant, of the wheel; it reads altitude the same
    way but cannot show more than ninety degrees.

    Args:
        altitude_deg: Altitude read on the arc (0 < altitude <= 90).
        jd: Julian Day of the observation.
        latitude_deg: Observer latitude (degrees).
        forenoon: True if read before noon.

    Returns:
        InstrumentTime, `source` "commentary".

    Raises:
        ValueError: if the altitude lies outside the arc's quadrant.
    """
    if not 0.0 < altitude_deg <= 90.0:
        raise ValueError(f"The arc reads altitudes in (0, 90], got {altitude_deg}")
    base = time_from_altitude(altitude_deg, jd, latitude_deg, forenoon)
    return dataclasses.replace(
        base, instrument="dhanus", reading=float(altitude_deg),
        reading_unit="degrees", source="commentary", verse="SS.13.20",
        extra={"zenith_distance_deg": 90.0 - altitude_deg},
    )


def _yashti_geometry(jd: float, lat: float,
                     staff_length: float) -> Tuple[float, float, float, float]:
    """The Sun's declination, rising hour angle, scaled day-radius and agra."""
    if staff_length <= 0:
        raise ValueError(f"Staff length must be positive, got {staff_length}")
    dec, h_rise = _rising_hour_angle(jd, lat)
    day_radius = staff_length * math.cos(math.radians(dec))
    agra = staff_length * math.sin(math.radians(dec)) / math.cos(math.radians(lat))
    return dec, h_rise, day_radius, agra


def yashti_chord(ghatis: float, jd: float, latitude_deg: float,
                 staff_length: float = float(R_SINE)) -> float:
    """
    Chord the staff would measure a given time from the horizon.

    The forward form of `yashti_time`: the chord from the staff's tip to
    the point of sunrise (or sunset) subtending `ghatis` of the Sun's
    diurnal circle, whose radius is staff_length * cos(dec).

    Args:
        ghatis: Time since sunrise (or until sunset), at most the half-day.
        jd: Julian Day.
        latitude_deg: Observer latitude (degrees).
        staff_length: Length of the staff (default R = 3438).

    Returns:
        The chord, in the staff's units.

    Raises:
        ValueError: for negative ghatis, a span beyond noon, or a Sun that
            does not rise and set.
    """
    lat = _check_latitude(latitude_deg)
    if ghatis < 0:
        raise ValueError(f"Ghatis must be non-negative, got {ghatis}")
    _, h_rise, day_radius, _ = _yashti_geometry(jd, lat, staff_length)
    arc = 6.0 * ghatis
    if arc > h_rise + 1e-9:
        raise ValueError(
            f"{ghatis} ghatis runs past noon; the half-day is {h_rise / 6.0:.3f}")
    return 2.0 * day_radius * math.sin(math.radians(arc) / 2.0)


def yashti_time(chord: float, jd: float, latitude_deg: float,
                forenoon: bool = True,
                staff_length: float = float(R_SINE)) -> InstrumentTime:
    """
    Time from the staff (yashti-yantra) — commentary to SS xiii.20.

    On level ground a circle is drawn with radius equal to the staff, and
    the sine of amplitude (agra = L sin(dec) / cos(lat)) marks the points of
    sunrise and sunset on it. The staff, its foot at the centre, is pointed
    at the Sun so it casts no shadow; its tip then lies on the day's diurnal
    circle, of radius L cos(dec). The chord from the tip to the sunrise point
    (before noon) or sunset point (after), applied to an inner circle of
    that radius divided into sixty nadis, gives the time:

        arc = 2 asin(chord / (2 L cos dec)),  ghatis = arc / 6

    Args:
        chord: Measured distance from the staff's tip to the horizon point.
        jd: Julian Day of the observation.
        latitude_deg: Observer latitude (degrees).
        forenoon: True if measured before noon (to the sunrise point).
        staff_length: Length of the staff (default R = 3438).

    Returns:
        InstrumentTime, `source` "commentary", with the agra, day-radius
        and arc in `extra`.

    Raises:
        ValueError: for a negative chord, one longer than the diurnal
            circle's diameter, one reaching past noon, or a Sun that does
            not rise and set.
    """
    lat = _check_latitude(latitude_deg)
    if chord < 0:
        raise ValueError(f"Chord must be non-negative, got {chord}")
    dec, h_rise, day_radius, agra = _yashti_geometry(jd, lat, staff_length)
    if chord > 2.0 * day_radius:
        raise ValueError(
            f"Chord {chord} exceeds the diurnal circle's diameter "
            f"{2.0 * day_radius:.3f}")
    arc = math.degrees(2.0 * math.asin(chord / (2.0 * day_radius)))
    if arc > h_rise + 1e-9:
        raise ValueError(
            f"Chord {chord} spans {arc:.3f} deg, past noon (half-day arc "
            f"{h_rise:.3f} deg); measure from the other horizon point")
    return _timed(
        instrument="yashti", reading=float(chord), unit="chord",
        arc_from_horizon=arc, h_rise=h_rise, dec=dec, lat=lat,
        forenoon=forenoon, source="commentary", verse="SS.13.20",
        extra={"agra": agra, "day_radius": day_radius, "arc_deg": arc,
               "staff_length": float(staff_length)},
    )


def instrument_time(instrument: str, value: float, jd: float,
                    latitude_deg: float, forenoon: bool = True,
                    gnomon: float = 12.0,
                    staff_length: float = float(R_SINE)) -> InstrumentTime:
    """
    Time of day from any of the chapter's time-finding instruments.

    Args:
        instrument: One of INSTRUMENT_METHODS — "nara" (value is a shadow),
            "cakra" or "dhanus" (an altitude in degrees), "yashti" (a chord).
        value: The reading.
        jd: Julian Day of the observation.
        latitude_deg: Observer latitude (degrees).
        forenoon: True if read before noon.
        gnomon: Gnomon height for "nara".
        staff_length: Staff length for "yashti".

    Returns:
        The InstrumentTime from the named method.

    Raises:
        KeyError: for an instrument without a time-finding rule.
    """
    methods: Dict[str, Callable[[], InstrumentTime]] = {
        "nara": lambda: nara_yantra_time(value, jd, latitude_deg, gnomon, forenoon),
        "cakra": lambda: cakra_time(value, jd, latitude_deg, forenoon),
        "dhanus": lambda: dhanus_time(value, jd, latitude_deg, forenoon),
        "yashti": lambda: yashti_time(value, jd, latitude_deg, forenoon, staff_length),
    }
    key = str(instrument).lower()
    if key not in methods:
        raise KeyError(
            f"No time-finding rule for {instrument!r}. Known: "
            f"{', '.join(INSTRUMENT_METHODS)}")
    return methods[key]()
