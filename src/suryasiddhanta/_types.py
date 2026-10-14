"""
Shared dataclasses and type definitions for the suryasiddhanta library.

This module contains all dataclasses used across multiple chapter modules,
centralized here to prevent circular imports. No chapter module imports
from another chapter module's dataclass definitions -- they all import
from here.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# -- Epicycle pair (Ch.2) --

@dataclass
class EpicyclePair:
    """
    Pulsating epicycle (SS Ch.2 v.34-38).

    even: size at the end of the even quadrants (kendra 0/180 deg,
          i.e. on the apsis line, where bhuja = 0)
    odd:  size at the end of the odd quadrants (kendra 90/270 deg,
          where bhuja = 90)

    SS ii.38: corrected epicycle = even + (odd - even) * sin(bhuja),
    the base-sine (bhujajya / R) being the interpolation factor.
    """
    even: float
    odd: float

    def at_bhuja(self, bhuja_deg: float) -> float:
        sin_bhuja = math.sin(math.radians(abs(bhuja_deg)))
        return self.even + sin_bhuja * (self.odd - self.even)


# -- Nakshatra (Ch.8) --

@dataclass
class Nakshatra:
    """A nakshatra (lunar mansion) with its junction star data."""
    number: int
    name: str
    devanagari: str
    longitude: float
    latitude: float
    star: str
    span_start: float
    span_end: float
    deity: str
    gana: str


# -- Vedic time (Ch.1) --

@dataclass
class VedicTime:
    """Time in the Vedic (SS) system: ghatis, palas, vipalas."""
    ghatis: int = 0
    palas: int = 0
    vipalas: float = 0.0

    @classmethod
    def from_day_fraction(cls, frac: float) -> VedicTime:
        total_ghatis = frac * 60
        gh = int(total_ghatis)
        remainder_palas = (total_ghatis - gh) * 60
        pl = int(remainder_palas)
        vp = (remainder_palas - pl) * 60
        return cls(ghatis=gh, palas=pl, vipalas=round(vp, 2))

    def to_day_fraction(self) -> float:
        total_gh = self.ghatis + self.palas / 60.0 + self.vipalas / 3600.0
        return total_gh / 60.0

    def to_minutes(self) -> float:
        return self.ghatis * 24 + self.palas * 0.4 + self.vipalas / 150.0

    def __str__(self) -> str:
        return f"{self.ghatis:02d}gh {self.palas:02d}pa {self.vipalas:.1f}vi"


# -- Mean positions (Ch.1) --

@dataclass
class MeanPositions:
    """Mean sidereal positions for all SS bodies at a given date."""
    jd: float
    Sun: float
    Moon: float
    Mars: float
    Mercury: float
    Jupiter: float
    Venus: float
    Saturn: float
    Moon_apogee: float
    Moon_node: float

    def as_dict(self) -> dict:
        return {
            "Sun": round(self.Sun, 4),
            "Moon": round(self.Moon, 4),
            "Mars": round(self.Mars, 4),
            "Mercury": round(self.Mercury, 4),
            "Jupiter": round(self.Jupiter, 4),
            "Venus": round(self.Venus, 4),
            "Saturn": round(self.Saturn, 4),
            "Moon_apogee": round(self.Moon_apogee, 4),
            "Moon_node": round(self.Moon_node, 4),
        }


# -- Planet position result (Ch.2) --

@dataclass
class PlanetPosition:
    """Complete planetary position from Surya Siddhanta computation."""
    planet: str
    jd: float
    year: int
    month: int
    day: int

    ahargana: float
    mean_lon: float
    mandocca: float
    manda_kendra: float
    manda_corr: float
    sighrocca: Optional[float]
    sighra_kendra: Optional[float]
    sighra_corr: Optional[float]

    true_longitude: float
    ayanamsha: float
    tropical_longitude: float

    nakshatra: dict
    rashi: dict

    def __str__(self) -> str:
        d, m, s = _dms(self.true_longitude)
        return (
            f"{self.planet:10s} | "
            f"True lon: {d:3d}°{m:02d}′{s:04.1f}″ ({self.true_longitude:.4f}°) | "
            f"Nakshatra: {self.nakshatra['name']} pada {self.nakshatra['pada']} | "
            f"Rashi: {self.rashi['name']}"
        )

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "date": f"{self.year}-{self.month:02d}-{self.day:02d}",
            "jd": round(self.jd, 2),
            "ahargana": round(self.ahargana, 2),
            "mean_longitude": round(self.mean_lon, 4),
            "mandocca": round(self.mandocca, 4),
            "manda_kendra": round(self.manda_kendra, 4),
            "manda_correction": round(self.manda_corr, 4),
            "sighrocca": round(self.sighrocca, 4) if self.sighrocca else None,
            "sighra_kendra": round(self.sighra_kendra, 4) if self.sighra_kendra else None,
            "sighra_correction": round(self.sighra_corr, 4) if self.sighra_corr else None,
            "true_longitude": round(self.true_longitude, 4),
            "ayanamsha": round(self.ayanamsha, 4),
            "tropical_longitude": round(self.tropical_longitude, 4),
            "nakshatra": self.nakshatra,
            "rashi": self.rashi,
        }


# -- Gnomon result (Ch.3) --

@dataclass
class GnomonResult:
    """Result of gnomon shadow calculation."""
    gnomon_length: float
    shadow_length: float
    altitude_deg: float
    azimuth_deg: Optional[float]
    direction: str

    def __str__(self) -> str:
        return (
            f"Gnomon: {self.gnomon_length} units  |  "
            f"Shadow: {self.shadow_length:.3f} units  |  "
            f"Altitude: {self.altitude_deg:.2f}°  |  "
            f"Direction: {self.direction}"
        )


# -- Lunar eclipse result (Ch.4) --

@dataclass
class LunarEclipse:
    """Result of SS lunar eclipse calculation."""
    jd: float
    is_eclipse: bool
    eclipse_type: str
    moon_latitude: float
    moon_diameter: float
    shadow_diameter: float
    magnitude: float
    half_duration: Optional[float]
    totality_half: Optional[float]
    notes: str

    def __str__(self):
        if not self.is_eclipse:
            return f"No lunar eclipse — Moon latitude {self.moon_latitude:.1f}′"
        return (
            f"Lunar Eclipse: {self.eclipse_type.upper()}\n"
            f"  Moon latitude  : {self.moon_latitude:.1f}′\n"
            f"  Moon diameter  : {self.moon_diameter:.1f}′\n"
            f"  Shadow diameter: {self.shadow_diameter:.1f}′\n"
            f"  Magnitude      : {self.magnitude:.3f}\n"
            f"  Half-duration  : {self.half_duration:.1f} min\n"
        )


# -- Solar eclipse result (Ch.5) --

@dataclass
class SolarEclipse:
    """Result of SS solar eclipse calculation."""
    jd: float
    is_eclipse: bool
    eclipse_type: str
    sun_diameter: float
    moon_diameter: float
    magnitude: float
    notes: str
    lambana: Optional[float] = None
    nati: Optional[float] = None
    half_duration: Optional[float] = None
    observer_lat: Optional[float] = None
    observer_lon: Optional[float] = None
    moon_latitude: float = 0.0  # signed apparent latitude, arcminutes
    sun_altitude_deg: Optional[float] = None  # at corrected conjunction
    locally_visible: Optional[bool] = None  # geometric overlap and daylight there

    def __str__(self):
        if not self.is_eclipse:
            return "No solar eclipse"
        lines = [
            f"Solar Eclipse: {self.eclipse_type.upper()}",
            f"  Sun  diameter: {self.sun_diameter:.1f}′",
            f"  Moon diameter: {self.moon_diameter:.1f}′",
            f"  Magnitude    : {self.magnitude:.3f}",
        ]
        if self.lambana is not None:
            lines.append(f"  Lambana      : {self.lambana:.1f}′")
        if self.nati is not None:
            lines.append(f"  Nati         : {self.nati:.1f}′")
        if self.half_duration is not None:
            lines.append(f"  Half-duration: {self.half_duration:.1f} min")
        return "\n".join(lines) + "\n"


# -- Panchanga result (cross-chapter) --

@dataclass
class Panchanga:
    """Complete panchanga (five-element almanac) for a date."""
    year: int
    month: int
    day: int
    jd: float

    tithi_: dict = field(default_factory=dict)
    vara_: dict = field(default_factory=dict)
    nakshatra: dict = field(default_factory=dict)
    yoga_: dict = field(default_factory=dict)
    karana_: dict = field(default_factory=dict)

    masa: dict = field(default_factory=dict)
    ritu: dict = field(default_factory=dict)
    samvatsara_: dict = field(default_factory=dict)
    sun_lon: float = 0.0
    moon_lon: float = 0.0
    ayanamsha: float = 0.0

    def __str__(self) -> str:
        lines = [
            f"{'='*60}",
            f"  पञ्चाङ्ग (Panchanga) — {self.year}-{self.month:02d}-{self.day:02d}",
            f"{'='*60}",
            f"  Tithi    : {self.tithi_['name']} ({self.tithi_['paksha']}) #{self.tithi_['number']}",
            f"  Vara     : {self.vara_['name']} ({self.vara_['name_en']})",
            f"  Nakshatra: {self.nakshatra['name']} pada {self.nakshatra['pada']}",
            f"  Yoga     : {self.yoga_['name']} #{self.yoga_['number']}",
            f"  Karana   : {self.karana_['name']} ({self.karana_['type']})",
            f"{'-'*60}",
            f"  Masa     : {self.masa['name']}",
            f"  Ritu     : {self.ritu['name']}",
            f"  Samvatsara: {self.samvatsara_['name']}",
            f"{'-'*60}",
            f"  Sun  lon : {self.sun_lon:.4f}°",
            f"  Moon lon : {self.moon_lon:.4f}°",
            f"  Ayanamsha: {self.ayanamsha:.4f}°",
            f"{'='*60}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "date": f"{self.year}-{self.month:02d}-{self.day:02d}",
            "jd": round(self.jd, 2),
            "tithi": self.tithi_,
            "vara": self.vara_,
            "nakshatra": self.nakshatra,
            "yoga": self.yoga_,
            "karana": self.karana_,
            "masa": self.masa,
            "ritu": self.ritu,
            "samvatsara": self.samvatsara_,
            "sun_longitude": round(self.sun_lon, 4),
            "moon_longitude": round(self.moon_lon, 4),
            "ayanamsha": round(self.ayanamsha, 4),
        }


# -- Pata event (Ch.11) --

@dataclass
class PataEvent:
    """
    One pata — Vyatipata or Vaidhrita — SS Ch.11.

    A pata is the moment the Sun's and Moon's declinations become equal
    in amount: in the same direction for Vyatipata (tropical longitude
    sum 180 deg), in opposite directions for Vaidhrita (sum 360 deg).

    Not the same thing as the nitya-yoga also called Vyatipata (number
    17 of 27) in ch01_mean_motions: that yoga is a fixed 13 deg 20'
    span of the longitude sum with no declination condition at all.
    """
    kind: str
    jd_sum_crossing: float
    jd_middle: float
    jd_begin: float
    jd_end: float
    duration_ghatis: float
    sun_declination: float
    moon_declination: float
    moon_latitude: float
    longitude_sum: float
    refined: bool
    is_past: Optional[bool] = None

    @property
    def duration_hours(self) -> float:
        """Total duration of the pata, in hours."""
        return (self.jd_end - self.jd_begin) * 24.0

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "kind": self.kind,
            "jd_sum_crossing": self.jd_sum_crossing,
            "jd_middle": self.jd_middle,
            "jd_begin": self.jd_begin,
            "jd_end": self.jd_end,
            "duration_ghatis": round(self.duration_ghatis, 2),
            "duration_hours": round(self.duration_hours, 3),
            "sun_declination": self.sun_declination,
            "moon_declination": self.moon_declination,
            "moon_latitude_arcmin": self.moon_latitude,
            "longitude_sum": self.longitude_sum,
            "refined": self.refined,
            "is_past": self.is_past,
        }


@dataclass
class OrbitInfo:
    """
    One body's orbit (kakshya) and distance — SS Ch.12 v.80-90.

    The Surya Siddhanta holds that every planet covers the same linear
    distance in a yuga, so an orbit's size is simply proportional to the
    time the body takes to go round it. Everything here therefore falls
    out of the Moon's stated orbit of 324,000 yojanas and the revolution
    counts of Ch.1.

    `stated_yojanas` is the figure the text itself gives in v.85-89,
    kept alongside the derived one because the two differ by up to about
    1.3 yojanas through the text's own rounding.
    """
    body: str
    orbit_yojanas: float
    revolutions_per_kalpa: int
    orbit_diameter_yojanas: float
    distance_yojanas: float
    daily_motion_arcmin: float
    stated_yojanas: Optional[int] = None
    verse: Optional[str] = None

    @property
    def stated_difference(self) -> Optional[float]:
        """Derived orbit less the orbit the text states, in yojanas."""
        if self.stated_yojanas is None:
            return None
        return self.orbit_yojanas - self.stated_yojanas

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "body": self.body,
            "orbit_yojanas": round(self.orbit_yojanas, 3),
            "revolutions_per_kalpa": self.revolutions_per_kalpa,
            "orbit_diameter_yojanas": round(self.orbit_diameter_yojanas, 3),
            "distance_yojanas": round(self.distance_yojanas, 3),
            "daily_motion_arcmin": round(self.daily_motion_arcmin, 4),
            "stated_yojanas": self.stated_yojanas,
            "stated_difference": (None if self.stated_difference is None
                                  else round(self.stated_difference, 3)),
            "verse": self.verse,
        }


@dataclass
class CosmicPlace:
    """
    One of the reference places of the Surya Siddhanta's geography —
    SS Ch.12 v.34-44, with Ujjayini from Ch.1 v.62.

    Meru and Vadavamukha are the poles and have no meaningful longitude,
    so `longitude` is None for them. The four cities stand on the
    equator a quadrant of the earth's circumference apart.
    """
    name: str
    iast: str
    latitude: float
    longitude: Optional[float]
    clime: Optional[str]
    direction: str
    note: str
    verse: str

    @property
    def is_pole(self) -> bool:
        """True for Meru and Vadavamukha, where longitude is undefined."""
        return self.longitude is None

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "name": self.name,
            "iast": self.iast,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "clime": self.clime,
            "direction": self.direction,
            "is_pole": self.is_pole,
            "note": self.note,
            "verse": self.verse,
        }


# -- Armillary sphere and instruments (Ch.13) --

@dataclass
class SphereHoop:
    """
    One hoop of the armillary sphere (gola-yantra) — SS Ch.13 v.4-16.

    Every hoop is a circle on the unit sphere, in the equatorial frame:
    z along the Meru axis toward the north pole, x toward the vernal
    equinox, y toward right ascension 90 deg. The circle is the set of
    points p with p . normal == offset, so a great circle has offset 0
    and a diurnal circle at declination d has normal (0, 0, 1) and offset
    sin(d).

    `kind` is one of great, solar_diurnal, star_diurnal or horizon;
    `group` is the display group the React page toggles by. `day_radius`
    is the text's dyujya — the radius of a diurnal circle as an SS sine,
    R = 3438 — and is None for great circles. `marker` is the unit vector
    of the star a stellar hoop was fixed for.
    """
    key: str
    name: str
    kind: str
    group: str
    normal: Tuple[float, float, float]
    offset: float
    declination: Optional[float]
    day_radius: Optional[float]
    verse: str
    note: str = ""
    marker: Optional[Tuple[float, float, float]] = None
    cased_below: bool = False

    @property
    def radius(self) -> float:
        """Radius of the hoop as a fraction of the sphere's radius."""
        return math.sqrt(max(0.0, 1.0 - self.offset * self.offset))

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "key": self.key,
            "name": self.name,
            "kind": self.kind,
            "group": self.group,
            "normal": [round(c, 6) for c in self.normal],
            "offset": round(self.offset, 6),
            "radius": round(self.radius, 6),
            "declination": (None if self.declination is None
                            else round(self.declination, 4)),
            "day_radius": (None if self.day_radius is None
                           else round(self.day_radius, 2)),
            "marker": (None if self.marker is None
                       else [round(c, 6) for c in self.marker]),
            "cased_below": self.cased_below,
            "note": self.note,
            "verse": self.verse,
        }


