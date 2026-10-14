"""Tests for Chapter 3: Direction, Place, and Time."""

import math
import pytest
from suryasiddhanta.ch01_mean_motions import (
    julian_day, RASHIS, jd_from_ut, LANKA_MERIDIAN_LONGITUDE,
)
from suryasiddhanta.ch03_direction_place_time import (
    ecliptic_to_equatorial, declination, right_ascension,
    equatorial_to_horizontal,
    gnomon_shadow, solar_altitude_from_shadow,
    sunrise_hour_angle, day_length_ghatis, night_length_ghatis,
    sunrise_sunset_offset,
    OBLIQUITY_DEGREES,
    greenwich_mean_sidereal_time, local_sidereal_time,
    cara, oblique_ascension,
    lagna,
    dik_from_gnomon, latitude_from_noon_shadow,
)


# =====================================================================
#  Declination
# =====================================================================

class TestDeclination:
    def test_zero_at_equinox(self):
        assert abs(declination(0.0)) < 0.01
        assert abs(declination(180.0)) < 0.01

    def test_max_at_90(self):
        dec = declination(90.0)
        assert abs(dec - OBLIQUITY_DEGREES) < 0.01

    def test_min_at_270(self):
        dec = declination(270.0)
        assert abs(dec + OBLIQUITY_DEGREES) < 0.01

    def test_bounded_by_obliquity(self):
        for lon in range(0, 360, 10):
            dec = declination(float(lon))
            assert -OBLIQUITY_DEGREES - 0.01 <= dec <= OBLIQUITY_DEGREES + 0.01

    def test_symmetry(self):
        d1 = declination(30.0)
        d2 = declination(150.0)
        assert abs(d1 - d2) < 0.01


# =====================================================================
#  Right Ascension
# =====================================================================

class TestRightAscension:
    def test_zero_at_zero(self):
        ra = right_ascension(0.0)
        assert abs(ra) < 0.01 or abs(ra - 360) < 0.01

    def test_90_at_90(self):
        ra = right_ascension(90.0)
        assert abs(ra - 90.0) < 0.5

    def test_180_at_180(self):
        ra = right_ascension(180.0)
        assert abs(ra - 180.0) < 0.01

    def test_in_range(self):
        for lon in range(0, 360, 15):
            ra = right_ascension(float(lon))
            assert 0 <= ra < 360


# =====================================================================
#  Ecliptic to Equatorial
# =====================================================================

class TestEclipticToEquatorial:
    def test_zero_lat_returns_valid(self):
        ra, dec = ecliptic_to_equatorial(45.0, 0.0)
        assert 0 <= ra < 360
        assert -90 <= dec <= 90

    def test_with_latitude(self):
        ra, dec = ecliptic_to_equatorial(90.0, 5.0)
        assert 0 <= ra < 360
        assert -90 <= dec <= 90

    def test_ecliptic_pole(self):
        ra, dec = ecliptic_to_equatorial(0.0, 90.0)
        assert abs(dec - (90.0 - OBLIQUITY_DEGREES)) < 0.5

    def test_equinox_zero_lat(self):
        ra, dec = ecliptic_to_equatorial(0.0, 0.0)
        assert abs(ra) < 0.01 or abs(ra - 360) < 0.01
        assert abs(dec) < 0.01


# =====================================================================
#  Equatorial to Horizontal
# =====================================================================

class TestEquatorialToHorizontal:
    def test_returns_valid_range(self):
        az, alt = equatorial_to_horizontal(0.0, 45.0, 0.0, 45.0)
        assert 0 <= az < 360
        assert -90 <= alt <= 90

    def test_transit_altitude(self):
        dec = 20.0
        lat = 30.0
        az, alt = equatorial_to_horizontal(0.0, dec, 0.0, lat)
        expected_alt = 90.0 - lat + dec
        assert abs(alt - expected_alt) < 1.0

    def test_below_horizon(self):
        _, alt = equatorial_to_horizontal(180.0, -60.0, 0.0, 45.0)
        assert alt < 0


# =====================================================================
#  Gnomon Shadow
# =====================================================================

