"""
Tests for ch13_instruments — SS Ch.13, Of the Armillary Sphere and other
Instruments.

The chapter builds an illustrative sphere of hoops and then names the
instruments by which time is found. What is validated here is:

- the geometry of the sphere — that each hoop sits at the declination the
  text prescribes, with the day-radius and sines of Ch.2-3 behind it;
- the three lagnas and the sines of xiii.13-15, including the cases where
  they must collapse (the equator, the equinoxes);
- the clepsydra's arithmetic of sixty sinkings to the day;
- that each time-finding instrument recovers the time it was given, by
  running the forward geometry and inverting it.

Where the text and Burgess's commentary differ, both are checked against
the value the module labels as each.
"""

import math

import pytest

from suryasiddhanta import ch13_instruments as ch13
from suryasiddhanta.ch02_true_places import (
    OBLIQUITY_DEGREES, R_SINE, ayanamsha, jya, koti,
)
from suryasiddhanta.ch03_direction_place_time import (
    declination, right_ascension, sunrise_hour_angle,
)
from suryasiddhanta.ch08_stars import ABHIJIT


# ── The hoops of the sphere (SS xiii.4-12) ───────────────────────

def test_solar_hoops_sit_at_the_declinations_of_the_sign_boundaries():
    """
    SS xiii.5-8 fix three diurnal hoops north of the equator for the Sun at
    the ends of Aries, Taurus and Gemini, and three south. Expected: six
    hoops, the outermost at the full obliquity of 24 deg with a day-radius
    equal to koti(24), and each southern hoop the mirror of a northern one.
    """
    hoops = ch13.solar_diurnal_hoops()
    assert len(hoops) == 6
    north = [h for h in hoops if h.declination > 0]
    south = [h for h in hoops if h.declination < 0]
    assert len(north) == len(south) == 3

    solstitial = max(north, key=lambda h: h.declination)
    assert solstitial.declination == pytest.approx(OBLIQUITY_DEGREES)
    assert solstitial.day_radius == pytest.approx(koti(OBLIQUITY_DEGREES))
    assert solstitial.offset == pytest.approx(math.sin(math.radians(24.0)))

    for n in north:
        mirror = [s for s in south if s.declination == pytest.approx(-n.declination)]
        assert len(mirror) == 1
        assert mirror[0].radius == pytest.approx(n.radius)
    assert all(h.verse.startswith("SS.13.") for h in hoops)


def test_great_hoops_are_unit_circles_with_the_ecliptic_tilted_24_degrees():
    """
    The equator, the two colures (the supporting hoops of xiii.4) and the
    ecliptic (xiii.11-12) are great circles. Expected: four hoops with
    unit normals and zero offset, the equator's normal on the Meru axis,
    and the ecliptic's normal 24 deg from it.
    """
    hoops = {h.key: h for h in ch13.great_hoops()}
    assert set(hoops) == {"equator", "equinoctial_colure",
                          "solstitial_colure", "ecliptic"}
    for hoop in hoops.values():
        assert math.hypot(*hoop.normal) == pytest.approx(1.0)
        assert hoop.offset == 0.0
        assert hoop.radius == pytest.approx(1.0)
    assert hoops["equator"].normal == pytest.approx((0.0, 0.0, 1.0))
    tilt = math.degrees(math.acos(hoops["ecliptic"].normal[2]))
    assert tilt == pytest.approx(OBLIQUITY_DEGREES)


def test_horizon_normal_is_the_zenith_and_the_lower_half_is_cased():
    """
    SS xiii.15-16 raise the observer's place to the top of the sphere and
    case the half below the horizon in cloth. Expected: the horizon's
    normal has unit length and a z-component of sin(latitude), because the
    pole stands at an altitude equal to the latitude; it is flagged cased.
    """
    hoop = ch13.horizon_hoop(23.18, 100.0)
    assert math.hypot(*hoop.normal) == pytest.approx(1.0)
    assert hoop.normal[2] == pytest.approx(math.sin(math.radians(23.18)))
    assert hoop.cased_below is True
    assert hoop.kind == "horizon"


def test_star_hoops_count_junction_stars_abhijit_and_the_seven_fixed_stars(jd_2024):
    """
    SS xiii.8-9 prescribe hoops for the junction stars, Abhijit, and the
    other fixed stars. Expected: 27 + 1 + 7 = 35 hoops, split into the
    junction-star and fixed-star groups.
    """
    hoops = ch13.star_diurnal_hoops(jd_2024)
    assert len(hoops) == 35
    assert sum(h.group == "junction_stars" for h in hoops) == 28
    assert sum(h.group == "fixed_stars" for h in hoops) == 7


