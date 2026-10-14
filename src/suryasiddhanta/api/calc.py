"""REST wrappers around the Ch.1-14 calculation library and daily_panchanga.

Each route backs one page of the React frontend. Most reuse the same
JSON-string helpers chatbot/tools.py already wraps around the ch0X functions
(json.loads'd here) so the LLM tool path and the REST path share one
implementation; a couple of routes (planet-position, all-planets, stars)
call the ch0X functions directly for the fuller field set the Explorer UI
pages show (DMS, rashi degrees, tropical longitude) that the terser LLM
tool summaries omit.
"""
from __future__ import annotations

import json
from datetime import date as _date
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from suryasiddhanta.chatbot import tools as t

from .schemas import (
    AharganaVerseIn, AllPlanetsIn, ClepsydraIn, ConjunctionsIn, CosmicTimeIn,
    CosmologyIn, DailyPanchangaIn, DailyPanchangaRangeIn, DateIn, EarthDimensionsIn,
    HeliacalIn, InstrumentsCatalogIn, InstrumentTimeIn, LunarEclipseIn, MoonIn,
    PataDetailsIn, PatasIn, PlaceTimeIn, PlanetaryOrbitsIn, PlanetPositionIn,
    SolarEclipseIn, SphereIn, StarsIn,
)

router = APIRouter(prefix="/calc", tags=["calc"])


def _tool(name: str, **kwargs) -> Dict[str, Any]:
    """Call a chatbot/tools.py function and parse its JSON-string result."""
    raw = t.TOOL_FUNCTIONS[name](**kwargs)
    result = json.loads(raw)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


def _is_gregorian(year: int, month: int, day: float) -> bool:
    return (year, month, day) >= (1582, 10, 15)


@router.post("/planet-position")
def planet_position(body: PlanetPositionIn) -> Dict[str, Any]:
    from suryasiddhanta.ch02_true_places import compute, to_dms

    greg = _is_gregorian(body.year, body.month, body.day)
    try:
        pos = compute(body.planet.capitalize(), body.year, body.month,
                      t._lib_day(body.day, body.utc_offset), gregorian=greg)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    d, m, s = to_dms(pos.true_longitude)
    return {
        "planet": pos.planet,
        "true_longitude": pos.true_longitude,
        "true_longitude_dms": f"{d}°{m:02d}′{s:04.1f}″",
        "mean_longitude": pos.mean_lon,
        "tropical_longitude": pos.tropical_longitude,
        "manda_correction": pos.manda_corr,
        "sighra_correction": pos.sighra_corr,
        "ayanamsha": pos.ayanamsha,
        "rashi": pos.rashi,
        "nakshatra": pos.nakshatra,
        "ahargana": pos.ahargana,
    }


@router.post("/all-planets")
def all_planets(body: AllPlanetsIn) -> Dict[str, Any]:
    from suryasiddhanta.ch01_mean_motions import ALL_PLANETS, ahargana, julian_day
    from suryasiddhanta.ch02_true_places import ayanamsha, compute

    greg = _is_gregorian(body.year, body.month, body.day)
    planets = body.planets or ALL_PLANETS
    day = t._lib_day(body.day, body.utc_offset)
    jd = julian_day(body.year, body.month, day, gregorian=greg)

    results = []
    for p in planets:
        try:
            pos = compute(p, body.year, body.month, day, gregorian=greg)
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        results.append({
            "planet": p,
            "true_longitude": pos.true_longitude,
            "mean_longitude": pos.mean_lon,
            "tropical_longitude": pos.tropical_longitude,
            "rashi": pos.rashi,
            "nakshatra": pos.nakshatra,
        })
    return {
        "jd": jd,
        "ahargana": ahargana(jd),
        "ayanamsha": ayanamsha(jd),
        "planets": results,
    }


@router.post("/panchanga")
def panchanga(body: DateIn) -> Dict[str, Any]:
    return _tool("compute_panchanga", year=body.year, month=body.month, day=body.day,
                 utc_offset=body.utc_offset)


@router.post("/eclipse/lunar")
def eclipse_lunar(body: LunarEclipseIn) -> Dict[str, Any]:
    return _tool("compute_lunar_eclipse", year=body.year, month=body.month, day=body.day)