class TestGnomonShadow:
    def test_45_deg_altitude(self):
        result = gnomon_shadow(45.0)
        assert abs(result.shadow_length - 12.0) < 0.01
        assert result.gnomon_length == 12.0

    def test_90_deg_no_shadow(self):
        result = gnomon_shadow(90.0)
        assert abs(result.shadow_length) < 0.01

    def test_below_horizon_infinite(self):
        result = gnomon_shadow(-5.0)
        assert result.shadow_length == float('inf')
        assert "below" in result.direction.lower()

    def test_zero_altitude_infinite(self):
        result = gnomon_shadow(0.0)
        assert result.shadow_length == float('inf')

    def test_low_altitude_long_shadow(self):
        result = gnomon_shadow(10.0)
        assert result.shadow_length > 50

    def test_custom_gnomon(self):
        result = gnomon_shadow(45.0, gnomon_length=6.0)
        assert abs(result.shadow_length - 6.0) < 0.01
        assert result.gnomon_length == 6.0

    def test_str_output(self):
        result = gnomon_shadow(45.0)
        s = str(result)
        assert "Gnomon" in s
        assert "Shadow" in s

    def test_direction_requires_solar_azimuth(self):
        result = gnomon_shadow(45.0)
        assert result.azimuth_deg is None
        assert result.direction == "Undetermined"

    def test_shadow_opposes_solar_azimuth(self):
        result = gnomon_shadow(45.0, sun_azimuth_deg=140.0)
        assert result.azimuth_deg == pytest.approx(320.0)
        assert result.direction == "NW"


# =====================================================================
#  Solar Altitude from Shadow
# =====================================================================

class TestSolarAltitudeFromShadow:
    def test_equal_shadow_gnomon(self):
        alt = solar_altitude_from_shadow(12.0)
        assert abs(alt - 45.0) < 0.01

    def test_zero_shadow(self):
        alt = solar_altitude_from_shadow(0.0)
        assert alt == 90.0

    def test_roundtrip(self):
        for altitude in [10, 30, 45, 60, 80]:
            result = gnomon_shadow(float(altitude))
            if result.shadow_length != float('inf'):
                back = solar_altitude_from_shadow(result.shadow_length)
                assert abs(back - altitude) < 0.1


# =====================================================================
#  Sunrise Hour Angle
# =====================================================================

class TestSunriseHourAngle:
    def test_equinox_at_equator(self):
        H = sunrise_hour_angle(0.0, 0.0)
        assert abs(H - 90.0) < 0.01

    def test_equinox_at_45(self):
        H = sunrise_hour_angle(45.0, 0.0)
        assert abs(H - 90.0) < 0.01

    def test_summer_longer_day(self):
        H_summer = sunrise_hour_angle(45.0, 20.0)
        H_equinox = sunrise_hour_angle(45.0, 0.0)
        assert H_summer > H_equinox

    def test_winter_shorter_day(self):
        H_winter = sunrise_hour_angle(45.0, -20.0)
        H_equinox = sunrise_hour_angle(45.0, 0.0)
        assert H_winter < H_equinox

    def test_midnight_sun(self):
        H = sunrise_hour_angle(70.0, 23.5)
        assert abs(H - 180.0) < 0.1

    def test_polar_night(self):
        H = sunrise_hour_angle(70.0, -23.5)
        assert abs(H) < 0.1


# =====================================================================
#  Day / Night Length
# =====================================================================

class TestDayLength:
    def test_equinox_30_ghatis(self):
        day = day_length_ghatis(23.18, 0.0)
        assert abs(day - 30.0) < 0.1

    def test_summer_longer(self):
        day_summer = day_length_ghatis(23.18, 90.0)
        day_equinox = day_length_ghatis(23.18, 0.0)
        assert day_summer > day_equinox

    def test_winter_shorter(self):
        day_winter = day_length_ghatis(23.18, 270.0)
        day_equinox = day_length_ghatis(23.18, 0.0)
        assert day_winter < day_equinox

    def test_day_plus_night_60(self):
        day = day_length_ghatis(23.18, 45.0)
        night = night_length_ghatis(23.18, 45.0)
        assert abs(day + night - 60.0) < 0.001

    def test_equator_always_30(self):
        for lon in [0, 90, 180, 270]:
            day = day_length_ghatis(0.0, float(lon))
            assert abs(day - 30.0) < 0.01


# =====================================================================
#  Sunrise/Sunset Offset
# =====================================================================

class TestSunriseSunsetOffset:
    def test_equinox_6_hours(self):
        offset = sunrise_sunset_offset(0.0, 0.0)
        assert abs(offset - 6.0) < 0.01

    def test_summer_more_than_6(self):
        offset = sunrise_sunset_offset(45.0, 20.0)
        assert offset > 6.0

    def test_winter_less_than_6(self):
        offset = sunrise_sunset_offset(45.0, -20.0)
        assert offset < 6.0


# =====================================================================
#  Part 2: LST, Cara, Lagna, Dik
# =====================================================================

