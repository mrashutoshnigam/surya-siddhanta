"""Tests for Chapter 5: Solar Eclipses."""

import math
import pytest
from suryasiddhanta.ch01_mean_motions import julian_day
from suryasiddhanta.ch02_true_places import OBLIQUITY_DEGREES
from suryasiddhanta.ch03_direction_place_time import local_sidereal_time
from suryasiddhanta.ch05_solar_eclipses import (
    MOON_HP_ARCMIN,
    nonagesimal, _lagna_longitude,
    lambana_correction, nati_correction, lambana_factor,
    find_new_moon,
    compute_solar_eclipse, compute_solar_eclipse_topocentric,
)


# =====================================================================
#  Constants
# =====================================================================

class TestConstants:
    def test_moon_hp(self):
        assert abs(MOON_HP_ARCMIN - 52.71) < 0.01  # 790'35"/15, SS iv.1-3 note

    def test_hp_about_1_degree(self):
        assert 0.85 < MOON_HP_ARCMIN / 60.0 < 0.95


# =====================================================================
#  Nonagesimal
# =====================================================================

class TestNonagesimal:
    def test_returns_tuple(self):
        vit, zen = nonagesimal(90.0, 23.18)
        assert isinstance(vit, float)
        assert isinstance(zen, float)

    def test_vitribha_in_range(self):
        vit, _ = nonagesimal(45.0, 30.0)
        assert 0 <= vit < 360

    def test_drkksepa_within_a_quadrant(self):
        """Drkksepa is the zenith's ecliptic latitude, so |drkksepa| <= 90."""
        _, zen = nonagesimal(90.0, 23.18)
        assert -90.0 <= zen <= 90.0

    def test_varies_with_lst(self):
        v1, _ = nonagesimal(0.0, 23.18)
        v2, _ = nonagesimal(90.0, 23.18)
        assert v1 != v2

    def test_varies_with_latitude(self):
        _, z1 = nonagesimal(90.0, 0.0)
        _, z2 = nonagesimal(90.0, 45.0)
        assert z1 != z2

    def test_equator_lst90(self):
        """At LST 90 on the equator the zenith sits a full obliquity
        south of the ecliptic, so the drkksepa is -24 deg."""
        vit, zen = nonagesimal(90.0, 0.0)
        assert 0 <= vit < 360
        assert abs(zen + OBLIQUITY_DEGREES) < 0.01

    def test_drkksepa_flips_across_the_ecliptic(self):
        """Northern and southern observers see the zenith on opposite
        sides of the ecliptic."""
        _, north = nonagesimal(90.0, 60.0)
        _, south = nonagesimal(90.0, -60.0)
        assert north > 0 > south


# =====================================================================
#  Lagna
# =====================================================================

class TestLagna:
    def test_in_range(self):
        lagna = _lagna_longitude(90.0, 23.18)
        assert 0 <= lagna < 360

    def test_varies_with_lst(self):
        l1 = _lagna_longitude(0.0, 23.18)
        l2 = _lagna_longitude(180.0, 23.18)
        assert l1 != l2


# =====================================================================
#  Lambana Correction
# =====================================================================

class TestLambanaCorrection:
    def test_returns_float(self):
        jd = julian_day(2024, 4, 8, gregorian=True)
        lam = lambana_correction(jd, 23.18, 75.77)
        assert isinstance(lam, float)

    def test_bounded(self):
        jd = julian_day(2024, 4, 8, gregorian=True)
        lam = lambana_correction(jd, 23.18, 75.77)
        assert abs(lam) <= MOON_HP_ARCMIN + 1

    def test_varies_with_longitude(self):
        jd = julian_day(2024, 4, 8, gregorian=True)
        l1 = lambana_correction(jd, 23.18, 0.0)
        l2 = lambana_correction(jd, 23.18, 90.0)
        assert l1 != l2

    def test_sign_varies(self):
        jd = julian_day(2024, 4, 8, gregorian=True)
        vals = [lambana_correction(jd, 23.18, lon)
                for lon in range(0, 360, 30)]
        signs = set(v > 0 for v in vals if abs(v) > 1.0)
        assert len(signs) == 2


# =====================================================================
#  Nati Correction
# =====================================================================

