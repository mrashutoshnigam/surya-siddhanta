"""Coverage audit: every chapter function is reachable from the chatbot.

The chat (and the MCP server, which serves the same registry) can only
compute what `chatbot/tools.py` exposes. This test reads tools.py's imports
and fails when a public function of a `chNN_*` module is neither called by
some tool nor listed below as an internal helper with a reason. Adding a
chapter function therefore forces a decision: give it a tool, or say why
the model never needs it directly.
"""
import ast
import importlib
import inspect
import pkgutil
from pathlib import Path

import suryasiddhanta
from suryasiddhanta.chatbot import tools

#: Reasons shared by many entries.
_VIA_POSITION = "step of compute_planet_position / compute_all_planets"
_MATH = "unit, angle or trigonometry helper"
_VIA_ECLIPSE = "step inside compute_lunar_eclipse / compute_solar_eclipse"
_VIA_DIAGRAM = "step inside compute_eclipse_diagram"
_VIA_SPHERE = "part of get_armillary_sphere's model"
_VIA_INSTRUMENT = "method inside compute_instrument_time"
_VIA_PATA = "step inside find_patas / compute_pata_details"
_VIA_SOLAR_YEAR = "part of compute_solar_year's result"
_TIME = "time-base conversion done at the tool boundary"

INTERNAL_HELPERS = {
    "ch01_mean_motions": {
        "compute_all_mean_positions": _VIA_POSITION,
        "mean_longitude": _VIA_POSITION,
        "mandocca_longitude": _VIA_POSITION,
        "sighrocca_longitude": _VIA_POSITION,
        "moon_node_longitude": _VIA_POSITION,
        "planet_node_longitude": _VIA_POSITION,
        "compute_panchanga": "compute_panchanga tool assembles the same fields itself",
        "karana_from_elongation": "part of compute_panchanga",
        "yoga_from_longitudes": "part of compute_panchanga",
        "rashi_from_longitude": "rashi is returned by the position tools",
        "yuga_elapsed_fraction": "part of compute_ahargana / get_cosmic_time",
        "jd_from_ahargana": _TIME,
        "jd_from_ut": _TIME,
        "jd_to_ut": _TIME,
        "day_to_hms": _TIME,
        "ghati_to_minutes": "covered by convert_time_measure / get_constant",
        "minutes_to_ghati": "covered by convert_time_measure / get_constant",
    },
    "ch02_true_places": {
        **{name: _VIA_POSITION for name in (
            "corrected_manda_epicycle", "corrected_sighra_epicycle", "manda_correction",
            "manda_longitude", "sighra_correction", "sighra_karna", "true_longitude_full",
            "planet_latitude", "spashta_vikshepa", "get_bhuja_koti", "get_quadrant",
            "is_odd_quadrant", "koti")},
        **{name: _MATH for name in (
            "angular_error", "arcjya", "arcmin_to_deg", "arcsec_to_deg", "deg_to_arcmin",
            "deg_to_arcsec", "from_dms", "to_dms", "jya", "jya_normalized", "utkrama_jya",
            "normalize", "normalize_signed", "ss_arcsin", "ss_cos", "ss_sin")},
        "sidereal_to_tropical": "tropical longitude is returned by the position tools",
        "tropical_to_sidereal": "inverse of the above; the model works sidereal",
    },
    "ch03_direction_place_time": {
        "cara": "part of compute_day_length",
        "oblique_ascension": "part of compute_lagna / compute_day_length",
        "sunrise_sunset_offset": "part of compute_day_length",
        "ecliptic_to_equatorial": _MATH,
        "greenwich_mean_sidereal_time": "step inside compute_lagna / compute_gnomon_shadow",
        "dik_from_gnomon": "needs two plotted shadow-tip coordinates; not a chat input",
    },
    "ch04_lunar_eclipses": {
        "apparent_diameter_moon": _VIA_ECLIPSE,
        "apparent_diameter_sun": _VIA_ECLIPSE,
        "check_lunar_eclipse_condition": _VIA_ECLIPSE,
        "earth_shadow_diameter": _VIA_ECLIPSE,
        "is_near_node": _VIA_ECLIPSE,
        "moon_latitude": _VIA_ECLIPSE,
    },
    "ch05_solar_eclipses": {
        "lambana_correction": _VIA_ECLIPSE,
        "lambana_factor": _VIA_ECLIPSE,
        "nati_correction": _VIA_ECLIPSE,
        "nonagesimal": _VIA_ECLIPSE,
    },
    "ch06_eclipse_projection": {
        "aksha_valana": _VIA_DIAGRAM,
        "ayana_valana": _VIA_DIAGRAM,
        "total_valana": _VIA_DIAGRAM,
        "eclipse_contact_points": _VIA_DIAGRAM,
        "project_eclipse_path": _VIA_DIAGRAM,
        "plot_eclipse": "matplotlib rendering, not data",
    },
    "ch07_conjunctions": {
        "angular_separation": "step inside find_conjunctions",
        "classify_conjunction": "step inside find_conjunctions",
        "find_conjunction": "find_conjunctions searches a window with it",
        "longitude_difference": _MATH,
        "nearest_conjunction": "find_conjunctions covers the search",
    },
    "ch08_stars": {
        "list_nakshatras": "list_nakshatras tool reads the catalog directly",
        "load_catalog_json": "catalog loader",
    },
    "ch09_heliacal": {
        "is_planet_visible": "step inside compute_visibility_events",
        "next_heliacal": "step inside compute_heliacal_rising / _setting",
        "sun_elongation": "step inside the heliacal tools",
    },
    "ch11_pata": {
        "ayana_valana": _VIA_PATA,
        "longitude_sum": _VIA_PATA,
        "moon_declination": _VIA_PATA,
        "moon_declination_exact": _VIA_PATA,
        "moon_latitude_deg": _VIA_PATA,
        "sun_declination": _VIA_PATA,
    },
    "ch12_cosmography": {
        "daily_motion_arcmin": "part of get_planetary_orbits",
        "mean_distance": "part of get_planetary_orbits",
        "orbit_diameter": "part of get_planetary_orbits",
        "orbit_yojanas": "part of get_planetary_orbits",
        "latitude_from_yojanas": "part of get_earth_dimensions",
        "yojanas_from_declination": "part of get_earth_dimensions",
        "pole_altitude": "part of get_earth_dimensions",
        "reference_places": "static place list",
        "solar_month_start": "compute_sankranti_punyakala gives sign entries",
        "solar_year_start": "compute_solar_year gives the Aries entry",
        "sun_crossing_jd": "solver behind the Ch.14 sankranti tools",
    },
    "ch13_instruments": {
        **{name: _VIA_SPHERE for name in (
            "cardinal_points", "ecliptic_sign_points", "equatorial_vector", "fixed_star",
            "great_hoops", "horizon_hoop", "meridian_ecliptic_point",
            "orient_ecliptic_point", "solar_diurnal_hoops", "sphere_points", "sphere_sines",
            "star_diurnal_hoops", "star_polar_declination", "sun_declination")},
        **{name: _VIA_INSTRUMENT for name in (
            "cakra_time", "dhanus_time", "nara_yantra_time", "time_from_altitude",
            "yashti_chord", "yashti_time", "chord_of_thirty")},
    },
    "ch14_reckoning_time": {
        "ayanas": _VIA_SOLAR_YEAR,
        "visuvats": _VIA_SOLAR_YEAR,
        "shadasitimukhas": _VIA_SOLAR_YEAR,
        "punyakala_nadis": "part of compute_sankranti_punyakala",
        "manvantara_position": "part of reckon_time",
        "asterism_month": "month_asterisms table is returned by reckon_time",
        "barhaspatya_cycle": "compute_barhaspatya_year answers one date at a time",
        "load_catalog": "catalog loader",
    },
}