@dataclass
class SpherePoint:
    """
    A named point on the armillary sphere — SS Ch.13 v.10-15.

    The sign divisions, the equinoxes and solstices, the three lagnas
    (orient, occident and meridian ecliptic-points) and the Sun. Longitude
    is given both tropical, which fixes the point on the sphere, and
    sidereal, the frame the rest of the treatise reckons in.
    """
    key: str
    name: str
    tropical_longitude: float
    sidereal_longitude: float
    right_ascension: float
    declination: float
    vector: Tuple[float, float, float]
    verse: str
    note: str = ""

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "key": self.key,
            "name": self.name,
            "tropical_longitude": round(self.tropical_longitude, 4),
            "sidereal_longitude": round(self.sidereal_longitude, 4),
            "right_ascension": round(self.right_ascension, 4),
            "declination": round(self.declination, 4),
            "vector": [round(c, 6) for c in self.vector],
            "note": self.note,
            "verse": self.verse,
        }


@dataclass
class ArmillarySphere:
    """
    The armillary sphere assembled for a place and a moment — SS Ch.13.

    Hoops and points are all in the equatorial frame (see SphereHoop).
    `lst_deg` is the local sidereal time, the angle through which the
    sphere has turned about its axis; `zenith` is the observer's zenith in
    the same frame, which is the normal of the horizon hoop. The pole
    stands at an altitude equal to the latitude (v.15-16).
    """
    jd: float
    latitude: float
    longitude: float
    lst_deg: float
    ayanamsha: float
    zenith: Tuple[float, float, float]
    hoops: List[SphereHoop]
    sign_points: List[SpherePoint]
    cardinal_points: List[SpherePoint]
    points: List[SpherePoint]
    sines: Dict[str, float]
    chord_of_thirty: float

    @property
    def pole_altitude(self) -> float:
        """Altitude of the elevated pole, which equals the latitude."""
        return self.latitude

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "jd": self.jd,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "pole_altitude": self.pole_altitude,
            "lst_deg": round(self.lst_deg, 4),
            "ayanamsha": round(self.ayanamsha, 4),
            "zenith": [round(c, 6) for c in self.zenith],
            "hoops": [h.to_dict() for h in self.hoops],
            "sign_points": [p.to_dict() for p in self.sign_points],
            "cardinal_points": [p.to_dict() for p in self.cardinal_points],
            "points": [p.to_dict() for p in self.points],
            "sines": {k: round(v, 3) for k, v in self.sines.items()},
            "chord_of_thirty": round(self.chord_of_thirty, 3),
        }


