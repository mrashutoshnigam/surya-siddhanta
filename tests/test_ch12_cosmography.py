"""
Tests for ch12_cosmography — SS Ch.12, Cosmogony, Geography and
Dimensions of the Creation.

The chapter states fixed dimensions rather than time-varying positions,
so most of what is validated here is a derivation chain: three stated
quantities (the earth's diameter, the earth's circumference and the
Moon's orbit) plus Ch.1's revolution counts must reproduce every orbit
the text gives in v.85-89, and must agree with the one Ch.12 figure
already hard-coded elsewhere in the library — the Sun's orbit of
4,331,500 yojanas in ch04_lunar_eclipses.

Where the text states a number as well as a rule, both are checked: the
derived value against the stated value, within the text's own rounding.
"""

import math

import pytest

from suryasiddhanta import ch12_cosmography as ch12
from suryasiddhanta.ch01_mean_motions import (
    KALPA, LANKA_MERIDIAN_LONGITUDE, MEAN_DAILY_MOTION, julian_day, vara,
)

LANKA = LANKA_MERIDIAN_LONGITUDE
from suryasiddhanta.ch04_lunar_eclipses import (
    EARTH_DIAMETER_YOJANA, YOJANA_PER_ARCMIN,
)


# ── The terrestrial sphere (SS i.59-61) ──────────────────────────

def test_earth_circumference_is_root_ten_diameters():
    """
    SS i.59 defines the circumference as the square root of ten times the
    square of the diameter. With a diameter of 1600 yojanas that is
    5059.644, the figure Burgess reports for the equatorial circumference.
    """
    assert ch12.EARTH_DIAMETER_YOJANA == EARTH_DIAMETER_YOJANA == 1600.0
    assert ch12.earth_circumference() == pytest.approx(5059.644, abs=1e-3)
    assert ch12.earth_circumference() == pytest.approx(
        math.sqrt(10.0 * 1600.0 ** 2), rel=1e-12)


def test_corrected_circumference_shrinks_by_the_cosine_of_latitude():
    """
    SS i.60: the corrected circumference is the whole circumference times
    the sine of the co-latitude over radius, that is, times cos(latitude).
    At the equator it is unchanged; at Ujjain it is smaller by cos(23.18);
    at either pole it vanishes.
    """
    whole = ch12.earth_circumference()
    assert ch12.corrected_circumference(0.0) == pytest.approx(whole)
    assert ch12.corrected_circumference(23.18) == pytest.approx(
        whole * math.cos(math.radians(23.18)))
    assert ch12.corrected_circumference(90.0) == pytest.approx(0.0, abs=1e-9)
    # Sign of the latitude must not matter — it is a parallel, not a pole.
    assert ch12.corrected_circumference(-40.0) == pytest.approx(
        ch12.corrected_circumference(40.0))


def test_desantara_yojanas_is_a_fraction_of_the_corrected_circumference():
    """
    SS i.60-61: the difference of longitude in yojanas is that part of the
    place's own parallel lying between it and the prime meridian. A
    quarter turn east of Lanka is a quarter of the equatorial
    circumference; Lanka itself is zero.
    """
    assert ch12.desantara_yojanas(0.0, LANKA) == pytest.approx(0.0)
    assert ch12.desantara_yojanas(0.0, LANKA + 90.0) == pytest.approx(
        ch12.earth_circumference() / 4.0)
    assert ch12.desantara_yojanas(23.18, LANKA + 90.0) == pytest.approx(
        ch12.corrected_circumference(23.18) / 4.0)


def test_desantara_correction_is_subtracted_east_and_added_west():
    """
    SS i.61: the quotient in minutes is subtracted from the mean place
    east of the prime meridian and added west, because a place east of
    the meridian reaches a given midnight earlier. The magnitude is the
    planet's daily motion scaled by the fraction of a turn.
    """
    motion = MEAN_DAILY_MOTION["Moon"] * 60.0   # arcminutes per day
    east = ch12.desantara_correction(motion, 0.0, LANKA + 90.0)
    west = ch12.desantara_correction(motion, 0.0, LANKA - 90.0)
    assert east == pytest.approx(-motion / 4.0)
    assert west == pytest.approx(+motion / 4.0)
    assert ch12.desantara_correction(motion, 23.18, LANKA) == pytest.approx(0.0)