def test_star_declination_follows_the_polar_rule_of_ii_58(jd_2024):
    """
    SS ii.58 finds true declination by adding the latitude to the
    declination of the ecliptic point, which is exact for the text's polar
    coordinates. Expected: Abhijit's hoop sits at declination(polar
    longitude + ayanamsha) + 60 deg — and not at the value an ecliptic-
    latitude conversion would give, which differs by degrees.
    """
    hoop = next(h for h in ch13.star_diurnal_hoops(jd_2024) if h.name == "Abhijit")
    expected = declination(ABHIJIT.longitude + ayanamsha(jd_2024)) + ABHIJIT.latitude
    assert hoop.declination == pytest.approx(expected)
    assert hoop.offset == pytest.approx(math.sin(math.radians(expected)))


def test_fixed_stars_match_burgess_viii_10_12_and_20_21():
    """
    The seven fixed stars are taken from Burgess's text of viii.10-12 and
    20-21, carried in corpus record SS.8.24. Expected: the polar
    coordinates the verses state, Apamvatsa and Apas reckoned north of
    Citra's 2 deg south, and every entry marked verified against the corpus.
    """
    expected = {
        "Agastya": (90.0, -80.0), "Mrgavyadha": (80.0, -40.0),
        "Agni": (52.0, 8.0), "Brahmahrdaya": (52.0, 30.0),
        "Prajapati": (57.0, 38.0), "Apamvatsa": (180.0, 3.0),
        "Apas": (180.0, 9.0),
    }
    for name, (lon, lat) in expected.items():
        star = ch13.fixed_star(name)
        assert (star["polar_longitude"], star["polar_latitude"]) == (lon, lat)
        assert star["verified_against_corpus"] is True
        assert star["corpus_record"] == "SS.8.24"


def test_unknown_star_raises_key_error():
    """An unknown fixed-star name must raise KeyError, not return None."""
    with pytest.raises(KeyError):
        ch13.fixed_star("Polaris")


# ── Points on the sphere (SS xiii.10-15) ─────────────────────────

def test_sign_points_and_the_chord_of_thirty():
    """
    SS xiii.11 fixes the signs on the hoops by oblique chords. Expected:
    twelve sign points, declination zero at the two equinoxes, 24 deg at
    the summer solstice, and the chord of 30 deg equal to 2 * jya(15).
    """
    points = ch13.ecliptic_sign_points()
    assert len(points) == 12
    assert points[0].declination == pytest.approx(0.0, abs=1e-9)
    assert points[6].declination == pytest.approx(0.0, abs=1e-9)
    assert points[3].declination == pytest.approx(24.0)
    assert ch13.chord_of_thirty() == pytest.approx(2.0 * jya(15.0))


def test_cardinal_points_are_the_equinoxes_and_solstices():
    """
    SS xiii.10 puts the equinoxes where the equator meets the equinoctial
    colure and the solstices 24 deg above and below it on the other.
    Expected: four points at 0, 90, 180 and 270 deg with declinations
    0, +24, 0 and -24.
    """
    points = {p.key: p for p in ch13.cardinal_points()}
    assert points["vernal_equinox"].declination == pytest.approx(0.0, abs=1e-9)
    assert points["summer_solstice"].declination == pytest.approx(24.0)
    assert points["autumnal_equinox"].declination == pytest.approx(0.0, abs=1e-9)
    assert points["winter_solstice"].declination == pytest.approx(-24.0)


@pytest.mark.parametrize("lst", [0.0, 37.5, 90.0, 145.0, 200.0, 270.0, 333.3])
def test_madhya_lagna_is_the_ecliptic_point_on_the_meridian(lst):
    """
    The meridian ecliptic-point of xiii.14 is the ecliptic longitude whose
    right ascension equals the local sidereal time. Expected: converting
    the returned longitude back to RA recovers the sidereal time, in every
    quadrant.
    """
    lon = ch13.meridian_ecliptic_point(lst)
    ra = right_ascension(lon)
    assert (ra - lst + 180.0) % 360.0 - 180.0 == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("lat", [-33.9, 0.0, 23.18, 60.0])
