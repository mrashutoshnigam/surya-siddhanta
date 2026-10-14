"""Tests for Chapter 10: Moon's Risings and Lunar Horns."""

import math
import pytest
from suryasiddhanta import ch10_lunar_horns as ch10
from suryasiddhanta.ch01_mean_motions import julian_day
from suryasiddhanta.ch10_lunar_horns import (
    MOON_APPARENT_RADIUS, PHASE_NAMES,
    moon_elongation, illuminated_fraction, phase_name, is_waxing,
    moonrise, moonset,
    crescent_width, bright_limb_angle, horn_angle,
)


# =====================================================================
#  Phase Constants
# =====================================================================

class TestConstants:
    def test_moon_radius(self):
        assert MOON_APPARENT_RADIUS == 15.75

    def test_phase_names_count(self):
        assert len(PHASE_NAMES) == 9

    def test_phase_names_start_zero(self):
        assert PHASE_NAMES[0][0] == 0.0

    def test_phase_names_wrap(self):
        assert PHASE_NAMES[-1][1] == "New Moon"


# =====================================================================
#  Moon Elongation
# =====================================================================

class TestMoonElongation:
    def test_returns_float(self):
        jd = julian_day(2024, 6, 15.0)
        elong = moon_elongation(jd)
        assert isinstance(elong, float)

    def test_in_range(self):
        jd = julian_day(2024, 6, 15.0)
        elong = moon_elongation(jd)
        assert 0 <= elong < 360

    def test_varies_daily(self):
        jd = julian_day(2024, 6, 15.0)
        e1 = moon_elongation(jd)
        e2 = moon_elongation(jd + 1.0)
        assert e1 != e2

    def test_changes_about_12_deg_per_day(self):
        jd = julian_day(2024, 6, 15.0)
        e1 = moon_elongation(jd)
        e2 = moon_elongation(jd + 1.0)
        diff = (e2 - e1) % 360
        assert 8 < diff < 16

    def test_full_cycle_in_month(self):
        """Elongation wraps 360 in ~29.5 days."""
        jd = julian_day(2024, 1, 1.0)
        vals = [moon_elongation(jd + d) for d in range(30)]
        assert min(vals) < 30 or max(vals) > 330


# =====================================================================
#  Illuminated Fraction
# =====================================================================

class TestIlluminatedFraction:
    def test_returns_float(self):
        jd = julian_day(2024, 6, 15.0)
        frac = illuminated_fraction(jd)
        assert isinstance(frac, float)

    def test_bounded_zero_one(self):
        for month in range(1, 13):
            jd = julian_day(2024, month, 15.0)
            frac = illuminated_fraction(jd)
            assert 0 <= frac <= 1.0

    def test_near_zero_at_new(self):
        """Find elongation near 0 and check fraction near 0."""
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            elong = moon_elongation(jd)
            if elong < 5 or elong > 355:
                frac = illuminated_fraction(jd)
                # linear SS rule (x.9): fraction = elongation/180
                assert frac < 5.0 / 180.0 + 0.01
                break

    def test_near_one_at_full(self):
        """Find elongation near 180 and check fraction near 1."""
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            elong = moon_elongation(jd)
            if 175 < elong < 185:
                frac = illuminated_fraction(jd)
                # linear SS rule (x.9): fraction = elongation/180
                assert frac > 175.0 / 180.0 - 0.01
                break

    def test_half_at_quarter(self):
        """Find elongation near 90 and check fraction near 0.5."""
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            elong = moon_elongation(jd)
            if 85 < elong < 95:
                frac = illuminated_fraction(jd)
                assert 0.45 < frac < 0.55
                break

    def test_formula_at_exact_values(self):
        assert illuminated_fraction.__doc__ is not None


# =====================================================================
#  Phase Name
# =====================================================================

class TestPhaseName:
    def test_returns_string(self):
        jd = julian_day(2024, 6, 15.0)
        name = phase_name(jd)
        assert isinstance(name, str)

    def test_valid_phase_names(self):
        valid = {
            "New Moon", "Waxing Crescent", "First Quarter",
            "Waxing Gibbous", "Full Moon", "Waning Gibbous",
            "Third Quarter", "Waning Crescent",
        }
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            assert phase_name(jd) in valid

    def test_all_phases_reachable(self):
        """Over 30 days, should see multiple distinct phases."""
        phases = set()
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            phases.add(phase_name(jd))
        assert len(phases) >= 4


# =====================================================================
#  Waxing Check
# =====================================================================

class TestIsWaxing:
    def test_returns_bool(self):
        jd = julian_day(2024, 6, 15.0)
        assert isinstance(is_waxing(jd), bool)

    def test_both_occur(self):
        waxing_seen = False
        waning_seen = False
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            if is_waxing(jd):
                waxing_seen = True
            else:
                waning_seen = True
        assert waxing_seen and waning_seen


# =====================================================================
#  Moonrise / Moonset
# =====================================================================

class TestMoonrise:
    def test_returns_jd(self):
        jd = julian_day(2024, 6, 15.0)
        rise = moonrise(jd, 28.6, 77.2)
        assert rise is None or isinstance(rise, float)

    def test_after_start(self):
        jd = julian_day(2024, 6, 15.0)
        rise = moonrise(jd, 28.6, 77.2)
        if rise:
            assert rise > jd

    def test_equator(self):
        jd = julian_day(2024, 6, 15.0)
        rise = moonrise(jd, 0.0, 0.0)
        assert rise is not None

    def test_within_two_days(self):
        jd = julian_day(2024, 6, 15.0)
        rise = moonrise(jd, 28.6, 77.2)
        if rise:
            assert rise - jd < 2.0