@router.post("/eclipse/solar")
def eclipse_solar(body: SolarEclipseIn) -> Dict[str, Any]:
    return _tool(
        "compute_solar_eclipse", year=body.year, month=body.month, day=body.day,
        latitude=body.latitude, longitude=body.longitude,
    )


@router.post("/conjunctions")
def conjunctions(body: ConjunctionsIn) -> Dict[str, Any]:
    return _tool(
        "find_conjunctions", planet1=body.planet1, planet2=body.planet2,
        year=body.year, month=body.month, months=body.months,
    )


@router.post("/stars")
def stars(body: StarsIn) -> Dict[str, Any]:
    from suryasiddhanta.ch01_mean_motions import julian_day
    from suryasiddhanta.ch08_stars import list_nakshatras, star_position

    info = _tool("get_nakshatra_info", nakshatra_name=body.nakshatra)
    position = _tool(
        "compute_star_position", star_name=body.nakshatra,
        year=body.year, month=body.month, day=body.day, utc_offset=body.utc_offset,
    )
    rise_set = _tool(
        "compute_star_rise_set", star_name=body.nakshatra,
        year=body.year, month=body.month, day=body.day,
        latitude=body.latitude, longitude=body.longitude, utc_offset=body.utc_offset,
    )

    greg = _is_gregorian(body.year, body.month, body.day)
    jd = julian_day(body.year, body.month, t._lib_day(body.day, body.utc_offset), gregorian=greg)
    sky_map = [
        {"name": nm, "right_ascension": sp.right_ascension, "declination": sp.declination_val}
        for nm, sp in ((n, star_position(n, jd)) for n in list_nakshatras())
    ]

    return {"info": info, "position": position, "rise_set": rise_set, "sky_map": sky_map}


@router.post("/heliacal")
def heliacal(body: HeliacalIn) -> Dict[str, Any]:
    return _tool("compute_visibility_events", planet=body.planet, year=body.year, months=body.months)


@router.post("/moon")
def moon(body: MoonIn) -> Dict[str, Any]:
    phase = _tool("compute_moon_phase", year=body.year, month=body.month, day=body.day,
                  utc_offset=body.utc_offset)
    horn = _tool(
        "compute_horn_angle", year=body.year, month=body.month, day=body.day,
        latitude=body.latitude, longitude=body.longitude, utc_offset=body.utc_offset,
    )
    rise_set = _tool(
        "compute_moonrise_moonset", year=body.year, month=body.month, day=body.day,
        latitude=body.latitude, longitude=body.longitude, utc_offset=body.utc_offset,
    )
    return {"phase": phase, "horn": horn, "rise_set": rise_set}


@router.post("/patas")
def patas(body: PatasIn) -> Dict[str, Any]:
    """Patas -- Vyatipata and Vaidhrita -- falling in a date range (SS Ch.11)."""
    return _tool("find_patas", year=body.year, month=body.month,
                 day=body.day, days=body.days, utc_offset=body.utc_offset)


@router.post("/pata/active")
def pata_active(body: PataDetailsIn) -> Dict[str, Any]:
    """The pata in progress at a moment, plus the next one due (SS Ch.11)."""
    return _tool("compute_pata_details", year=body.year, month=body.month,
                 day=body.day, hour=body.hour, utc_offset=body.utc_offset)


@router.post("/cosmography/earth")
def cosmography_earth(body: EarthDimensionsIn) -> Dict[str, Any]:
    """The earth's dimensions and the sky's behaviour at a place (SS Ch.12)."""
    return _tool("get_earth_dimensions",
                 latitude=body.latitude, longitude=body.longitude)


@router.post("/cosmography/orbits")
def cosmography_orbits(body: PlanetaryOrbitsIn) -> Dict[str, Any]:
    """The orbits of the planets in yojanas and their distances (SS Ch.12)."""
    return _tool("get_planetary_orbits", body=body.body)


@router.post("/cosmography/time")
def cosmography_time(body: CosmicTimeIn) -> Dict[str, Any]:
    """The days of the orders of beings and the regents of time (SS Ch.12)."""
    return _tool("get_cosmic_time",
                 year=body.year, month=body.month, day=body.day,
                 utc_offset=body.utc_offset)


