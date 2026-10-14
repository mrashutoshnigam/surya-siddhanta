"""
Tests for the planet-wise modules (``suryasiddhanta.planets``).

The planet modules are a facade over the chapter modules: every name in
them is a chapter function with the planet already bound, a chapter
function or constant re-exported as it is, or a constant read from a
chapter table. Nothing is computed there except Ketu's opposite point.
These tests pin that contract: bound wrappers return what the chapter
function returns for that planet, have the chapter function's signature
less the planet parameter, re-exports are the chapter objects themselves,
and each module carries the functions its body needs and no others.
"""

import inspect
import sys

import pytest

from suryasiddhanta import (
    ch01_mean_motions as ch01,
    ch02_true_places as ch02,
    ch04_lunar_eclipses as ch04,
    ch05_solar_eclipses as ch05,
    ch07_conjunctions as ch07,
    ch09_heliacal as ch09,
    ch11_pata as ch11,
    ch12_cosmography as ch12,
    ch13_instruments as ch13,
)
from suryasiddhanta.planets import (
    GRAHAS, jupiter, ketu, mars, mercury, moon, rahu, saturn, sun, venus,
)

TARAGRAHA = [mars, mercury, jupiter, venus, saturn]
ALL_MODULES = [sun, moon, *TARAGRAHA, rahu, ketu]

# Chapter module that owns each generic (planet-taking) function.
BOUND_SOURCE = {
    **{n: ch01 for n in ("mean_longitude", "mandocca_longitude",
                         "sighrocca_longitude", "planet_node_longitude")},
    **{n: ch02 for n in ("corrected_manda_epicycle", "manda_correction",
                         "manda_longitude", "corrected_sighra_epicycle",
                         "sighra_correction", "sighra_karna",
                         "true_longitude_full", "planet_latitude", "compute")},
    **{n: ch07 for n in ("find_conjunction", "planet_planet_conjunction",
                         "nearest_conjunction", "planet_star_conjunction")},
    **{n: ch09 for n in ("sun_elongation", "is_planet_visible",
                         "heliacal_rising", "heliacal_setting",
                         "visibility_events", "next_heliacal")},
    **{n: ch12 for n in ("orbit_yojanas", "daily_motion_arcmin",
                         "orbit_diameter", "mean_distance")},
}

_CH07 = {"find_conjunction", "planet_planet_conjunction",
         "nearest_conjunction", "planet_star_conjunction"}
_CH12 = {"orbit_yojanas", "daily_motion_arcmin", "orbit_diameter",
         "mean_distance"}
_MANDA = {"corrected_manda_epicycle", "manda_correction", "manda_longitude",
          "true_longitude_full", "compute"}

EXPECTED_BOUND = {
    "Sun": {"mean_longitude", "mandocca_longitude"} | _MANDA | _CH07 | _CH12,
    "Moon": ({"mean_longitude", "mandocca_longitude", "planet_latitude"}
             | _MANDA | _CH07 | _CH12),
    "taragraha": set(BOUND_SOURCE),
    "Rahu": set(_CH12),
    "Ketu": set(),
}

JUPITER_EXTRAS = {"samvatsara", "SAMVATSARA_NAMES", "barhaspatya_year",
                  "barhaspatya_cycle", "BARHASPATYA_METHODS"}


def _key(module):
    """The body name as the chapter modules spell it (``Moon_node`` for the nodes)."""
    return getattr(module, "CHAPTER_KEY", module.NAME)


def _bound_names(module):
    """Names in ``__all__`` that are bound wrappers of a chapter function."""
    names = set()
    for name in module.__all__:
        obj = getattr(module, name)
        if (callable(obj) and getattr(obj, "__module__", None) == module.__name__
                and name in BOUND_SOURCE
                and not (module in (rahu, ketu) and name == "mean_longitude")):
            names.add(name)
    return names


def _bound_cases():
    """(module, name) for every bound wrapper in every planet module."""
    return [pytest.param(m, n, id=f"{m.NAME}.{n}")
            for m in ALL_MODULES for n in sorted(_bound_names(m))]


def _sample_args(module, name, jd):
    """Cheap, representative arguments for a bound wrapper (planet excluded)."""
    other = "Saturn" if module is jupiter else "Jupiter"
    return {
        "mean_longitude": (jd,), "mandocca_longitude": (jd,),
        "sighrocca_longitude": (jd,), "planet_node_longitude": (jd,),
        "corrected_manda_epicycle": (37.0,), "corrected_sighra_epicycle": (37.0,),
        "manda_correction": (100.0, 130.0), "manda_longitude": (100.0, 130.0),
        "sighra_correction": (100.0, 250.0), "sighra_karna": (100.0, 250.0),
        "true_longitude_full": (jd,), "planet_latitude": (jd,),
        "compute": (2024, 4, 9),
        "find_conjunction": (other, jd, jd + 30.0),
        "planet_planet_conjunction": (other, 2024, 1, 1),
        "nearest_conjunction": (other, jd, 30.0),
        "planet_star_conjunction": ("Rohini", 2024, 1),
        "sun_elongation": (jd,), "is_planet_visible": (jd, 23.18, 75.77),
        "heliacal_rising": (2024, 23.18, 1), "heliacal_setting": (2024, 23.18, 1),
        "visibility_events": (2024, 2), "next_heliacal": (jd, "rising"),
        "orbit_yojanas": (), "daily_motion_arcmin": (),
        "orbit_diameter": (), "mean_distance": (),
    }[name]