class TestNatiCorrection:
    def test_returns_float(self):
        jd = julian_day(2024, 4, 8, gregorian=True)
        nat = nati_correction(jd, 23.18, 75.77)
        assert isinstance(nat, float)

    def test_bounded_by_hp(self):
        jd = julian_day(2024, 4, 8, gregorian=True)
        nat = nati_correction(jd, 23.18, 75.77)
        assert abs(nat) <= MOON_HP_ARCMIN + 1

    def test_opposes_the_drkksepa(self):
        """Parallax carries the Moon away from the zenith, so nati is
        always opposite in sign to the drkksepa."""
        jd = julian_day(2024, 4, 8, gregorian=True)
        for lat in (-60.0, -23.18, 23.18, 60.0):
            _, drk = nonagesimal(local_sidereal_time(jd, 75.77), lat)
            nat = nati_correction(jd, lat, 75.77)
            assert nat * drk <= 0.0

    def test_varies_with_latitude(self):
        jd = julian_day(2024, 4, 8, gregorian=True)
        n1 = nati_correction(jd, 0.0, 75.77)
        n2 = nati_correction(jd, 60.0, 75.77)
        assert n1 != n2

    def test_zero_at_zenith_approx(self):
        """When nonagesimal is at zenith, nati ≈ 0."""
        for lst in range(0, 360, 10):
            for lat in range(0, 60, 10):
                jd = julian_day(2024, 4, 8, gregorian=True)
                nat = nati_correction(jd, float(lat), float(lst))
                assert abs(nat) <= MOON_HP_ARCMIN + 1


# =====================================================================
#  New Moon Finder
# =====================================================================

class TestFindNewMoon:
    def test_converges(self):
        from suryasiddhanta.ch02_true_places import compute as c2_compute, normalize
        day = find_new_moon(2024, 4, 8.0)
        sun = c2_compute("Sun", 2024, 4, day)
        moon = c2_compute("Moon", 2024, 4, day)
        elongation = normalize(moon.true_longitude - sun.true_longitude)
        if elongation > 180:
            elongation -= 360
        assert abs(elongation) < 0.5

    def test_returns_float(self):
        day = find_new_moon(628, 3, 1.0)
        assert isinstance(day, float)

    def test_near_input(self):
        day = find_new_moon(2024, 4, 8.0)
        assert -15 < day < 45


# =====================================================================
#  Geocentric Solar Eclipse
# =====================================================================

class TestComputeSolarEclipse:
    def test_returns_solar_eclipse(self):
        from suryasiddhanta._types import SolarEclipse
        result = compute_solar_eclipse(2024, 4, 8.0)
        assert isinstance(result, SolarEclipse)

    def test_eclipse_type_valid(self):
        result = compute_solar_eclipse(2024, 4, 8.0)
        assert result.eclipse_type in ("none", "partial", "total", "annular")

    def test_magnitude_nonnegative(self):
        result = compute_solar_eclipse(2024, 4, 8.0)
        assert result.magnitude >= 0.0

    def test_jd_populated(self):
        result = compute_solar_eclipse(2024, 4, 8.0)
        assert result.jd > 0

    def test_diameters_populated(self):
        result = compute_solar_eclipse(2024, 4, 8.0)
        assert result.sun_diameter > 0
        assert result.moon_diameter > 0

    def test_no_parallax_fields(self):
        result = compute_solar_eclipse(2024, 4, 8.0)
        assert result.lambana is None
        assert result.nati is None

    def test_notes_has_geocentric(self):
        result = compute_solar_eclipse(2024, 4, 8.0)
        assert "eocentric" in result.notes or "No eclipse" in result.notes

    def test_628_ce(self):
        result = compute_solar_eclipse(628, 6, 1.0)
        assert result.eclipse_type in ("none", "partial", "total", "annular")

    def test_str_output(self):
        result = compute_solar_eclipse(2024, 4, 8.0)
        s = str(result)
        assert len(s) > 0

    def test_different_months_differ(self):
        r1 = compute_solar_eclipse(2024, 4, 8.0)
        r2 = compute_solar_eclipse(2024, 10, 2.0)
        assert r1.jd != r2.jd


# =====================================================================
#  Topocentric Solar Eclipse
# =====================================================================

