"""Tests for Chapter 4: Lunar Eclipses."""

import math
import pytest
from suryasiddhanta.ch01_mean_motions import julian_day
from suryasiddhanta.ch04_lunar_eclipses import (
    APPARENT_DIAMETER_ARCMIN, MAX_MOON_LATITUDE_ARCMIN, MOON_DAILY_MOTION_DEG,
    apparent_diameter_moon, apparent_diameter_sun, earth_shadow_diameter,
    moon_latitude,
    is_near_node, check_lunar_eclipse_condition,
    find_full_moon,
    compute_lunar_eclipse,
)


# =====================================================================
#  Constants
# =====================================================================

class TestConstants:
    def test_sun_diameter(self):
        assert abs(APPARENT_DIAMETER_ARCMIN["Sun"] - 32.4137) < 0.001  # 32'24".8, SS iv.1 note

    def test_moon_diameter(self):
        assert APPARENT_DIAMETER_ARCMIN["Moon"] == 32.0  # 480 yojanas / 15

    def test_shadow_diameter(self):
        assert abs(APPARENT_DIAMETER_ARCMIN["Shadow"] - 82.5436) < 0.001  # suci rule iv.4-5

    def test_max_latitude(self):
        assert MAX_MOON_LATITUDE_ARCMIN == 270.0

    def test_moon_daily_motion(self):
        assert 13.0 < MOON_DAILY_MOTION_DEG < 13.5


# =====================================================================
#  Apparent Diameters
# =====================================================================