def test_desantara_is_measured_from_ujjain_not_greenwich():
    """
    SS i.62: the prime meridian runs through Lanka and Avanti (Ujjain),
    so by default Ujjain has no difference of longitude and Greenwich,
    75.78 degrees west of it, takes that share of its parallel and has
    the correction added. Regression: the default was once 0 deg E, which
    made Greenwich the prime meridian.
    """
    motion = MEAN_DAILY_MOTION["Moon"] * 60.0
    assert ch12.desantara_yojanas(23.18, 75.78) == pytest.approx(0.0)
    assert ch12.desantara_correction(motion, 23.18, 75.78) == pytest.approx(0.0)
    assert ch12.desantara_yojanas(51.48, 0.0) == pytest.approx(
        ch12.corrected_circumference(51.48) * LANKA / 360.0)
    assert ch12.desantara_correction(motion, 51.48, 0.0) == pytest.approx(
        motion * LANKA / 360.0)


# ── Orbits and distances (SS xii.80-90) ──────────────────────────

def test_ether_orbit_uses_the_moons_revolutions_in_a_kalpa():
    """
    SS xii.81 and xii.90: the orbit of the ether is the Moon's revolutions
    in an Aeon times the Moon's orbit, and the text states the result
    outright as 18,712,080,864,000,000 yojanas. Taking the Moon's
    revolutions per mahayuga instead would give a figure a thousand times
    too small, so this test pins the kalpa.
    """
    assert ch12.ETHER_ORBIT_YOJANAS == 18_712_080_864_000_000


def test_derived_orbits_match_the_orbits_the_text_states():
    """
    SS xii.82 derives every orbit from the ether orbit and the body's
    revolutions in an Aeon; SS xii.85-89 then states the results. The two
    must agree to within the text's own rounding, which is under 1.3
    yojanas in every case — the worst being Mercury's sighrocca, derived
    as 1,043,207.8 against a stated 1,043,209.
    """
    stated = {row["body"]: row["yojanas"]
              for row in ch12.load_catalog()["stated_orbits"]}
    for body, value in stated.items():
        if body == "Ether":
            continue
        assert ch12.orbit_yojanas(body) == pytest.approx(value, abs=2.0), body


def test_sun_orbit_pins_the_constant_already_used_by_chapter_four():
    """
    ch04_lunar_eclipses hard-codes 4,331,500 as the Sun's orbit when it
    turns the Sun's diameter in yojanas into an apparent diameter in
    arcminutes. That number belongs to this chapter, so the derivation
    here must reproduce it or the two chapters have silently diverged.
    """
    assert ch12.orbit_yojanas("Sun") == pytest.approx(4_331_500.0, abs=1.0)


def test_asterism_orbit_is_exactly_sixty_sun_orbits():
    """SS xii.80: the orbit of the asterisms is the Sun's circuit times sixty."""
    assert ch12.orbit_yojanas("Asterisms") == pytest.approx(
        60.0 * ch12.orbit_yojanas("Sun"), rel=1e-12)
    assert ch12.orbit_yojanas("Asterisms") == pytest.approx(259_890_012.0, abs=1.0)


def test_mercury_and_venus_share_the_suns_orbit():
    """
    SS xii.86 gives one orbit for the Sun, Mercury and Venus together:
    in this system the two inner planets have the Sun's mean longitude,
    and only their sighroccas have orbits of their own.
    """
    assert ch12.orbit_yojanas("Mercury") == ch12.orbit_yojanas("Sun")
    assert ch12.orbit_yojanas("Venus") == ch12.orbit_yojanas("Sun")
    assert ch12.orbit_yojanas("Mercury_sighrocca") < ch12.orbit_yojanas("Sun")


def test_daily_linear_motion_is_the_same_for_every_planet():
    """
    SS xii.82: the ether orbit divided by the terrestrial days in an Aeon
    gives the daily eastward motion "of them all" — 11,858.717 yojanas.
    This equality of linear speed is the assumption the whole table of
    orbits is manufactured from.
    """
    assert ch12.daily_linear_motion() == pytest.approx(11_858.717, abs=1e-3)
    assert ch12.daily_linear_motion() == pytest.approx(
        ch12.ETHER_ORBIT_YOJANAS / (1_577_917_828 * 1000), rel=1e-12)