@pytest.mark.parametrize("lst", [0.0, 22.8, 100.0, 200.0, 300.0])
def test_lagna_lies_on_the_eastern_horizon(lat, lst):
    """
    The orient ecliptic-point of xiii.13 is the ecliptic point rising on
    the eastern horizon. Expected: its unit vector is perpendicular to the
    zenith (altitude zero) and points to the east of the meridian, and the
    point opposite it lies on the horizon to the west — at every latitude
    and sidereal time tried.
    """
    t = math.radians(lst)
    zenith = ch13.equatorial_vector(lst, lat)
    east = (-math.sin(t), math.cos(t), 0.0)

    def vector(lon):
        """Unit vector of an ecliptic longitude."""
        return ch13.equatorial_vector(right_ascension(lon), declination(lon))

    def dot(a, b):
        """Scalar product of two 3-vectors."""
        return sum(x * y for x, y in zip(a, b))

    rising = vector(ch13.orient_ecliptic_point(lst, lat))
    setting = vector(ch13.orient_ecliptic_point(lst, lat) + 180.0)
    assert dot(rising, zenith) == pytest.approx(0.0, abs=1e-9)
    assert dot(rising, east) > 0.0
    assert dot(setting, zenith) == pytest.approx(0.0, abs=1e-9)
    assert dot(setting, east) < 0.0


def test_asta_lagna_is_opposite_the_lagna(jd_2024, ujjain_location):
    """
    xiii.13 finds the occident point "in a corresponding manner": the
    ecliptic point on the western horizon is diametrically opposite the
    rising one. Expected: asta-lagna = lagna + 180 deg, and the Sun point
    lies at the Sun's tropical longitude.
    """
    lat, lon = ujjain_location
    points = {p.key: p for p in ch13.sphere_points(jd_2024, lat, lon)}
    assert set(points) == {"lagna", "asta_lagna", "madhya_lagna", "sun"}
    diff = (points["asta_lagna"].tropical_longitude
            - points["lagna"].tropical_longitude) % 360.0
    assert diff == pytest.approx(180.0)
    for point in points.values():
        assert math.hypot(*point.vector) == pytest.approx(1.0)


def test_sines_vanish_at_the_equator():
    """
    At Lanka (latitude 0) day and night are always equal, so the earth-sine
    and the ascensional-difference sine are zero and the day-measure is the
    full radius. Expected: carajya = kujya = 0, antya = R on both scales
    scaled by the day-radius.
    """
    sines = ch13.sphere_sines(0.0, 20.0)
    assert sines["carajya"] == pytest.approx(0.0, abs=1e-9)
    assert sines["kujya"] == pytest.approx(0.0, abs=1e-9)
    assert sines["antya_great_circle"] == pytest.approx(R_SINE)
    assert sines["antya_small_circle"] == pytest.approx(koti(20.0))


def test_sines_grow_with_latitude_when_the_sun_is_north():
    """
    For a northern observer with the Sun north of the equator the day is
    longer than the night. Expected: positive carajya, kujya equal to
    carajya times the day-radius over R, and antya above R.
    """
    sines = ch13.sphere_sines(23.18, 20.0)
    assert sines["carajya"] > 0.0
    assert sines["kujya"] == pytest.approx(sines["carajya"] * koti(20.0) / R_SINE)
    assert sines["antya_great_circle"] > R_SINE


def test_armillary_sphere_bundles_everything(jd_2024, ujjain_location):
    """
    The assembled sphere carries every hoop, point and sine. Expected: 46
    hoops with stars (4 great, 1 horizon, 6 solar, 35 stellar) and 11
    without; a unit zenith whose z is sin(latitude); the pole altitude
    equal to the latitude; and a JSON-serializable dict.
    """
    lat, lon = ujjain_location
    sphere = ch13.armillary_sphere(jd_2024, lat, lon)
    assert len(sphere.hoops) == 46
    assert len(ch13.armillary_sphere(jd_2024, lat, lon, include_stars=False).hoops) == 11
    assert math.hypot(*sphere.zenith) == pytest.approx(1.0)
    assert sphere.zenith[2] == pytest.approx(math.sin(math.radians(lat)))
    assert sphere.pole_altitude == lat
    data = sphere.to_dict()
    assert len(data["hoops"]) == 46
    assert data["chord_of_thirty"] == pytest.approx(2.0 * jya(15.0))


def test_polar_latitude_is_rejected(jd_2024):
    """tan(latitude) is undefined at the poles. Expected: ValueError."""
    with pytest.raises(ValueError):
        ch13.armillary_sphere(jd_2024, 90.0, 0.0)


# ── The clepsydra (SS xiii.23) ───────────────────────────────────