def test_grahas_registry():
    """
    ``GRAHAS`` maps each of the nine graha names to its module, in the
    traditional order, and each module's ``NAME`` matches its key.
    Expected: Sun ... Saturn, Rahu, Ketu; NAME == key for all nine.
    """
    assert list(GRAHAS) == ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                            "Venus", "Saturn", "Rahu", "Ketu"]
    for name, module in GRAHAS.items():
        assert module.NAME == name


@pytest.mark.parametrize("module", ALL_MODULES, ids=lambda m: m.NAME)
def test_all_is_complete_and_public(module):
    """
    Every name in a planet module's ``__all__`` resolves, is public and
    appears once. Expected: no AttributeError, no leading underscore, no
    duplicates.
    """
    assert len(module.__all__) == len(set(module.__all__))
    for name in module.__all__:
        assert not name.startswith("_")
        assert hasattr(module, name)


@pytest.mark.parametrize("module", ALL_MODULES, ids=lambda m: m.NAME)
def test_module_carries_expected_bound_wrappers(module):
    """
    Each body gets exactly the generic functions that apply to it: the Sun
    no sighra, latitude or heliacal forms; the Moon no sighra or heliacal
    forms; the star-planets all of them; Rahu only its orbit; Ketu none.
    Expected: the bound-wrapper set equals the table for that body.
    """
    group = "taragraha" if module in TARAGRAHA else module.NAME
    assert _bound_names(module) == EXPECTED_BOUND[group]


@pytest.mark.parametrize("module,name", _bound_cases())
def test_bound_wrapper_signature_matches_chapter(module, name):
    """
    A bound wrapper has the chapter function's signature with the planet
    parameter removed (and ``planet2`` renamed ``other``): same names,
    order, kinds, defaults and annotations. This catches a wrapper left
    stale by a chapter signature change. Expected: identical parameter
    lists and return annotation.
    """
    source = inspect.signature(getattr(BOUND_SOURCE[name], name))
    wrapper = inspect.signature(getattr(module, name))
    expected = [p.replace(name="other") if p.name == "planet2" else p
                for p in list(source.parameters.values())[1:]]
    assert list(wrapper.parameters.values()) == expected
    assert wrapper.return_annotation == source.return_annotation


@pytest.mark.parametrize("module,name", _bound_cases())
def test_bound_wrapper_delegates_to_chapter(module, name, jd_2024):
    """
    A bound wrapper returns what the chapter function returns when called
    with the body's chapter key. Expected: equal results for representative
    arguments.
    """
    args = _sample_args(module, name, jd_2024)
    source = getattr(BOUND_SOURCE[name], name)
    assert getattr(module, name)(*args) == source(_key(module), *args)


@pytest.mark.parametrize("module", ALL_MODULES, ids=lambda m: m.NAME)
def test_reexports_are_chapter_objects(module):
    """
    Every function a planet module does not define itself is the chapter
    module's own object, not a copy or wrapper. Expected: each such
    callable comes from a chapter module and is that module's attribute.
    """
    for name in module.__all__:
        obj = getattr(module, name)
        if not callable(obj) or obj.__module__ == module.__name__:
            continue
        assert obj.__module__.startswith("suryasiddhanta.ch")
        assert getattr(sys.modules[obj.__module__], obj.__name__) is obj


def test_joint_functions_are_split_body_centric():
    """
    Sun+Moon functions sit where a reader would look: the solar eclipse in
    sun, the lunar eclipse and phases in moon, and the panchanga, patas and
    eclipse projection in both as the same object. Expected: identity with
    the chapter objects and absence where they do not belong.
    """
    assert sun.compute_solar_eclipse is ch05.compute_solar_eclipse
    assert moon.compute_lunar_eclipse is ch04.compute_lunar_eclipse
    assert not hasattr(moon, "compute_solar_eclipse")
    assert not hasattr(sun, "compute_lunar_eclipse")
    assert not hasattr(sun, "phase_name")
    for name in ("tithi_from_elongation", "compute_panchanga", "find_patas",
                 "eclipse_diagram_data"):
        assert getattr(sun, name) is getattr(moon, name)


def test_taragraha_share_one_function_set():
    """
    The five star-planets expose the same functions, Jupiter adding its
    samvatsara and Jovian-cycle functions. Expected: equal callable sets
    once Jupiter's extras are removed.
    """
    def callables(m):
        """Callable public names of a module."""
        return {n for n in m.__all__ if callable(getattr(m, n))}

    reference = callables(mars)
    for module in (mercury, venus, saturn):
        assert callables(module) == reference
    assert callables(jupiter) - JUPITER_EXTRAS == reference
    assert JUPITER_EXTRAS <= set(jupiter.__all__)