@dataclass
class ClepsydraReading:
    """
    A reading of the water-clock (ghati-yantra) — SS Ch.13 v.23.

    The copper bowl sinks sixty times in a day and night, so each sinking
    is one ghati (nadi) of 24 minutes. `partial` is how far the bowl has
    filled toward its next sinking, from 0 up to (not including) 1.
    """
    sinkings: int
    partial: float
    ghatis: float
    palas: int
    vipalas: float
    hours: int
    minutes: int
    seconds: float
    total_minutes: float

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "sinkings": self.sinkings,
            "partial": round(self.partial, 4),
            "ghatis": round(self.ghatis, 4),
            "ghati_pala_vipala": f"{int(self.ghatis)}-{self.palas:02d}-{self.vipalas:04.1f}",
            "palas": self.palas,
            "vipalas": round(self.vipalas, 2),
            "clock": f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:04.1f}",
            "total_minutes": round(self.total_minutes, 3),
        }


@dataclass
class InstrumentTime:
    """
    Time of day found with an instrument — SS Ch.13 v.20-24.

    `reading` is what the instrument measured, in `reading_unit`: a shadow
    for the gnomon (nara), an altitude for the wheel (cakra) and arc
    (dhanus), a chord for the staff (yashti). `source` is "verse" when the
    method is the treatise's own and "commentary" when it comes from
    Burgess's notes. Times are in ghatis; the half-day is sunrise to noon.
    """
    instrument: str
    reading: float
    reading_unit: str
    ghatis_since_sunrise: float
    ghatis_to_sunset: float
    sun_altitude_deg: float
    hour_angle_deg: float
    sun_declination_deg: float
    half_day_ghatis: float
    forenoon: bool
    source: str
    verse: str
    extra: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        since = self.ghatis_since_sunrise
        return {
            "instrument": self.instrument,
            "reading": self.reading,
            "reading_unit": self.reading_unit,
            "ghatis_since_sunrise": round(since, 4),
            "ghatis_to_sunset": round(self.ghatis_to_sunset, 4),
            "hours_since_sunrise": round(since * 24.0 / 60.0, 4),
            "sun_altitude_deg": round(self.sun_altitude_deg, 4),
            "hour_angle_deg": round(self.hour_angle_deg, 4),
            "sun_declination_deg": round(self.sun_declination_deg, 4),
            "half_day_ghatis": round(self.half_day_ghatis, 4),
            "forenoon": self.forenoon,
            "source": self.source,
            "verse": self.verse,
            "extra": {k: round(v, 4) for k, v in self.extra.items()},
        }