class TestGMST:
    def test_in_range(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        gmst = greenwich_mean_sidereal_time(jd)
        assert 0 <= gmst < 360

    def test_advances_roughly_1_deg_per_day(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        g1 = greenwich_mean_sidereal_time(jd)
        g2 = greenwich_mean_sidereal_time(jd + 1)
        diff = (g2 - g1) % 360
        assert 0.9 < diff < 1.1

    def test_iau_value_at_j2000_ut(self):
        """The IAU formula gives 280.46061837 deg at J2000.0 UT; a library
        JD is Ujjain mean time, so J2000.0 UT is jd_from_ut(2451545.0)."""
        gmst = greenwich_mean_sidereal_time(jd_from_ut(2451545.0))
        assert gmst == pytest.approx(280.46061837, abs=1e-6)

    @pytest.mark.parametrize("date", [
        (2024, 1, 1), (2024, 4, 1), (2024, 7, 1), (2024, 10, 1),
        (1860, 1, 1), (500, 6, 1),
    ])
    def test_sun_is_on_the_ujjain_meridian_at_ujjain_mean_noon(self, date):
        """
        A library JD is Ujjain mean time, so X.0 is mean noon at Ujjain and
        the Sun's hour angle there is near zero -- off only by the equation
        of time and the text's own error in the Sun's place. Regression:
        when sidereal time read the same JD as UT, it was about 76 deg off.
        """
        from suryasiddhanta.ch02_true_places import (
            OBLIQUITY_DEGREES, sidereal_to_tropical, true_longitude_full,
        )
        jd = julian_day(*date) + 0.5
        lam = math.radians(sidereal_to_tropical(
            true_longitude_full("Sun", jd)["true_longitude"], jd))
        eps = math.radians(OBLIQUITY_DEGREES)
        ra = math.degrees(math.atan2(math.sin(lam) * math.cos(eps),
                                     math.cos(lam))) % 360
        ha = (local_sidereal_time(jd, LANKA_MERIDIAN_LONGITUDE) - ra
              + 180.0) % 360.0 - 180.0
        assert abs(ha) < 6.0


class TestLocalSiderealTime:
    def test_lst_equals_gmst_at_greenwich(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        gmst = greenwich_mean_sidereal_time(jd)
        lst = local_sidereal_time(jd, 0.0)
        assert abs(lst - gmst) < 0.001

    def test_east_is_ahead(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        lst_0 = local_sidereal_time(jd, 0.0)
        lst_90 = local_sidereal_time(jd, 90.0)
        diff = (lst_90 - lst_0) % 360
        assert abs(diff - 90.0) < 0.001

    def test_ujjain(self):
        jd = julian_day(628, 1, 1)
        lst = local_sidereal_time(jd, 75.77)
        assert 0 <= lst < 360

    def test_advances_with_time(self):
        jd = julian_day(2024, 6, 21, gregorian=True)
        lst1 = local_sidereal_time(jd, 75.77)
        lst2 = local_sidereal_time(jd + 0.5, 75.77)
        assert lst1 != lst2


class TestCara:
    def test_zero_at_equator(self):
        c = cara(0.0, 20.0)
        assert abs(c) < 0.01

    def test_zero_at_equinox(self):
        c = cara(45.0, 0.0)
        assert abs(c) < 0.01

    def test_positive_summer_north(self):
        c = cara(23.18, 20.0)
        assert c > 0

    def test_negative_winter_north(self):
        c = cara(23.18, -20.0)
        assert c < 0

    def test_symmetry(self):
        c1 = cara(30.0, 15.0)
        c2 = cara(30.0, -15.0)
        assert abs(c1 + c2) < 0.01

    def test_bounded(self):
        c = cara(60.0, 23.0)
        assert abs(c) < 15


class TestObliqueAscension:
    def test_all_twelve_sum_to_360(self):
        total = sum(oblique_ascension(i, 23.18) for i in range(12))
        assert abs(total - 360.0) < 0.5

    def test_all_positive(self):
        for i in range(12):
            assert oblique_ascension(i, 23.18) > 0

    def test_equator_nearly_equal(self):
        vals = [oblique_ascension(i, 0.0) for i in range(12)]
        for v in vals:
            assert abs(v - 30.0) < 3.0

    def test_latitude_affects_values(self):
        v0 = oblique_ascension(0, 0.0)
        v45 = oblique_ascension(0, 45.0)
        assert v0 != v45


class TestLagna:
    def test_tropical_aries_rises_at_lst_270_then_returns_sidereal_sign(self):
        from suryasiddhanta.ch02_true_places import ayanamsha

        jd = julian_day(2024, 1, 1, gregorian=True)
        observer_lon = (270.0 - greenwich_mean_sidereal_time(jd)) % 360.0
        degree, index, name = lagna(jd, 0.0, observer_lon)
        expected = (-ayanamsha(jd)) % 360.0
        assert degree == pytest.approx(expected, abs=1e-8)
        assert index == int(expected // 30)
        assert name == RASHIS[index]

    def test_interpolates_within_sign_after_horizon_offset(self):
        from suryasiddhanta.ch02_true_places import ayanamsha

        jd = julian_day(2024, 1, 1, gregorian=True)
        half_sign_oa = right_ascension(30.0) / 2.0
        observer_lon = (half_sign_oa - 90.0 - greenwich_mean_sidereal_time(jd)) % 360.0
        degree, _, _ = lagna(jd, 0.0, observer_lon)
        assert degree == pytest.approx((15.0 - ayanamsha(jd)) % 360.0, abs=1e-8)

    def test_returns_valid_range(self):
        jd = julian_day(628, 1, 1)
        deg, idx, name = lagna(jd, 23.18, 75.77)
        assert 0 <= deg < 360
        assert 0 <= idx < 12
        assert name in RASHIS

    def test_changes_with_time(self):
        jd = julian_day(2024, 6, 21, gregorian=True)
        d1, _, _ = lagna(jd, 23.18, 75.77)
        d2, _, _ = lagna(jd + 0.1, 23.18, 75.77)
        assert d1 != d2

    def test_cycles_through_rashis(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        seen = set()
        for hour_frac in range(24):
            _, idx, _ = lagna(jd + hour_frac / 24.0, 23.18, 75.77)
            seen.add(idx)
        assert len(seen) >= 10

    def test_modern_ujjain(self):
        jd = julian_day(2024, 4, 9, gregorian=True)
        deg, idx, name = lagna(jd, 23.18, 75.77)
        assert 0 <= deg < 360
        assert name in RASHIS


class TestDikFromGnomon:
    def test_ew_shadow_gives_ns(self):
        angle, direction = dik_from_gnomon(-5.0, 1.0, 5.0, 1.0,
                                           noon_shadow_direction="north")
        assert 0 <= angle < 360

    def test_returns_cardinal(self):
        _, direction = dik_from_gnomon(-1.0, 1.0, 1.0, 1.0,
                                       noon_shadow_direction="north")
        assert direction in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

    def test_symmetric_tips(self):
        a1, _ = dik_from_gnomon(-3.0, 1.0, 3.0, 1.0, noon_shadow_direction="north")
        a2, _ = dik_from_gnomon(-3.0, 2.0, 3.0, 2.0, noon_shadow_direction="north")
        assert abs(a1 - a2) < 0.01

    def test_south_pointing_noon_shadow_reverses_north(self):
        assert dik_from_gnomon(-3.0, 4.0, 3.0, 4.0,
                               noon_shadow_direction="south") == (180.0, "S")

    def test_needs_physical_reference(self):
        with pytest.raises(TypeError):
            dik_from_gnomon(-3.0, 4.0, 3.0, 4.0)


class TestLatitudeFromNoonShadow:
    def test_equinox_equator(self):
        lat = latitude_from_noon_shadow(0.001, 0.0, shadow_direction="north")
        assert abs(lat) < 1.0

    def test_reasonable_ujjain(self):
        dec = declination(80.0)
        alt = 90.0 - abs(23.18 - dec)
        shadow = 12.0 / math.tan(math.radians(alt))
        recovered = latitude_from_noon_shadow(shadow, 80.0, shadow_direction="north")
        assert abs(recovered - 23.18) < 1.0

    def test_south_pointing_shadow_places_observer_south_of_sun(self):
        shadow = 12.0 * math.tan(math.radians(15.0))
        assert latitude_from_noon_shadow(shadow, 0.0,
                                          shadow_direction="south") == pytest.approx(-15.0)

    def test_direction_is_required(self):
        with pytest.raises(TypeError):
            latitude_from_noon_shadow(3.0, 0.0)


def test_dik_from_gnomon_independent_of_tip_order():
    """
    Validates that the N-S line does not depend on which shadow tip is
    listed first (SS Ch.3 v.1-4: the line through the two tips is E-W).

    Expected: tips at (-3, 4) and (3, 4) give North for both orderings.
    """
    from suryasiddhanta.ch03_direction_place_time import dik_from_gnomon
    a = dik_from_gnomon(-3.0, 4.0, 3.0, 4.0, noon_shadow_direction="north")
    b = dik_from_gnomon(3.0, 4.0, -3.0, 4.0, noon_shadow_direction="north")
    assert a[1] == b[1] == "N"
    assert abs(a[0] - b[0]) < 1e-9