@router.post("/cosmography/worlds")
def cosmography_worlds(body: CosmologyIn) -> Dict[str, Any]:
    """The creation, the patalas and the geography of Ch.12 (SS Ch.12)."""
    return _tool("get_cosmology", section=body.section)


@router.post("/instruments/sphere")
def instruments_sphere(body: SphereIn) -> Dict[str, Any]:
    """The armillary sphere with full 3D geometry for drawing (SS Ch.13 v.3-16)."""
    return _tool("get_armillary_sphere", year=body.year, month=body.month,
                 day=body.day, hour=body.hour, latitude=body.latitude,
                 longitude=body.longitude, include_stars=body.include_stars,
                 include_geometry=True, utc_offset=body.utc_offset)


@router.post("/instruments/clepsydra")
def instruments_clepsydra(body: ClepsydraIn) -> Dict[str, Any]:
    """Sinkings, ghatis, day and night, and drift of the water clock (SS Ch.13 v.23)."""
    return _tool("compute_clepsydra", sinkings=body.sinkings, ghatis=body.ghatis,
                 partial=body.partial, year=body.year, month=body.month,
                 day=body.day, latitude=body.latitude,
                 observed_per_day=body.observed_per_day)


@router.post("/instruments/time")
def instruments_time(body: InstrumentTimeIn) -> Dict[str, Any]:
    """Time of day from the gnomon, wheel, arc or staff (SS Ch.13 v.20-24)."""
    return _tool("compute_instrument_time", instrument=body.instrument,
                 value=body.value, year=body.year, month=body.month,
                 day=body.day, latitude=body.latitude, gnomon=body.gnomon,
                 forenoon=body.forenoon, staff_length=body.staff_length)


@router.post("/instruments/catalog")
def instruments_catalog(body: InstrumentsCatalogIn) -> Dict[str, Any]:
    """The instruments, the parts of the sphere and the fixed stars (SS Ch.13)."""
    return _tool("get_instruments", section=body.section)


@router.post("/place-time")
def place_time(body: PlaceTimeIn) -> Dict[str, Any]:
    clock = dict(year=body.year, month=body.month, day=body.day, utc_offset=body.utc_offset)
    ahargana_info = _tool("compute_ahargana", **clock)
    ayanamsha_info = _tool("compute_ayanamsha", **clock)
    day_length = _tool(
        "compute_day_length", year=body.year, month=body.month, day=body.day,
        latitude=body.latitude,
    )
    lagna = _tool(
        "compute_lagna", **clock,
        latitude=body.latitude, longitude=body.longitude,
    )
    from suryasiddhanta.ch03_direction_place_time import gnomon_shadow
    shadow = gnomon_shadow(body.gnomon_altitude)
    return {
        "ahargana": ahargana_info,
        "ayanamsha": ayanamsha_info,
        "day_length": day_length,
        "lagna": lagna,
        "gnomon": {
            "altitude": body.gnomon_altitude,
            "shadow_length": None if shadow.shadow_length == float("inf") else shadow.shadow_length,
        },
    }


@router.post("/ahargana-verse")
def ahargana_verse(body: AharganaVerseIn) -> Dict[str, Any]:
    """The ahargana by the text's own luni-solar route, with every intermediate (SS i.48-51)."""
    return _tool(
        "compute_ahargana_verse_route",
        years=body.years, months=body.months, tithis=body.tithis,
        from_creation=body.from_creation,
    )


@router.post("/daily-panchanga")
def daily_panchanga(body: DailyPanchangaIn) -> Dict[str, Any]:
    from suryasiddhanta.daily_panchanga.core import get_panchanga
    return get_panchanga(body.year, body.month, body.day)


@router.post("/daily-panchanga/range")
def daily_panchanga_range(body: DailyPanchangaRangeIn) -> Dict[str, Any]:
    from suryasiddhanta.daily_panchanga.core import get_panchanga_range
    start = _date(body.year, body.month, body.day)
    return {"days": get_panchanga_range(start, body.days)}