def _chapter_modules():
    """Every chNN_* module of the package, imported."""
    root = Path(suryasiddhanta.__file__).parent
    return {m.name: importlib.import_module(f"suryasiddhanta.{m.name}")
            for m in pkgutil.iter_modules([str(root)]) if m.name[:2] == "ch" and m.name[2:4].isdigit()}


def _public_functions(module):
    """Names of functions defined in `module` itself, not imported, not private."""
    return {name for name, obj in vars(module).items()
            if inspect.isfunction(obj) and obj.__module__ == module.__name__
            and not name.startswith("_")}


def _referenced_by_tools():
    """{module: names} that tools.py imports from, or reads as attributes of, a chapter module."""
    tree = ast.parse(Path(tools.__file__).read_text(encoding="utf-8"))
    used, aliases = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("suryasiddhanta.ch"):
                used.setdefault(node.module.split(".")[-1], set()).update(a.name for a in node.names)
            elif node.module == "suryasiddhanta":
                aliases.update({a.asname or a.name: a.name for a in node.names})
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id in aliases):
            used.setdefault(aliases[node.value.id], set()).add(node.attr)
    return used


def test_every_chapter_function_is_reachable_or_explained():
    """
    No chapter function is silently out of the chat's reach.
    Expected: each public chNN function is referenced by tools.py or is in
    INTERNAL_HELPERS; the failure message lists the ones that are neither.
    """
    used = _referenced_by_tools()
    missing = {
        name: sorted(fns - used.get(name, set()) - set(INTERNAL_HELPERS.get(name, {})))
        for name, fns in ((n, _public_functions(m)) for n, m in _chapter_modules().items())
    }
    missing = {k: v for k, v in missing.items() if v}
    assert not missing, f"Give these a tool or add them to INTERNAL_HELPERS: {missing}"


def test_allowlist_has_no_stale_entries():
    """
    The allowlist stays honest: an entry for a function that no longer exists,
    or that a tool now calls, must be removed.
    Expected: every INTERNAL_HELPERS name is a public function not used by tools.py.
    """
    modules, used = _chapter_modules(), _referenced_by_tools()
    stale = {}
    for name, helpers in INTERNAL_HELPERS.items():
        public = _public_functions(modules[name])
        bad = sorted(h for h in helpers if h not in public or h in used.get(name, set()))
        if bad:
            stale[name] = bad
    assert not stale, f"Remove stale INTERNAL_HELPERS entries: {stale}"


def test_every_definition_is_dispatchable():
    """
    The model is never offered a tool the dispatcher cannot run, nor the reverse.
    Expected: TOOL_DEFINITIONS names equal TOOL_FUNCTIONS keys, no duplicates.
    """
    names = [d["name"] for d in tools.TOOL_DEFINITIONS]
    assert len(names) == len(set(names))
    assert set(names) == set(tools.TOOL_FUNCTIONS)