# -- Modes of reckoning time (Ch.14) --

@dataclass
class Mana:
    """
    One of the nine modes of reckoning time (mana) — SS Ch.14 v.1-2.

    `unit_days` is the length of the mode's unit in civil days, which is
    all `convert` needs. `practical` is verse 2's own division: four modes
    are used in practice, the rest are not.
    """
    key: str
    iast: str
    devanagari: str
    english: str
    unit: str
    unit_days: float
    practical: bool
    uses: List[str]
    verses: str
    source: str

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "key": self.key, "iast": self.iast, "devanagari": self.devanagari,
            "english": self.english, "unit": self.unit,
            "unit_days": self.unit_days, "practical": self.practical,
            "uses": list(self.uses), "verses": self.verses,
            "source": self.source,
        }


@dataclass
class ManaReading:
    """A moment expressed in one mana: how many of its units, and in words."""
    key: str
    count: float
    unit: str
    description: str

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {"key": self.key, "count": self.count, "unit": self.unit,
                "description": self.description}


@dataclass
class ReckoningPanorama:
    """One Julian Day expressed in all nine manas at once."""
    jd: float
    readings: List[ManaReading]
    details: Dict[str, object]

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {"jd": self.jd,
                "readings": [r.to_dict() for r in self.readings],
                "details": self.details}