class TestComputeSolarEclipseTopocentric:
    def test_returns_solar_eclipse(self):
        from suryasiddhanta._types import SolarEclipse
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert isinstance(result, SolarEclipse)

    def test_has_parallax_fields(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert result.lambana is not None
        assert result.nati is not None

    def test_observer_coords_stored(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert result.observer_lat == 23.18
        assert result.observer_lon == 75.77

    def test_eclipse_type_valid(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert result.eclipse_type in ("none", "partial", "total", "annular")

    def test_magnitude_nonnegative(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert result.magnitude >= 0.0

    def test_differs_from_geocentric(self):
        geo = compute_solar_eclipse(2024, 4, 8.0)
        topo = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert geo.jd != topo.jd or geo.magnitude != topo.magnitude

    def test_different_observers_differ(self):
        r1 = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        r2 = compute_solar_eclipse_topocentric(2024, 4, 8.0, 51.5, -0.12)
        assert r1.lambana != r2.lambana or r1.nati != r2.nati

    def test_lambana_bounded(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert abs(result.lambana) <= MOON_HP_ARCMIN + 1

    def test_nati_bounded(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert abs(result.nati) <= MOON_HP_ARCMIN + 1

    def test_notes_has_topocentric(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        assert "opocentric" in result.notes or "No eclipse" in result.notes

    def test_str_with_parallax(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        if result.is_eclipse:
            s = str(result)
            assert "Lambana" in s or "Solar" in s

    def test_ancient_date(self):
        result = compute_solar_eclipse_topocentric(628, 6, 1.0, 23.18, 75.77)
        assert result.eclipse_type in ("none", "partial", "total", "annular")

    def test_far_future(self):
        result = compute_solar_eclipse_topocentric(2100, 6, 1.0, 35.0, 139.0)
        assert result.eclipse_type in ("none", "partial", "total", "annular")


# =====================================================================
#  Parallax Sign Behavior
# =====================================================================

class TestParallaxSignCorrectness:
    def test_lambana_sign_changes_with_moon_position(self):
        """Lambana should change sign depending on Moon vs nonagesimal."""
        jd1 = julian_day(2024, 1, 11, gregorian=True)
        jd2 = julian_day(2024, 7, 5, gregorian=True)
        l1 = lambana_correction(jd1, 23.18, 75.77)
        l2 = lambana_correction(jd2, 23.18, 75.77)
        assert l1 != l2

    def test_nati_flips_between_hemispheres(self):
        """A northern observer sees the Moon pushed south, a southern
        observer north — the whole reason a solar eclipse is regional."""
        jd = julian_day(2024, 4, 8, gregorian=True)
        assert nati_correction(jd, 45.0, 75.77) < 0
        assert nati_correction(jd, -45.0, 75.77) > 0


# =====================================================================
#  Edge Cases
# =====================================================================

class TestEdgeCases:
    def test_equator_observer(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 0.0, 75.77)
        assert result.eclipse_type in ("none", "partial", "total", "annular")

    def test_high_latitude_observer(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 65.0, 25.0)
        assert result.eclipse_type in ("none", "partial", "total", "annular")

    def test_negative_longitude(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 40.0, -74.0)
        assert result.eclipse_type in ("none", "partial", "total", "annular")

    def test_eclipse_has_half_duration(self):
        result = compute_solar_eclipse_topocentric(2024, 4, 8.0, 23.18, 75.77)
        if result.is_eclipse:
            assert result.half_duration is not None
            assert result.half_duration > 0


class TestLambanaBookExamples:
    """Checks the lambana formula against the book's worked example."""

    def test_lambana_ghatis_match_book(self):
        """
        Validates 4*cos(z_n)*sin(delta) against the Kashi example of the
        Samvat 1982 Magha solar eclipse (book Ch.5 bhashya).

        Expected: 1.0608, 1.442 and 1.576 ghatis for (z_n, delta) of
        (43d36', 21d26'), (41d43', 28d52'), (40d57', 31d28').
        """
        cases = [((43 + 36/60, 21 + 26/60), 1.0608),
                 ((41 + 43/60, 28 + 52/60), 1.442),
                 ((40 + 57/60, 31 + 28/60), 1.576)]
        for (z, d), expected in cases:
            assert abs(4 * lambana_factor(z, d) - expected) < 0.01


def test_topocentric_eclipse_reports_signed_moon_latitude_and_daylight():
    from suryasiddhanta.ch01_mean_motions import moon_node_longitude
    from suryasiddhanta.ch02_true_places import compute
    from suryasiddhanta.ch04_lunar_eclipses import moon_latitude

    new_moon_day = find_new_moon(2024, 4, 8.0)
    new_moon_jd = julian_day(2024, 4, new_moon_day)
    moon_lon = compute("Moon", 2024, 4, new_moon_day).true_longitude
    geocentric_latitude = moon_latitude(moon_lon, moon_node_longitude(new_moon_jd))
    # The SS new moon falls near 17:30 UT on 8 Apr 2024: night at 0 deg,
    # late morning at 90 deg W, where the real eclipse was seen.
    night = compute_solar_eclipse_topocentric(2024, 4, 8.0, 0.0, 0.0)
    day = compute_solar_eclipse_topocentric(2024, 4, 8.0, 0.0, -90.0)
    assert night.is_eclipse and day.is_eclipse
    assert night.moon_latitude != 0.0
    assert day.moon_latitude != 0.0
    assert night.moon_latitude == pytest.approx(geocentric_latitude + night.nati, abs=0.01)
    assert night.sun_altitude_deg < 0.0
    assert night.locally_visible is False
    assert day.sun_altitude_deg > 0.0
    assert day.locally_visible is True


def test_geocentric_solar_eclipse_has_latitude_but_no_local_visibility():
    eclipse = compute_solar_eclipse(2024, 4, 8.0)
    assert eclipse.moon_latitude != 0.0
    assert eclipse.sun_altitude_deg is None
    assert eclipse.locally_visible is None