@pytest.mark.parametrize("module", [mars, jupiter, saturn], ids=lambda m: m.NAME)
def test_outer_planet_constants(module):
    """
    Constants of Mars, Jupiter and Saturn are the chapter-table entries for
    that planet. Expected: equality with ch01, ch02 and ch09 tables.
    """
    n = module.NAME
    assert module.REVOLUTIONS_PER_MAHAYUGA == ch01.BHAGANA[n]
    assert module.MEAN_DAILY_MOTION == ch01.MEAN_DAILY_MOTION[n]
    assert module.MANDOCCA_REVOLUTIONS_KALPA == ch01.MANDOCCA_REVOLUTIONS_KALPA[n]
    assert module.MANDOCCA_AT_EPOCH == ch01.MANDOCCA_AT_EPOCH[n]
    assert module.NODE_REVOLUTIONS_KALPA == ch01.NODE_REVOLUTIONS_KALPA[n]
    assert module.NODE_AT_EPOCH == ch01.NODE_AT_EPOCH[n]
    assert module.MANDA_EPICYCLE == ch02.MANDA_EPICYCLE[n]
    assert module.SIGHRA_EPICYCLE == ch02.SIGHRA_EPICYCLE[n]
    assert module.MADHYAMA_VIKSHEPA_ARCMIN == ch02.MADHYAMA_VIKSHEPA_ARCMIN[n]
    assert module.VISIBILITY_THRESHOLDS == ch09.VISIBILITY_THRESHOLDS[n]


@pytest.mark.parametrize("module", [mercury, venus], ids=lambda m: m.NAME)
def test_inner_planet_revolutions_are_the_sighrocca(module):
    """
    Mercury's and Venus's own revolutions are carried by the sighrocca
    (their mean place is the Sun's), so they expose SIGHROCCA_* constants
    and no REVOLUTIONS_PER_MAHAYUGA. Expected: the ``<name>_sighrocca``
    table entries, and no misleading plain revolution count.
    """
    key = f"{module.NAME}_sighrocca"
    assert module.SIGHROCCA_REVOLUTIONS_PER_MAHAYUGA == ch01.BHAGANA[key]
    assert module.SIGHROCCA_MEAN_DAILY_MOTION == ch01.MEAN_DAILY_MOTION[key]
    assert not hasattr(module, "REVOLUTIONS_PER_MAHAYUGA")
    assert module.VISIBILITY_THRESHOLDS == ch09.VISIBILITY_THRESHOLDS[module.NAME]


def test_sun_and_moon_constants():
    """
    Sun and Moon constants are their chapter-table entries; the Moon's
    apogee revolutions come from the ``Moon_apogee`` key. Expected:
    equality with ch01 and ch02 tables.
    """
    assert sun.REVOLUTIONS_PER_MAHAYUGA == ch01.BHAGANA["Sun"]
    assert sun.MANDA_EPICYCLE == ch02.MANDA_EPICYCLE["Sun"]
    assert moon.REVOLUTIONS_PER_MAHAYUGA == ch01.BHAGANA["Moon"]
    assert moon.APOGEE_REVOLUTIONS_PER_MAHAYUGA == ch01.BHAGANA["Moon_apogee"]
    assert moon.MADHYAMA_VIKSHEPA_ARCMIN == ch02.MADHYAMA_VIKSHEPA_ARCMIN["Moon"]


def test_rahu_is_the_moons_node(jd_2024, jd_628):
    """
    Rahu's mean longitude is ch01's Moon node, by both of ch01's routes,
    and the node moves retrograde. Expected: equal longitudes and a
    negative mean daily motion.
    """
    for jd in (jd_2024, jd_628):
        assert rahu.mean_longitude(jd) == ch01.moon_node_longitude(jd)
        assert rahu.mean_longitude(jd) == pytest.approx(
            ch01.mean_longitude("Moon_node", jd), abs=1e-9)
    assert rahu.MEAN_DAILY_MOTION < 0
    assert rahu.REVOLUTIONS_PER_MAHAYUGA == ch01.BHAGANA["Moon_node"]


def test_ketu_is_opposite_rahu(jd_2024, jd_628):
    """
    Ketu is the conventional opposite point of Rahu and shares its motion.
    Expected: Ketu = (Rahu + 180) mod 360, in [0, 360), same daily motion.
    """
    for jd in (jd_2024, jd_628):
        k = ketu.mean_longitude(jd)
        assert 0.0 <= k < 360.0
        assert k == pytest.approx((rahu.mean_longitude(jd) + 180.0) % 360.0, abs=1e-9)
    assert ketu.MEAN_DAILY_MOTION == rahu.MEAN_DAILY_MOTION


def test_sun_declination_chapters_agree(jd_2024, jd_628):
    """
    ``sun.sun_declination`` is taken from ch11; ch13 carries its own copy.
    Pin them equal so the choice of source cannot change a result.
    Expected: equal declinations at sample dates across a year.
    """
    assert sun.sun_declination is ch11.sun_declination
    for jd in (jd_628, jd_2024, jd_2024 + 91.0, jd_2024 + 182.0):
        assert ch11.sun_declination(jd) == pytest.approx(ch13.sun_declination(jd), abs=1e-12)