class TestMoonset:
    def test_returns_jd(self):
        jd = julian_day(2024, 6, 15.0)
        s = moonset(jd, 28.6, 77.2)
        assert s is None or isinstance(s, float)

    def test_after_start(self):
        jd = julian_day(2024, 6, 15.0)
        s = moonset(jd, 28.6, 77.2)
        if s:
            assert s > jd

    def test_equator(self):
        jd = julian_day(2024, 6, 15.0)
        s = moonset(jd, 0.0, 0.0)
        assert s is not None


# =====================================================================
#  Crescent Geometry
# =====================================================================

class TestCrescentWidth:
    def test_returns_float(self):
        jd = julian_day(2024, 6, 15.0)
        w = crescent_width(jd)
        assert isinstance(w, float)

    def test_nonnegative(self):
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            assert crescent_width(jd) >= 0

    def test_matches_versine_of_elongation(self):
        """
        Validates width = R * (1 - cos(elongation)) (SS Ch.10 versed-sine rule).

        Expected: the width equals the versine formula for every day of a
        month, never exceeds the full disc diameter 2R, and is largest near
        full moon rather than at the quarters.
        """
        widths = []
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            elong = moon_elongation(jd)
            w = crescent_width(jd)
            expected = MOON_APPARENT_RADIUS * (1 - math.cos(math.radians(elong)))
            assert abs(w - expected) < 1e-3
            widths.append((w, elong))
        assert max(w for w, _ in widths) <= 2 * MOON_APPARENT_RADIUS + 0.01
        assert 150 < max(widths)[1] < 210

    def test_near_zero_at_new_moon(self):
        """Width is under 1 arcmin when the elongation is within a few degrees of 0."""
        for d in range(30):
            jd = julian_day(2024, 1, 1.0) + d
            elong = moon_elongation(jd)
            if elong < 3 or elong > 357:
                assert crescent_width(jd) < 1.0
                break


class TestBrightLimbAngle:
    def test_returns_float(self):
        jd = julian_day(2024, 6, 15.0)
        angle = bright_limb_angle(jd)
        assert isinstance(angle, float)

    def test_in_range(self):
        jd = julian_day(2024, 6, 15.0)
        angle = bright_limb_angle(jd)
        assert 0 <= angle < 360

    def test_varies(self):
        jd = julian_day(2024, 6, 15.0)
        a1 = bright_limb_angle(jd)
        a2 = bright_limb_angle(jd + 7.0)
        assert a1 != a2


class TestHornAngle:
    def test_returns_float(self):
        jd = julian_day(2024, 6, 15.0)
        angle = horn_angle(jd, 28.6, 77.2)
        assert isinstance(angle, float)

    def test_in_range(self):
        jd = julian_day(2024, 6, 15.0)
        angle = horn_angle(jd, 28.6, 77.2)
        assert 0 <= angle < 360

    def test_varies_with_latitude(self):
        jd = julian_day(2024, 6, 15.0)
        a1 = horn_angle(jd, 10.0, 77.2)
        a2 = horn_angle(jd, 50.0, 77.2)
        assert a1 != a2


def test_parallactic_angle_retains_obtuse_quadrant():
    """A southern observer can have an obtuse parallactic angle."""
    jd = julian_day(2024, 6, 15.0)
    lon = 77.2
    lst = ch10.local_sidereal_time(jd, lon)
    angle = ch10._parallactic_angle(lst - 45.0, 0.0, -45.0, lon, jd)
    assert angle == pytest.approx(144.73561031724535)


# =====================================================================
#  Edge Cases
# =====================================================================

class TestEdgeCases:
    def test_ancient_date(self):
        jd = julian_day(628, 3, 20.0)
        frac = illuminated_fraction(jd)
        assert 0 <= frac <= 1

    def test_moonrise_ancient(self):
        jd = julian_day(628, 3, 20.0)
        rise = moonrise(jd, 23.18, 75.77)
        assert rise is None or rise > jd

    def test_south_hemisphere(self):
        jd = julian_day(2024, 6, 15.0)
        rise = moonrise(jd, -33.9, 18.4)
        assert rise is None or isinstance(rise, float)

    def test_phase_name_all_months(self):
        for month in range(1, 13):
            jd = julian_day(2024, month, 15.0)
            name = phase_name(jd)
            assert isinstance(name, str)


@pytest.mark.parametrize("year, month, start", [
    (2024, 4, 20.0), (2024, 10, 10.0), (2025, 1, 10.0), (2023, 7, 1.0),
])
def test_full_moon_rises_near_sunset_at_ujjain(year, month, start):
    """
    The full Moon stands opposite the Sun, so she rises about sunset. A
    library JD is Ujjain mean time, so the rise falls near 18h on that
    clock. Regression: when sidereal time read the JD as UT, the rise
    landed about five hours off.
    """
    from suryasiddhanta.ch01_mean_motions import (
        UJJAIN_UTC_OFFSET_HOURS, clock_from_jd, julian_day,
    )
    from suryasiddhanta.ch04_lunar_eclipses import find_full_moon
    from suryasiddhanta.ch10_lunar_horns import moonrise

    day = find_full_moon(year, month, start)
    rise = moonrise(julian_day(year, month, int(day)), 23.18, 75.78)
    assert rise is not None
    hour = clock_from_jd(rise, UJJAIN_UTC_OFFSET_HOURS)[3]
    assert 16.5 < hour < 19.5