@pytest.mark.parametrize("body", ["Sun", "Moon", "Mars", "Jupiter", "Saturn"])
def test_daily_motion_in_arcminutes_recovers_chapter_one(body):
    """
    SS xii.83 converts the common linear motion back into each planet's
    apparent daily motion: multiply by the Moon's orbit, divide by the
    planet's own, divide by fifteen. The result must reproduce the mean
    daily motions Ch.1 derives from the revolution counts, since both
    descend from the same bhagana.
    """
    expected = MEAN_DAILY_MOTION[body] * 60.0
    assert ch12.daily_motion_arcmin(body) == pytest.approx(expected, rel=1e-6)


def test_the_fifteen_of_verse_eighty_three_is_chapter_fours_yojana_per_arcmin():
    """
    The divisor of SS xii.83 is the same 15 yojanas per arcminute that
    ch04 uses to turn the Moon's diameter into its apparent diameter.
    Stated as a test so the two cannot drift apart.
    """
    assert ch12.YOJANA_PER_ARCMIN == YOJANA_PER_ARCMIN == 15.0


def test_orbit_diameter_and_distance_follow_verse_eighty_four():
    """
    SS xii.84: an orbit times the earth's diameter over the earth's
    circumference is that orbit's diameter; that less the earth's
    diameter, halved, is the planet's distance. Because the circumference
    is the diameter times root ten, the first step is a division by root
    ten, and the Moon accordingly stands about 50,400 yojanas away.
    """
    moon_orbit = ch12.orbit_yojanas("Moon")
    assert ch12.orbit_diameter("Moon") == pytest.approx(
        moon_orbit / math.sqrt(10.0), rel=1e-12)
    assert ch12.mean_distance("Moon") == pytest.approx(
        (ch12.orbit_diameter("Moon") - EARTH_DIAMETER_YOJANA) / 2.0, rel=1e-12)
    assert ch12.mean_distance("Moon") == pytest.approx(50_428.0, abs=1.0)
    # Distance must grow with the orbit, which is the chapter's whole point.
    distances = [ch12.mean_distance(b)
                 for b in ("Moon", "Sun", "Mars", "Jupiter", "Saturn")]
    assert distances == sorted(distances)


def test_all_orbits_is_ordered_and_carries_the_stated_values():
    """
    all_orbits() is what the tool and REST layers serve: one OrbitInfo per
    body, smallest orbit first, each carrying the figure the text states
    and its verse so a caller can cite the source of the number.
    """
    orbits = ch12.all_orbits()
    assert [o.body for o in orbits][0] == "Moon"
    assert [o.orbit_yojanas for o in orbits] == sorted(
        o.orbit_yojanas for o in orbits)
    moon = orbits[0]
    assert moon.stated_yojanas == 324_000
    assert moon.verse == "SS.12.85"
    assert abs(moon.stated_difference) < 2.0
    assert moon.to_dict()["revolutions_per_kalpa"] == 57_753_336_000


def test_unknown_body_raises_key_error():
    """A body the chapter never gives an orbit for must fail loudly."""
    with pytest.raises(KeyError):
        ch12.orbit_yojanas("Pluto")
    with pytest.raises(KeyError):
        ch12.mean_distance("Vidyadhara")


def test_orbital_order_runs_outward_from_the_clouds_to_the_brahma_egg():
    """
    SS xii.29-31 fixes the order of the spheres outward from the earth,
    and that order is what makes the planetary regency of the weekdays
    come out as it does. The seven planets within it must appear in the
    Saturn-downward sequence the regent rules then count along.
    """
    names = [entry["name"] for entry in ch12.orbital_order()]
    assert names[0] == "Clouds"
    assert names[-1] == "Brahma-egg"
    planets = [n for n in names if n in ch12.REGENT_ORDER]
    assert planets == list(reversed(ch12.REGENT_ORDER))


# ── Latitude and the varying day (SS xii.42-72) ──────────────────

def test_yojanas_from_declination_is_a_proportion_of_the_circumference():
    """
    SS xii.59: multiply the earth's circumference by the declination in
    degrees and divide by 360. The round trip through latitude_from_yojanas
    must return the declination unchanged.
    """
    assert ch12.yojanas_from_declination(0.0) == pytest.approx(0.0)
    assert ch12.yojanas_from_declination(360.0) == pytest.approx(
        ch12.earth_circumference())
    assert ch12.latitude_from_yojanas(
        ch12.yojanas_from_declination(24.0)) == pytest.approx(24.0)


