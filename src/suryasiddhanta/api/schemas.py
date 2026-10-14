"""Pydantic request models for the /calc/* endpoints.

Kept deliberately thin -- inputs only. Responses are plain dicts built by
the underlying ch0X functions / chatbot/tools.py helpers, so the JSON shape
stays a single source of truth instead of being duplicated into response
models here.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

DEFAULT_LAT = 23.18   # Ujjain -- the SS prime meridian city
DEFAULT_LON = 75.78


class DateIn(BaseModel):
    """A civil date; a fraction of ``day`` is clock time in ``utc_offset``
    (hours from UTC, IST by default). The library reckons in Ujjain mean
    time; the routes convert."""
    year: int
    month: int = 1
    day: float = 1.0
    utc_offset: float = Field(5.5, ge=-12.0, le=14.0)


class DateLocationIn(DateIn):
    latitude: float = DEFAULT_LAT
    longitude: float = DEFAULT_LON


class PlanetPositionIn(DateIn):
    planet: str


class AllPlanetsIn(DateIn):
    planets: Optional[List[str]] = None


class LunarEclipseIn(BaseModel):
    year: int
    month: int
    day: float = 15.0


class SolarEclipseIn(BaseModel):
    year: int
    month: int
    day: float = 1.0
    # Both omitted = geocentric; both given = topocentric at that place.
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=360.0)


class ConjunctionsIn(BaseModel):
    planet1: str
    planet2: str
    year: int
    month: int = 1
    months: int = 12


class StarsIn(DateLocationIn):
    nakshatra: str


class HeliacalIn(BaseModel):
    planet: str
    year: int
    months: int = 12


class MoonIn(DateLocationIn):
    pass


class PlaceTimeIn(DateLocationIn):
    gnomon_altitude: float = 45.0


class AharganaVerseIn(BaseModel):
    """Elapsed time as the ahargana process of SS i.48-51 takes it.

    ``years`` are complete elapsed years, ``months`` the complete
    luni-solar months of the current year and ``tithis`` the complete
    tithis of the current lunar month. All three are reckoned from the
    Kali epoch unless ``from_creation`` is set, in which case they run
    from the end of creation, as Burgess's worked example does.
    """

    years: int
    months: int = 0
    tithis: int = 0
    from_creation: bool = False


class DailyPanchangaIn(BaseModel):
    year: int
    month: int
    day: int


class DailyPanchangaRangeIn(DailyPanchangaIn):
    days: int = 7


class PatasIn(DateIn):
    days: int = 60


class PataDetailsIn(DateIn):
    hour: float = 0.0


class EarthDimensionsIn(BaseModel):
    latitude: float = DEFAULT_LAT
    longitude: float = DEFAULT_LON


class PlanetaryOrbitsIn(BaseModel):
    body: Optional[str] = None


class CosmicTimeIn(DateIn):
    pass


class CosmologyIn(BaseModel):
    section: Optional[str] = None


class SphereIn(DateIn):
    """Armillary sphere for a place and moment (SS Ch.13 v.3-16); `hour` is clock time in `utc_offset`."""
    hour: float = Field(12.0, ge=0.0, le=24.0)
    latitude: float = Field(DEFAULT_LAT, gt=-90.0, lt=90.0)
    longitude: float = Field(DEFAULT_LON, ge=-180.0, le=180.0)
    include_stars: bool = True


class ClepsydraIn(BaseModel):
    """Water-clock arithmetic (SS Ch.13 v.23); supply any of the four inputs."""
    sinkings: Optional[int] = Field(None, ge=0)
    ghatis: Optional[float] = Field(None, ge=0.0)
    partial: float = Field(0.0, ge=0.0, lt=1.0)
    year: Optional[int] = None
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    latitude: float = Field(DEFAULT_LAT, gt=-90.0, lt=90.0)
    observed_per_day: Optional[float] = Field(None, gt=0.0)


class InstrumentTimeIn(DateIn):
    """Time of day from an instrument reading (SS Ch.13 v.20-24)."""
    instrument: Literal["nara", "cakra", "dhanus", "yashti"]
    value: float = Field(..., ge=0.0)
    latitude: float = Field(DEFAULT_LAT, gt=-90.0, lt=90.0)
    gnomon: float = Field(12.0, gt=0.0)
    forenoon: bool = True
    staff_length: float = Field(3438.0, gt=0.0)


class InstrumentsCatalogIn(BaseModel):
    """Descriptive catalog of Ch.13, optionally one section."""
    section: Optional[str] = None


class ChatIn(BaseModel):
    message: str
    session_id: Optional[str] = None


class Ch01In(BaseModel):
    """Date for a Chapter 1 verse-card payload (SS Ch.1 v.11-58).

    Unlike the /calc/* date models this one bounds the year. Every Chapter 1
    figure is O(1) in the date, so wild years are cheap rather than slow --
    the bounds are here to say that a year outside them yields a number with
    no meaning, and they match the range the React date input offers.
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)


class Ch02In(BaseModel):
    """Date and latitude for a Chapter 2 verse-card payload (SS Ch.2).

    Bounded like ``Ch01In`` and for the same reason: every figure is O(1) in
    the date, so the bounds say a wild year has no meaning rather than
    protecting the server. Latitude feeds only the day-length card (v.60-63).
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    latitude: float = Field(23.18, ge=-90.0, le=90.0)


class Ch02ProbeIn(BaseModel):
    """One slider's worth of input for a Chapter 2 card (``/book/chapter/2/probe``).

    ``card`` selects the calculation; the other fields are the inputs that
    card reads. Every field is bounded here, and the route checks that the
    ones its card needs were sent.
    """
    card: Literal["ii.29-30", "ii.31-33", "ii.34-38", "ii.60-63"]
    body: Optional[Literal["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]] = None
    kendra: Optional[float] = Field(None, ge=-3600.0, le=3600.0)
    mode: Optional[str] = Field(None, pattern="^(forward|inverse)$")
    arc_deg: Optional[float] = Field(None, ge=0.0, le=90.0)
    sine: Optional[float] = Field(None, ge=0.0, le=3438.0)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    sun_longitude: Optional[float] = Field(None, ge=-720.0, le=720.0)


class Ch03In(BaseModel):
    """Date and latitude for a Chapter 3 verse-card payload (SS Ch.3).

    Bounded like ``Ch02In``: every figure is O(1) in the date. Latitude seeds
    the shadow, hour-angle, day-length and rising-time cards.
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    latitude: float = Field(23.18, ge=-90.0, le=90.0)


class Ch03ProbeIn(BaseModel):
    """One slider's worth of input for a Chapter 3 card (``/book/chapter/3/probe``).

    ``card`` selects the calculation; the other fields are the inputs that
    card reads, each bounded here. The route checks the ones its card needs
    were sent.
    """
    card: Literal[
        "iii.1-4", "iii.5-8", "iii.13-17", "iii.18-20",
        "iii.21-23", "iii.38-41", "iii.42", "iii.43-44",
    ]
    x1: Optional[float] = Field(None, ge=-1000.0, le=1000.0)
    y1: Optional[float] = Field(None, ge=-1000.0, le=1000.0)
    x2: Optional[float] = Field(None, ge=-1000.0, le=1000.0)
    y2: Optional[float] = Field(None, ge=-1000.0, le=1000.0)
    noon_shadow_direction: Optional[Literal["north", "south"]] = None
    altitude: Optional[float] = Field(None, ge=0.0, le=90.0)
    shadow: Optional[float] = Field(None, ge=0.0, le=10000.0)
    shadow_direction: Optional[Literal["north", "south"]] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    declination: Optional[float] = Field(None, ge=-90.0, le=90.0)
    hour_angle: Optional[float] = Field(None, ge=-360.0, le=360.0)
    longitude: Optional[float] = Field(None, ge=-720.0, le=720.0)
    sun_longitude: Optional[float] = Field(None, ge=-720.0, le=720.0)


class Ch04In(BaseModel):
    """Date for a Chapter 4 verse-card payload (SS Ch.4).

    ``day`` is only the starting guess for the full-moon search, as the
    ``day`` argument of ``compute_lunar_eclipse`` is.
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(15.0, ge=1.0, lt=32.0)


class Ch04ProbeIn(BaseModel):
    """Inputs of the eclipse geometry probe (``/book/chapter/4/probe``).

    The two disk diameters and the Moon's latitude, all in arcminutes. All
    three are required; a missing one is a 422 from the schema itself.
    """
    card: Literal["iv.10-11", "iv.12-13"]
    moon_diameter: float = Field(..., ge=0.0, le=200.0)
    shadow_diameter: float = Field(..., ge=0.0, le=400.0)
    latitude_arcmin: float = Field(..., ge=-600.0, le=600.0)


class Ch05In(BaseModel):
    """Date and place for a Chapter 5 verse-card payload (SS Ch.5).

    ``day`` is only the starting guess for the new-moon search. The place
    defaults to Ujjain, the traditional reference meridian.
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(15.0, ge=1.0, lt=32.0)
    latitude: float = Field(23.18, ge=-66.0, le=66.0)
    longitude: float = Field(75.78, ge=-180.0, le=180.0)


class Ch05ProbeIn(BaseModel):
    """One slider's worth of input for a Chapter 5 card (``/book/chapter/5/probe``).

    ``drkksepa`` (the ecliptic zenith-distance, degrees) feeds the nati card;
    ``interval`` (sun to meridian ecliptic-point, degrees) and ``drggati``
    feed the lambana card. Each route branch checks the fields it needs.
    """
    card: Literal["v.8-9", "v.10-12"]
    drkksepa: Optional[float] = Field(None, ge=-90.0, le=90.0)
    interval: Optional[float] = Field(None, ge=-180.0, le=180.0)


class Ch06In(BaseModel):
    """Eclipse kind, date and place for a Chapter 6 payload (SS Ch.6).

    ``kind`` picks the lunar or the solar construction; ``day`` is the
    starting guess for the full-moon / new-moon search.
    """
    kind: Literal["lunar", "solar"] = "lunar"
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(15.0, ge=1.0, lt=32.0)
    latitude: float = Field(23.18, ge=-66.0, le=66.0)
    longitude: float = Field(75.78, ge=-180.0, le=180.0)


class Ch06ProbeIn(BaseModel):
    """Inputs of the projection probe (``/book/chapter/6/probe``).

    The two disk radii and the latitude of the path, in arcminutes, plus the
    stick the construction lays off: the amount obscured (v.17-19) or nothing
    (v.20-22 uses the half-difference). ``side`` is the end of the path.
    """
    card: Literal["vi.17-19", "vi.20-22"]
    kind: Literal["lunar", "solar"] = "lunar"
    eclipsed_radius: float = Field(..., gt=0.0, le=200.0)
    eclipser_radius: float = Field(..., gt=0.0, le=400.0)
    latitude_arcmin: float = Field(..., ge=-600.0, le=600.0)
    obscured: float = Field(0.0, ge=0.0, le=400.0)
    side: Literal["contact", "separation"] = "contact"


_BODIES = Literal["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


class Ch07In(BaseModel):
    """A pair of bodies and a date for a Chapter 7 verse-card payload (SS Ch.7).

    The conjunction nearest the date is searched within ``search_days`` on
    either side; the scan is daily, so the window bounds the cost.
    """
    planet1: _BODIES = "Mars"
    planet2: _BODIES = "Venus"
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    search_days: float = Field(400.0, ge=10.0, le=3700.0)


_NAKSHATRAS = Literal[
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]


class Ch08In(BaseModel):
    """A star, a date and a place for a Chapter 8 verse-card payload (SS Ch.8).

    ``planet`` and ``months`` feed the planet-star conjunction card, which
    scans daily from 1 January of ``year``.
    """
    star: _NAKSHATRAS = "Rohini"
    planet: Literal["Mars", "Mercury", "Jupiter", "Venus", "Saturn"] = "Jupiter"
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    months: int = Field(12, ge=1, le=36)
    latitude: float = Field(23.18, ge=-90.0, le=90.0)
    longitude: float = Field(75.78, ge=-180.0, le=180.0)


class Ch09In(BaseModel):
    """A planet and a date for a Chapter 9 verse-card payload (SS Ch.9).

    ``months`` bounds the list of heliacal events after the date; the scan is
    daily, so it also bounds the cost. The library ignores the observer's
    place for heliacal events, so none is taken.
    """
    planet: Literal["Mars", "Mercury", "Jupiter", "Venus", "Saturn"] = "Venus"
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    months: int = Field(12, ge=1, le=36)


class Ch10In(BaseModel):
    """A date and a place for a Chapter 10 verse-card payload (SS Ch.10)."""
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    latitude: float = Field(23.18, ge=-90.0, le=90.0)
    longitude: float = Field(75.78, ge=-180.0, le=180.0)


class Ch11In(BaseModel):
    """A date and a search window for a Chapter 11 verse-card payload (SS Ch.11).

    ``days`` bounds how far ahead the pata search looks; the scan is in
    half-day steps, so it also bounds the cost. The library takes no
    observer's place for the patas, so none is asked for.
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    days: int = Field(60, ge=1, le=365)


class Ch12In(BaseModel):
    """A date and a place for a Chapter 12 verse-card payload (SS Ch.12).

    Chapter 12 states fixed dimensions, so the date only moves the regents and
    the Brahma-day card, and the place only the sphere-aspect and earth cards.
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    latitude: float = Field(23.18, ge=-90.0, le=90.0)
    longitude: float = Field(75.78, ge=-180.0, le=180.0)


class Ch13In(BaseModel):
    """A date, a place and a gnomon reading for a Chapter 13 verse-card payload (SS Ch.13).

    The armillary sphere refuses a pole, so the latitude stays strictly inside
    +/-90. ``shadow`` is the gnomon's shadow in the text's twelve-digit units,
    read before noon when ``forenoon`` is true; the other instruments are
    shown the same moment.
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    latitude: float = Field(23.18, gt=-90.0, lt=90.0)
    longitude: float = Field(75.78, ge=-180.0, le=180.0)
    shadow: float = Field(20.0, ge=0.0, le=1000.0)
    forenoon: bool = True


ManaKey = Literal["brahma", "daiva", "pitrya", "prajapatya", "barhaspatya",
                  "saura", "savana", "candra", "naksatra"]


class Ch14In(BaseModel):
    """A date, a conversion and a Jupiter method for a Chapter 14 verse-card payload (SS Ch.14).

    The date's Gregorian year picks the solar year the sankranti and
    shadasitimukha cards describe. ``from_mana`` and ``to_mana`` are the nine
    modes of xiv.1-2, so a typo is refused here. ``heliacal`` asks for
    Jupiter's year by the slower heliacal method as well as the mean one.
    """
    year: int = Field(..., ge=-3000, le=4000)
    month: int = Field(1, ge=1, le=12)
    day: float = Field(1.0, ge=1.0, lt=32.0)
    value: float = Field(1.0, ge=0.0, le=1e15)
    from_mana: ManaKey = "daiva"
    to_mana: ManaKey = "savana"
    heliacal: bool = False