@dataclass
class SankrantiEvent:
    """
    The Sun's entry into a sign — SS Ch.14 v.7-11.

    `kind` is "visuvat" at Aries and Libra, "ayana" at Cancer and
    Capricorn, "plain" elsewhere. The punyakala is the auspicious time the
    Sun's disk takes to cross the boundary; `punyakala_each_side_nadis` is
    the half before and again after the entry (v.11).
    """
    sign_index: int
    sign: str
    masa: str
    longitude: float
    jd: float
    kind: str
    tropical_longitude: float
    ayanamsha: float
    punyakala_total_nadis: float
    punyakala_each_side_nadis: float

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return dict(self.__dict__)


@dataclass
class SolarYearStructure:
    """The solar year as one structure — SS Ch.14 v.3-11."""
    year: int
    year_days: float
    sankrantis: List[SankrantiEvent]
    ayanas: Dict[str, object]
    visuvats: Dict[str, object]
    shadasitimukhas: List[dict]
    ritus: List[dict]

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return {
            "year": self.year, "year_days": self.year_days,
            "sankrantis": [e.to_dict() for e in self.sankrantis],
            "ayanas": self.ayanas, "visuvats": self.visuvats,
            "shadasitimukhas": self.shadasitimukhas, "ritus": self.ritus,
        }


@dataclass
class PitryaClock:
    """
    Where a moment falls in the day of the Fathers — SS Ch.14 v.14.

    A lunar month is one day and night of the Fathers: the new moon is
    their midday and the full moon their midnight. `hour` is on their
    24-hour clock, with 12 at midday.
    """
    jd: float
    elongation: float
    hour: float
    ghati: float
    day_fraction: float
    tithi: int
    paksha: str
    phase: str
    next_noon_jd: float
    next_midnight_jd: float

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return dict(self.__dict__)


@dataclass
class BarhaspatyaYear:
    """
    A year of Jupiter's twelve-year cycle — SS Ch.14 v.17.

    `source` is "verse" for the mean method and "commentary" for the
    heliacal one, whose naming rule is a reconstruction.
    """
    jd: float
    method: str
    source: str
    jovian_years_elapsed: int
    name: str
    name_index: int
    asterism: str
    longitude: float
    sixty_year_name: str
    note: str = ""

    def to_dict(self) -> dict:
        """JSON-serializable form, used by the tool and REST layers."""
        return dict(self.__dict__)


def _dms(degrees: float) -> Tuple[int, int, float]:
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = ((degrees - d) * 60 - m) * 60
    return d, m, s