def test_polar_day_limit_falls_at_the_arctic_circle_of_the_text():
    """
    SS xii.60-61: subtract from a quarter of the circumference the yojanas
    of the greatest declination; at the remaining distance from the pole
    the day reaches sixty nadis once a year. With the SS obliquity of 24
    degrees that parallel is 90 - 24 = 66 degrees, the text's arctic circle.
    """
    limit = ch12.polar_day_limit()
    assert limit["latitude"] == pytest.approx(66.0)
    assert limit["yojanas_from_pole"] == pytest.approx(
        ch12.yojanas_from_declination(24.0))
    assert limit["yojanas_from_equator"] == pytest.approx(
        ch12.earth_circumference() / 4.0 - ch12.yojanas_from_declination(24.0))


def test_invisibility_limits_give_the_two_and_four_sign_parallels():
    """
    SS xii.63-66: the declination reached at one sign and at two signs of
    longitude fixes two parallels. Beyond the two-sign parallel the sun is
    lost for the two signs beginning with Sagittarius; beyond the one-sign
    parallel, for the four beginning with Scorpio. The higher latitude
    must be the one that loses the sun for longer.
    """
    limits = {entry["signs_invisible"]: entry
              for entry in ch12.invisibility_limits()}
    assert set(limits) == {2, 4}
    assert limits[2]["latitude"] == pytest.approx(69.38, abs=0.05)
    assert limits[4]["latitude"] == pytest.approx(78.26, abs=0.05)
    assert limits[4]["latitude"] > limits[2]["latitude"]
    assert limits[2]["latitude"] > ch12.polar_day_limit()["latitude"]


def test_solar_overhead_band_is_a_fifteenth_of_the_circumference():
    """
    SS xii.68: the sun passes directly overhead across a fifteenth part of
    the earth's circumference on either side, which in degrees is 360/15 —
    exactly the 24 degree obliquity the treatise uses. The band is the
    tropics.
    """
    band = ch12.solar_overhead_band()
    assert band["yojanas"] == pytest.approx(ch12.earth_circumference() / 15.0)
    assert band["degrees"] == pytest.approx(24.0)
    assert band["degrees"] == pytest.approx(ch12.OBLIQUITY_DEGREES)


@pytest.mark.parametrize("latitude,kind", [
    (0.0, "right"), (23.18, "oblique"), (-45.0, "oblique"),
    (90.0, "parallel"), (-90.0, "parallel"),
])
def test_sphere_aspect_names_the_three_situations_of_the_chapter(latitude, kind):
    """
    SS xii.42-44 and 53-56 describe three situations: no latitude, where
    both pole stars lie in the horizon and day and night are thirty nadis
    each; Meru and Vadavamukha, where a pole is overhead; and everything
    between. pole_altitude is the elevation of the pole, which the text
    equates with the latitude.
    """
    aspect = ch12.sphere_aspect(latitude)
    assert aspect["kind"] == kind
    assert aspect["pole_altitude"] == pytest.approx(abs(latitude))
    assert aspect["colatitude"] == pytest.approx(90.0 - abs(latitude))
    if kind == "right":
        assert aspect["day_ghatis"] == pytest.approx(30.0)


def test_cities_clock_reproduces_verse_seventy():
    """
    SS xii.70: when the sun is passing overhead at Bhadrashva it is rising
    in Bharata, midnight in Ketumala and sunset in Kuru. In the cities'
    own names, noon at Yamakoti is 06:00 at Lanka, 00:00 at Romaka and
    18:00 at Siddhapura.
    """
    clock = ch12.cities_clock("Yamakoti", 12.0)
    assert clock["Yamakoti"] == pytest.approx(12.0)
    assert clock["Lanka"] == pytest.approx(6.0)
    assert clock["Romaka"] == pytest.approx(0.0)
    assert clock["Siddhapura"] == pytest.approx(18.0)


def test_cities_clock_rejects_a_place_with_no_longitude():
    """
    Meru and Vadavamukha are the poles; every meridian meets there, so
    they have no local hour and cannot anchor the clock.
    """
    with pytest.raises(ValueError):
        ch12.cities_clock("Meru", 12.0)