class TestApparentDiameters:
    def test_moon_diameter_near_nominal(self):
        """
        The SS Moon's true motion runs about 12.0-14.4 deg/day against a
        mean of 13.18, so iv.2 keeps her disc within about 29.2'-34.9'.
        Expected: a near-perigee date (15 Jan 2024) falls in that range.
        """
        jd = julian_day(2024, 1, 15, gregorian=True)
        d = apparent_diameter_moon(jd)
        assert 29.0 < d < 35.0

    def test_moon_diameter_varies(self):
        jd1 = julian_day(2024, 1, 15, gregorian=True)
        jd2 = julian_day(2024, 4, 15, gregorian=True)
        d1 = apparent_diameter_moon(jd1)
        d2 = apparent_diameter_moon(jd2)
        assert d1 != d2

    def test_moon_diameter_largest_when_fastest(self):
        """
        SS iv.2 scales the diameter by true motion over mean motion, so over
        a month the largest disc must fall on the fastest day (perigee) and
        the smallest on the slowest (apogee). Expected: both extremes coincide.
        """
        from suryasiddhanta.ch02_true_places import true_longitude_full
        jd0 = julian_day(2024, 3, 20, gregorian=True)
        days = [jd0 + k for k in range(28)]

        def motion(jd):
            return (true_longitude_full("Moon", jd + 0.5)["true_longitude"]
                    - true_longitude_full("Moon", jd - 0.5)["true_longitude"]) % 360.0

        assert max(days, key=apparent_diameter_moon) == max(days, key=motion)
        assert min(days, key=apparent_diameter_moon) == min(days, key=motion)

    def test_moon_diameter_is_true_over_mean_motion(self):
        """
        The corrected diameter is 32' times the true/mean motion ratio
        (iv.2), so it stays within the ratio's range of about 0.9 to 1.1
        and averages to the mean 32' over a month. Expected: mean within 0.3'.
        """
        jd0 = julian_day(2024, 3, 20, gregorian=True)
        values = [apparent_diameter_moon(jd0 + k * 0.25) for k in range(4 * 55)]
        assert all(28.5 < v < 35.5 for v in values)
        assert sum(values) / len(values) == pytest.approx(32.0, abs=0.3)

    def test_sun_diameter_constant(self):
        jd1 = julian_day(2024, 1, 1, gregorian=True)
        jd2 = julian_day(2024, 7, 1, gregorian=True)
        assert apparent_diameter_sun(jd1) == apparent_diameter_sun(jd2) == APPARENT_DIAMETER_ARCMIN["Sun"]

    def test_shadow_diameter_constant(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        assert earth_shadow_diameter(jd) == APPARENT_DIAMETER_ARCMIN["Shadow"]

    def test_shadow_bigger_than_moon(self):
        jd = julian_day(2024, 6, 15, gregorian=True)
        assert earth_shadow_diameter(jd) > apparent_diameter_moon(jd)


# =====================================================================
#  Moon Latitude (Viksepa)
# =====================================================================

class TestMoonLatitude:
    def test_zero_at_node(self):
        lat = moon_latitude(100.0, 100.0)
        assert abs(lat) < 0.01

    def test_zero_at_opposite_node(self):
        lat = moon_latitude(280.0, 100.0)
        assert abs(lat) < 0.01

    def test_max_at_90_from_node(self):
        lat = moon_latitude(190.0, 100.0)
        assert abs(lat - MAX_MOON_LATITUDE_ARCMIN) < 0.01

    def test_min_at_270_from_node(self):
        lat = moon_latitude(10.0, 100.0)
        assert abs(lat + MAX_MOON_LATITUDE_ARCMIN) < 0.01

    def test_bounded(self):
        for angle in range(0, 360, 15):
            lat = moon_latitude(float(angle), 0.0)
            assert -MAX_MOON_LATITUDE_ARCMIN <= lat <= MAX_MOON_LATITUDE_ARCMIN

    def test_antisymmetric(self):
        lat1 = moon_latitude(45.0, 0.0)
        lat2 = moon_latitude(315.0, 0.0)
        assert abs(lat1 + lat2) < 0.01

    def test_max_latitude_is_4_5_deg(self):
        assert abs(MAX_MOON_LATITUDE_ARCMIN / 60.0 - 4.5) < 0.01


# =====================================================================
#  Near Node Check
# =====================================================================

class TestIsNearNode:
    def test_at_node(self):
        assert is_near_node(100.0, 100.0) is True

    def test_at_opposite_node(self):
        assert is_near_node(280.0, 100.0) is True

    def test_far_from_node(self):
        assert is_near_node(145.0, 100.0) is False

    def test_just_inside_tolerance(self):
        assert is_near_node(111.0, 100.0, tolerance_deg=12.0) is True

    def test_just_outside_tolerance(self):
        assert is_near_node(113.0, 100.0, tolerance_deg=12.0) is False

    def test_near_180_from_node(self):
        assert is_near_node(289.0, 100.0, tolerance_deg=12.0) is True


# =====================================================================
#  Full Moon Finder
# =====================================================================

class TestFindFullMoon:
    def test_picks_closer_full_moon_across_new_moon(self):
        # The fixed elongation step can choose March's lunation from Feb 24,
        # although February's full moon is closer in elapsed days.
        assert find_full_moon(2020, 2, 24.0) == pytest.approx(9.54, abs=0.1)

    def test_converges(self):
        from suryasiddhanta.ch02_true_places import compute as c2_compute
        day = find_full_moon(2024, 3, 15.0)
        sun = c2_compute("Sun", 2024, 3, day)
        moon = c2_compute("Moon", 2024, 3, day)
        elongation = (moon.true_longitude - sun.true_longitude) % 360
        assert abs(elongation - 180.0) < 0.5

    def test_returns_float(self):
        day = find_full_moon(628, 1, 15.0)
        assert isinstance(day, float)

    def test_near_input(self):
        day = find_full_moon(2024, 6, 15.0)
        assert -15 < day < 45


# =====================================================================
#  Eclipse Condition Check
# =====================================================================

class TestCheckEclipseCondition:
    def test_returns_tuple(self):
        jd = julian_day(2024, 3, 25, gregorian=True)
        result = check_lunar_eclipse_condition(jd)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_latitude_is_float(self):
        jd = julian_day(2024, 3, 25, gregorian=True)
        _, lat = check_lunar_eclipse_condition(jd)
        assert isinstance(lat, float)


# =====================================================================
#  Compute Lunar Eclipse
# =====================================================================

class TestComputeLunarEclipse:
    def test_requested_month_contains_selected_full_moon(self):
        from suryasiddhanta.ch01_mean_motions import from_julian_day

        result = compute_lunar_eclipse(2020, 2, 24.0)
        year, month, _, _ = from_julian_day(result.jd)
        assert (year, month) == (2020, 2)

    def test_returns_lunar_eclipse(self):
        from suryasiddhanta._types import LunarEclipse
        result = compute_lunar_eclipse(2024, 3, 25.0)
        assert isinstance(result, LunarEclipse)

    def test_eclipse_type_valid(self):
        result = compute_lunar_eclipse(2024, 9, 18.0)
        assert result.eclipse_type in ("none", "partial", "total")

    def test_magnitude_nonnegative(self):
        result = compute_lunar_eclipse(2024, 3, 25.0)
        assert result.magnitude >= 0.0

    def test_magnitude_bounded_when_eclipse(self):
        result = compute_lunar_eclipse(2024, 9, 18.0)
        if result.is_eclipse:
            assert 0.0 < result.magnitude

    def test_no_eclipse_has_none_duration(self):
        result = compute_lunar_eclipse(2024, 3, 25.0)
        if not result.is_eclipse:
            assert result.half_duration is None

    def test_eclipse_has_positive_duration(self):
        result = compute_lunar_eclipse(2024, 9, 18.0)
        if result.is_eclipse:
            assert result.half_duration > 0

    def test_total_eclipse_has_totality(self):
        result = compute_lunar_eclipse(2024, 9, 18.0)
        if result.eclipse_type == "total":
            assert result.totality_half is not None
            assert result.totality_half > 0

    def test_partial_eclipse_no_totality(self):
        result = compute_lunar_eclipse(2024, 3, 25.0)
        if result.eclipse_type == "partial":
            assert result.totality_half is None

    def test_jd_populated(self):
        result = compute_lunar_eclipse(2024, 3, 25.0)
        assert result.jd > 0

    def test_moon_diameter_populated(self):
        result = compute_lunar_eclipse(2024, 3, 25.0)
        assert 29.0 < result.moon_diameter < 34.0

    def test_shadow_diameter_populated(self):
        result = compute_lunar_eclipse(2024, 3, 25.0)
        assert abs(result.shadow_diameter - 82.54) < 0.01

    def test_str_output_no_eclipse(self):
        result = compute_lunar_eclipse(2024, 3, 25.0)
        if not result.is_eclipse:
            s = str(result)
            assert "No lunar eclipse" in s or "latitude" in s.lower()

    def test_str_output_eclipse(self):
        result = compute_lunar_eclipse(2024, 9, 18.0)
        if result.is_eclipse:
            s = str(result)
            assert "Lunar Eclipse" in s or "TOTAL" in s or "PARTIAL" in s

    def test_notes_populated(self):
        result = compute_lunar_eclipse(2024, 9, 18.0)
        assert isinstance(result.notes, str)
        assert len(result.notes) > 0

    def test_628_ce(self):
        result = compute_lunar_eclipse(628, 1, 15.0)
        assert result.eclipse_type in ("none", "partial", "total")

    def test_different_months_vary(self):
        r1 = compute_lunar_eclipse(2024, 3, 25.0)
        r2 = compute_lunar_eclipse(2024, 9, 18.0)
        assert r1.moon_latitude != r2.moon_latitude


# =====================================================================
#  Edge Cases
# =====================================================================

class TestEdgeCases:
    def test_moon_latitude_wraps_correctly(self):
        lat1 = moon_latitude(359.0, 0.0)
        lat2 = moon_latitude(1.0, 0.0)
        assert lat1 < 0
        assert lat2 > 0

    def test_is_near_node_wraps_360(self):
        assert is_near_node(5.0, 355.0, tolerance_deg=12.0) is True

    def test_compute_eclipse_far_future(self):
        result = compute_lunar_eclipse(2100, 6, 15.0)
        assert result.eclipse_type in ("none", "partial", "total")

    def test_compute_eclipse_ancient(self):
        result = compute_lunar_eclipse(500, 6, 15.0)
        assert result.eclipse_type in ("none", "partial", "total")