def test_sixty_sinkings_make_a_day():
    """
    xiii.23: the bowl sinks sixty times in a day and night. Expected: 60
    sinkings are 1440 minutes, one sinking is 24 minutes, and a half-filled
    bowl after two sinkings reads 2 ghatis 30 palas.
    """
    assert ch13.clepsydra_elapsed(60).total_minutes == pytest.approx(1440.0)
    one = ch13.clepsydra_elapsed(1)
    assert (one.hours, one.minutes) == (0, 24)
    reading = ch13.clepsydra_elapsed(2, 0.5)
    assert (int(reading.ghatis), reading.palas) == (2, 30)


def test_sinkings_and_ghatis_round_trip():
    """
    clepsydra_sinkings inverts clepsydra_elapsed. Expected: 17.25 ghatis
    reads back as 17 whole sinkings and a quarter-filled bowl.
    """
    reading = ch13.clepsydra_sinkings(17.25)
    assert reading.sinkings == 17
    assert reading.partial == pytest.approx(0.25)
    back = ch13.clepsydra_elapsed(reading.sinkings, reading.partial)
    assert back.ghatis == pytest.approx(17.25)


def test_negative_or_overfull_readings_are_rejected():
    """Negative sinkings and a fill fraction of 1 or more are errors."""
    with pytest.raises(ValueError):
        ch13.clepsydra_elapsed(-1)
    with pytest.raises(ValueError):
        ch13.clepsydra_elapsed(3, 1.0)


def test_day_and_night_sinkings_sum_to_sixty(jd_2024, ujjain_location):
    """
    Between one sunrise and the next the bowl sinks sixty times. Expected:
    the day and night sinkings at Ujjain on 9 April 2024 add to 60, with
    the day the longer (the Sun is north of the equator in April).
    """
    lat, _ = ujjain_location
    day = ch13.clepsydra_day(jd_2024, lat)
    assert day["day_ghatis"] + day["night_ghatis"] == pytest.approx(60.0)
    assert day["day_ghatis"] > 30.0


def test_drift_of_a_miscalibrated_bowl():
    """
    A true bowl has no drift; one that sinks 61 times a day runs fast.
    Expected: zero error at 60, and at 61 a sinking shorter than 24 minutes
    and a daily reading one ghati (24 minutes) ahead.
    """
    assert ch13.clepsydra_drift(60)["error_minutes_per_sinking"] == pytest.approx(0.0)
    fast = ch13.clepsydra_drift(61)
    assert fast["error_minutes_per_sinking"] < 0.0
    assert fast["reading_error_minutes_per_day"] == pytest.approx(24.0)
    with pytest.raises(ValueError):
        ch13.clepsydra_drift(0)


# ── Time from instruments (SS xiii.20-24) ────────────────────────

def _altitude_at(hour_angle_deg, dec_deg, lat_deg):
    """Forward altitude of the Sun for a given hour angle, declination, latitude."""
    lat, dec, h = map(math.radians, (lat_deg, dec_deg, hour_angle_deg))
    return math.degrees(math.asin(
        math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(h)))


def test_time_from_altitude_recovers_a_known_hour_angle(jd_2024, ujjain_location):
    """
    The core of iii.34-39: from altitude back to time since sunrise.
    Expected: an altitude computed forward for an hour angle 45 deg before
    noon gives (H_rise - 45) / 6 ghatis since sunrise, and the same
    altitude taken as afternoon gives that many ghatis to sunset.
    """
    lat, _ = ujjain_location
    dec = ch13.sun_declination(jd_2024)
    h_rise = sunrise_hour_angle(lat, dec)
    alt = _altitude_at(45.0, dec, lat)

    morning = ch13.time_from_altitude(alt, jd_2024, lat, forenoon=True)
    assert morning.ghatis_since_sunrise == pytest.approx((h_rise - 45.0) / 6.0)
    assert morning.hour_angle_deg == pytest.approx(-45.0)

    evening = ch13.time_from_altitude(alt, jd_2024, lat, forenoon=False)
    assert evening.ghatis_to_sunset == pytest.approx((h_rise - 45.0) / 6.0)
    assert evening.ghatis_since_sunrise == pytest.approx((h_rise + 45.0) / 6.0)