def test_reference_places_stand_a_quadrant_apart_on_the_equator():
    """
    SS xii.38-41: the four cities are each a quadrant of the earth's
    circumference from the next, upon the equator, with Meru a further
    quadrant north. Ujjayini is the exception — it carries the prime
    meridian's real latitude (SS i.62).
    """
    places = {p.name: p for p in ch12.reference_places()}
    assert {p.longitude for p in places.values() if p.name in
            ("Lanka", "Yamakoti", "Siddhapura", "Romaka")} == {0.0, 90.0, 180.0, -90.0}
    for name in ("Lanka", "Yamakoti", "Siddhapura", "Romaka"):
        assert places[name].latitude == 0.0
        assert not places[name].is_pole
    assert places["Meru"].is_pole and places["Meru"].latitude == 90.0
    assert places["Vadavamukha"].is_pole and places["Vadavamukha"].latitude == -90.0
    assert places["Ujjayini"].longitude == 0.0


# ── Time and its regents (SS xii.74, 78-79) ──────────────────────

def test_day_lengths_of_the_orders_of_beings():
    """
    SS xii.74: gods and demons see the sun for half a year, the Fathers in
    the moon for half a month, men for their own day. Brahma's day is the
    Aeon of Ch.1. All are returned in days so they can be compared.
    """
    assert ch12.day_of_the_gods() == pytest.approx(365.25868, abs=1e-4)
    assert ch12.day_of_the_manes() == pytest.approx(29.5305, abs=1e-3)
    assert ch12.day_of_brahma() == pytest.approx(KALPA * 365.25868, rel=1e-6)


def test_brahma_day_elapsed_is_a_fraction_between_zero_and_one(jd_2024):
    """
    The Surya Siddhanta places the creation 1,955,880,000 years before the
    Kali epoch, a little under half an Aeon, so any historical date falls
    somewhat past the middle of Brahma's present day.
    """
    elapsed = ch12.brahma_day_elapsed(jd_2024)
    assert 0.0 < elapsed["fraction"] < 1.0
    assert elapsed["fraction"] == pytest.approx(0.4527, abs=1e-3)
    assert elapsed["years_elapsed"] == pytest.approx(1_955_885_125, abs=100)