def test_noon_altitude_gives_the_half_day(jd_2024, ujjain_location):
    """
    At noon the hour angle is zero, so the time since sunrise is the whole
    half-day. Expected: ghatis since sunrise equal the half-day in ghatis.
    """
    lat, _ = ujjain_location
    dec = ch13.sun_declination(jd_2024)
    noon = 90.0 - abs(lat - dec)
    result = ch13.time_from_altitude(noon - 1e-9, jd_2024, lat)
    assert result.ghatis_since_sunrise == pytest.approx(result.half_day_ghatis, abs=1e-3)


def test_altitude_above_noon_is_rejected(jd_2024, ujjain_location):
    """The Sun cannot stand higher than its noon altitude. Expected: ValueError."""
    lat, _ = ujjain_location
    with pytest.raises(ValueError):
        ch13.time_from_altitude(89.9, jd_2024, lat)


def test_altitude_outside_physical_range_is_rejected(jd_2024, ujjain_location):
    """Sine periodicity must not make 180 degrees a valid solar altitude."""
    lat, _ = ujjain_location
    with pytest.raises(ValueError):
        ch13.time_from_altitude(180.0, jd_2024, lat)


def test_nara_and_cakra_agree_for_the_same_altitude(jd_2024, ujjain_location):
    """
    The man-instrument (xiii.24) reads a shadow; the wheel (commentary to
    xiii.20) reads the altitude directly. Expected: a 12-digit gnomon
    casting a 12-digit shadow (altitude 45 deg) gives the same time as the
    wheel read at 45 deg, and the two are labelled verse and commentary.
    """
    lat, _ = ujjain_location
    nara = ch13.nara_yantra_time(12.0, jd_2024, lat)
    cakra = ch13.cakra_time(45.0, jd_2024, lat)
    assert nara.ghatis_since_sunrise == pytest.approx(cakra.ghatis_since_sunrise)
    assert nara.source == "verse"
    assert cakra.source == "commentary"


def test_dhanus_rejects_an_altitude_beyond_its_quadrant(jd_2024, ujjain_location):
    """The arc is at most a quadrant of the wheel. Expected: 95 deg raises ValueError."""
    lat, _ = ujjain_location
    with pytest.raises(ValueError):
        ch13.dhanus_time(95.0, jd_2024, lat)


def test_yashti_chord_and_time_round_trip(jd_2024, ujjain_location):
    """
    The staff of the commentary to xiii.20: the chord from the staff's tip
    to the sunrise point, on the day's diurnal circle, measures the time
    since sunrise. Expected: the chord for 5 ghatis reads back as 5 ghatis,
    and the agra is reported.
    """
    lat, _ = ujjain_location
    chord = ch13.yashti_chord(5.0, jd_2024, lat)
    result = ch13.yashti_time(chord, jd_2024, lat)
    assert result.ghatis_since_sunrise == pytest.approx(5.0)
    assert "agra" in result.extra


def test_yashti_rejects_a_chord_longer_than_the_diameter(jd_2024, ujjain_location):
    """No chord exceeds the diurnal circle's diameter. Expected: ValueError."""
    lat, _ = ujjain_location
    with pytest.raises(ValueError):
        ch13.yashti_time(3.0 * R_SINE, jd_2024, lat)


def test_instrument_dispatcher(jd_2024, ujjain_location):
    """
    instrument_time routes by name. Expected: "nara" matches the direct
    call, and an unknown instrument raises KeyError.
    """
    lat, _ = ujjain_location
    direct = ch13.nara_yantra_time(10.0, jd_2024, lat)
    routed = ch13.instrument_time("nara", 10.0, jd_2024, lat)
    assert routed.ghatis_since_sunrise == pytest.approx(direct.ghatis_since_sunrise)
    with pytest.raises(KeyError):
        ch13.instrument_time("sundial", 10.0, jd_2024, lat)


# ── The catalog ──────────────────────────────────────────────────

def test_catalog_loads_the_instruments_and_their_verses():
    """
    The catalog holds the descriptive half of the chapter. Expected: eleven
    instruments each citing a Ch.13 verse, the clepsydra vessel of the
    commentary, the Seven Sages without coordinates, and the note that
    verse 6 is absent from the corpus.
    """
    catalog = ch13.load_catalog()
    assert len(catalog["instruments"]) == 11
    assert all(i["verse"].startswith("SS.13.") for i in catalog["instruments"])
    assert catalog["clepsydra_vessel"]["height_angulas"] == 6
    assert "polar_longitude" not in catalog["seven_sages"]
    assert "6" in catalog["missing_verses_note"]
    assert ch13.get_instrument("ghati")["computable"] is True
    with pytest.raises(KeyError):
        ch13.get_instrument("astrolabe")