def test_hora_lords_run_downward_from_saturn():
    """
    SS xii.79 with Burgess's note: the hora is the primitive, each planet
    ruling one in the outward-to-inward order of xii.31. Twenty-four horas
    later the cycle has advanced three places, which is why the day lord is
    "the fourth counting downward from Saturn".
    """
    assert ch12.REGENT_ORDER == [
        "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
    jd = julian_day(2024, 4, 9.0)              # a Tuesday, ruled by Mars
    assert ch12.regent_of_day(jd) == "Mars"
    assert ch12.hora_lord(jd, 0) == "Mars"
    assert ch12.hora_lord(jd, 1) == "Sun"      # one place downward
    assert ch12.hora_lord(jd, 7) == "Mars"     # the cycle closes in seven
    assert ch12.hora_lord(jd, 24) == "Mercury"  # the next day's lord


@pytest.mark.parametrize("offset", range(14))
def test_regent_of_day_agrees_with_chapter_ones_weekday(offset):
    """
    The day regent is nothing other than the lord of the weekday, so it
    must track ch01.vara over a fortnight or the two are inconsistent.
    """
    jd = julian_day(2024, 4, 9.0) + offset
    index, _ = vara(jd)
    assert ch12.regent_of_day(jd) == ch12.WEEKDAY_LORDS[index]


def test_regents_match_burgess_worked_example_for_1860():
    """
    Burgess's note to i.51-52 works Jan 1, 1860 (ahargana from creation
    714,404,108,572): day lord Sun, month lord Saturn, year lord Jupiter.

    Expected: all three lords match, which pins the 30- and 360-day
    periods to the count from creation rather than from the Kali epoch.
    """
    jd = julian_day(1860, 1, 1.0)
    assert ch12.regent_of_day(jd) == "Sun"
    assert ch12.regent_of_month(jd) == "Saturn"
    assert ch12.regent_of_year(jd) == "Jupiter"


def test_month_regent_advances_one_place_upward_every_thirty_civil_days(jd_kali_epoch):
    """
    720 horas per month step backward one place in the seven-lord cycle.

    The creation count stands at 17 (mod 30) on the Kali epoch, so the
    current month began 17 days earlier and the next begins 13 days later.
    Expected: Mars through day 12, then Jupiter, then Saturn a month on.
    """
    assert ch12.regent_of_month(jd_kali_epoch - 17) == "Mars"
    assert ch12.regent_of_month(jd_kali_epoch) == "Mars"
    assert ch12.regent_of_month(jd_kali_epoch + 12.9) == "Mars"
    assert ch12.regent_of_month(jd_kali_epoch + 13) == "Jupiter"
    assert ch12.regent_of_month(jd_kali_epoch + 43) == "Saturn"


def test_year_regent_advances_two_places_every_360_civil_days(jd_kali_epoch):
    """
    8640 horas per year step forward two places in the seven-lord cycle.

    The creation count stands at 347 (mod 360) on the Kali epoch, so the
    next regent year begins 13 days later.
    Expected: Moon until day 12, then Jupiter, then the Sun a year on.
    """
    assert ch12.regent_of_year(jd_kali_epoch - 347) == "Moon"
    assert ch12.regent_of_year(jd_kali_epoch) == "Moon"
    assert ch12.regent_of_year(jd_kali_epoch + 12.9) == "Moon"
    assert ch12.regent_of_year(jd_kali_epoch + 13) == "Jupiter"
    assert ch12.regent_of_year(jd_kali_epoch + 373) == "Sun"


def test_solar_year_start_lands_on_the_suns_entry_into_aries(jd_2024):
    """
    The sidereal new year, distinct from the fixed 360-day regent year,
    is when the Sun's true longitude crosses zero. The start must precede
    the given day by less than a year and put the Sun back at the
    beginning of Aries.
    """
    from suryasiddhanta.ch01_mean_motions import from_julian_day
    from suryasiddhanta.ch02_true_places import compute

    start = ch12.solar_year_start(jd_2024)
    assert 0.0 <= jd_2024 - start < 366.0
    year, month, day, frac = from_julian_day(start)
    lon = compute("Sun", year, month, day + frac).true_longitude
    # The bisection may settle a hair either side of the crossing, so the
    # longitude reads as 0 or as 360 -- the same point of the ecliptic.
    assert min(lon, 360.0 - lon) == pytest.approx(0.0, abs=0.01)


def test_solar_month_start_puts_the_sun_on_a_sign_boundary(jd_2024):
    """
    The month regent is anchored the same way on the sankranti — the Sun's
    entry into a sign — so the start must fall within a month and leave the
    Sun's longitude a multiple of thirty degrees.
    """
    from suryasiddhanta.ch01_mean_motions import from_julian_day
    from suryasiddhanta.ch02_true_places import compute

    start = ch12.solar_month_start(jd_2024)
    assert 0.0 <= jd_2024 - start < 32.0
    year, month, day, frac = from_julian_day(start)
    lon = compute("Sun", year, month, day + frac).true_longitude
    into_sign = lon % 30.0
    assert min(into_sign, 30.0 - into_sign) == pytest.approx(0.0, abs=0.01)


# ── The catalog (SS xii.1-33) ────────────────────────────────────

def test_catalog_loads_with_the_chapters_descriptive_material():
    """
    The JSON catalog carries what cannot be computed: Maya's nine
    inquiries, the creation sequence, the five elements and the seven
    patalas. Verse 33 gives the patalas no names, and the Surya Siddhanta
    has no table of upper lokas at all, so the catalog must not invent
    either.
    """
    catalog = ch12.load_catalog()
    assert catalog["chapter"] == 12
    assert len(catalog["inquiries"]) == 9
    assert len(catalog["elements"]) == 5
    assert catalog["patalas"]["count"] == 7
    assert catalog["patalas"]["named_in_text"] is False
    assert "lokas" not in catalog


def test_every_catalog_entry_cites_a_chapter_twelve_verse():
    """
    Citation safety: each datum must name the verse it came from, in the
    corpus's own SS.<chapter>.<verse> form, so an answer built on this
    catalog can point at its source. A handful of entries legitimately
    cite Ch.1 instead — Ujjayini and Brahma's day.
    """
    catalog = ch12.load_catalog()
    for section in ("inquiries", "creation_sequence", "elements",
                    "planet_origins", "reference_places", "orbital_order",
                    "stated_orbits", "regents", "day_and_night"):
        for entry in catalog[section]:
            assert entry["verse"].startswith("SS."), (section, entry)


def test_creation_sequence_is_contiguous_and_ordered():
    """
    SS xii.13-28 runs from the waters through the golden egg to the whole
    animate creation. The catalog's order field must be a dense sequence
    starting at one so a UI can render it as a numbered chain.
    """
    orders = [entry["order"] for entry in ch12.load_catalog()["creation_sequence"]]
    assert orders == list(range(1, len(orders) + 1))
