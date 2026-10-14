"""Tests for Chapter 6: Eclipse Projection."""

import math
import pytest
from suryasiddhanta.ch04_lunar_eclipses import compute_lunar_eclipse
from suryasiddhanta.ch05_solar_eclipses import compute_solar_eclipse
from suryasiddhanta.ch06_eclipse_projection import (
    ayana_valana, aksha_valana, total_valana,
    eclipse_contact_points, project_eclipse_path,
    eclipse_diagram_data, EclipseDiagram,
)


# =====================================================================
#  Ayana Valana
# =====================================================================

class TestAyanaValana:
    def test_zero_at_solstice_90(self):
        av = ayana_valana(90.0)
        assert abs(av) < 0.1

    def test_zero_at_solstice_270(self):
        av = ayana_valana(270.0)
        assert abs(av) < 0.1

    def test_max_at_equinox_0(self):
        av = ayana_valana(0.0)
        assert abs(av - 24.0) < 0.5

    def test_max_at_equinox_180(self):
        av = ayana_valana(180.0)
        assert abs(av + 24.0) < 0.5

    def test_bounded_by_obliquity(self):
        for lon in range(0, 360, 10):
            av = ayana_valana(float(lon))
            assert -24.5 <= av <= 24.5

    def test_antisymmetric(self):
        av1 = ayana_valana(30.0)
        av2 = ayana_valana(330.0)
        assert abs(av1 - av2) < 0.01

    def test_sign_change_across_solstice(self):
        av_before = ayana_valana(80.0)
        av_after = ayana_valana(100.0)
        assert av_before * av_after < 0 or abs(av_before) < 1 or abs(av_after) < 1


# =====================================================================
#  Aksha Valana
# =====================================================================

class TestAkshaValana:
    def test_zero_at_meridian(self):
        kv = aksha_valana(0.0, 20.0, 23.18)
        assert abs(kv) < 0.01

    def test_zero_at_equator(self):
        """
        Validates SS Ch.4 v.24: sin(aksha) carries sin(latitude), so an
        observer on the equator has no aksha-valana whatever the hour angle.
        """
        assert abs(aksha_valana(30.0, 10.0, 0.0)) < 1e-9

    def test_increases_with_latitude(self):
        """Expected: the aksha-valana grows with latitude (book v.24)."""
        kv_low = abs(aksha_valana(45.0, 20.0, 10.0))
        kv_high = abs(aksha_valana(45.0, 20.0, 60.0))
        assert kv_low < kv_high

    def test_book_example_samvat_1981_kashi(self):
        """
        Validates against the book's lunar eclipse of Samvat 1981 at Kashi.

        Moon zenith distance 47d17', declination 14d16'.5 S, latitude
        25d20', agra 53d56' S of west.  Expected: 13d44' south (book
        Ch.6 example), i.e. about -13.73 deg in the north-positive convention.
        """
        lat, dec, z = 25 + 20 / 60, -(14 + 16.5 / 60), 47 + 17 / 60
        # hour angle from cos z = sin(lat) sin(dec) + cos(lat) cos(dec) cos(H)
        cos_h = ((math.cos(math.radians(z))
                  - math.sin(math.radians(lat)) * math.sin(math.radians(dec)))
                 / (math.cos(math.radians(lat)) * math.cos(math.radians(dec))))
        h = math.degrees(math.acos(cos_h))   # west (positive)
        assert abs(aksha_valana(h, dec, lat) - (-(13 + 44 / 60))) < 0.1

    def test_ayana_book_example(self):
        """
        Validates ayana-valana against the same example: sayana longitude
        321d14', obliquity 23d27'.  Expected: 18d40' north.
        """
        av = ayana_valana(321 + 14 / 60, 23 + 27 / 60)
        assert abs(av - (18 + 40 / 60)) < 0.2

    def test_nonzero_off_meridian(self):
        kv = aksha_valana(45.0, 20.0, 23.18)
        assert abs(kv) > 0.1

    def test_sign_changes_with_ha(self):
        kv_east = aksha_valana(45.0, 20.0, 23.18)
        kv_west = aksha_valana(-45.0, 20.0, 23.18)
        assert kv_east * kv_west < 0

    def test_bounded(self):
        for ha in range(-180, 180, 30):
            kv = aksha_valana(float(ha), 20.0, 45.0)
            assert -90 <= kv <= 90


# =====================================================================
#  Total Valana
# =====================================================================

class TestTotalValana:
    def test_equals_sum(self):
        from suryasiddhanta.ch03_direction_place_time import declination
        sun_lon = 45.0
        ha = 30.0
        lat = 23.18
        tv = total_valana(sun_lon, ha, lat)
        av = ayana_valana(sun_lon)
        dec = declination(sun_lon)
        kv = aksha_valana(ha, dec, lat)
        assert abs(tv - (av + kv)) < 0.01

    def test_zero_at_solstice_meridian_equator(self):
        tv = total_valana(90.0, 0.0, 0.0)
        assert abs(tv) < 0.1


# =====================================================================
#  Eclipse Contact Points
# =====================================================================

def _get_lunar_eclipse():
    """Find a month that produces an eclipse for testing."""
    for month in range(1, 13):
        ecl = compute_lunar_eclipse(2024, month, 15.0)
        if ecl.is_eclipse:
            return ecl
    return compute_lunar_eclipse(2024, 9, 18.0)


def _get_solar_eclipse():
    for month in range(1, 13):
        ecl = compute_solar_eclipse(2024, month, 1.0)
        if ecl.is_eclipse:
            return ecl
    return compute_solar_eclipse(2024, 4, 8.0)


class TestEclipseContactPoints:
    def test_lunar_eclipse_returns_dict(self):
        ecl = _get_lunar_eclipse()
        cp = eclipse_contact_points(ecl, 23.18, 75.77)
        assert isinstance(cp, dict)
        assert "first_contact_pa" in cp
        assert "last_contact_pa" in cp
        assert "valana" in cp

    def test_no_eclipse_returns_none_pa(self):
        ecl = compute_lunar_eclipse(2024, 3, 25.0)
        if not ecl.is_eclipse:
            cp = eclipse_contact_points(ecl)
            assert cp["first_contact_pa"] is None
            assert cp["last_contact_pa"] is None

    def test_pa_in_range(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            cp = eclipse_contact_points(ecl, 23.18, 75.77)
            assert 0 <= cp["first_contact_pa"] < 360
            assert 0 <= cp["last_contact_pa"] < 360

    def test_has_valana_components(self):
        ecl = _get_lunar_eclipse()
        cp = eclipse_contact_points(ecl, 23.18, 75.77)
        assert "ayana_valana" in cp
        assert "aksha_valana" in cp

    def test_solar_eclipse_contact(self):
        ecl = _get_solar_eclipse()
        cp = eclipse_contact_points(ecl, 23.18, 75.77)
        assert isinstance(cp, dict)

    def test_different_observers_differ(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            cp1 = eclipse_contact_points(ecl, 23.18, 75.77)
            cp2 = eclipse_contact_points(ecl, 51.5, -0.12)
            assert cp1["valana"] != cp2["valana"]


# =====================================================================
#  Path Projection
# =====================================================================

class TestProjectEclipsePath:
    def test_eclipse_returns_points(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            path = project_eclipse_path(ecl)
            assert len(path) > 0

    def test_no_eclipse_empty(self):
        ecl = compute_lunar_eclipse(2024, 3, 25.0)
        if not ecl.is_eclipse:
            path = project_eclipse_path(ecl)
            assert path == []

    def test_points_are_tuples(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            path = project_eclipse_path(ecl)
            for p in path:
                assert isinstance(p, tuple)
                assert len(p) == 2

    def test_path_symmetric(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            path = project_eclipse_path(ecl, n_points=50)
            x_first = path[0][0]
            x_last = path[-1][0]
            assert abs(x_first + x_last) < 0.1

    def test_y_constant(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            path = project_eclipse_path(ecl)
            ys = set(p[1] for p in path)
            assert len(ys) == 1

    def test_contact_on_eclipse_circle(self):
        """First/last path points should be at combined radius from centre."""
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            path = project_eclipse_path(ecl)
            x, y = path[0]
            dist = math.sqrt(x**2 + y**2)
            limit = ecl.shadow_diameter / 2 + ecl.moon_diameter / 2
            assert abs(dist - limit) < 0.5

    def test_custom_n_points(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            path = project_eclipse_path(ecl, n_points=10)
            assert len(path) == 11

    def test_solar_eclipse_path(self):
        ecl = _get_solar_eclipse()
        path = project_eclipse_path(ecl)
        if ecl.is_eclipse:
            assert len(path) > 0


# =====================================================================
#  Eclipse Diagram Data
# =====================================================================

class TestEclipseDiagramData:
    def test_returns_diagram(self):
        ecl = _get_lunar_eclipse()
        diag = eclipse_diagram_data(ecl, 23.18, 75.77)
        assert isinstance(diag, EclipseDiagram)

    def test_lunar_body_is_moon(self):
        """
        Validates SS Ch.6: in a lunar eclipse the Moon is the eclipsed
        (chhadya) body and the earth's shadow the eclipser.
        """
        ecl = _get_lunar_eclipse()
        diag = eclipse_diagram_data(ecl)
        assert diag.eclipsed_body == "Moon"

    def test_solar_body_is_sun(self):
        ecl = _get_solar_eclipse()
        diag = eclipse_diagram_data(ecl)
        assert diag.eclipsed_body == "Sun"

    def test_radii_positive(self):
        ecl = _get_lunar_eclipse()
        diag = eclipse_diagram_data(ecl)
        assert diag.eclipsed_radius > 0
        assert diag.eclipser_radius > 0

    def test_has_path(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            diag = eclipse_diagram_data(ecl)
            assert len(diag.path) > 0

    def test_has_contact_xy(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            diag = eclipse_diagram_data(ecl)
            assert diag.first_contact_xy is not None
            assert diag.last_contact_xy is not None
            assert diag.mid_eclipse_xy is not None

    def test_mid_eclipse_at_origin_x(self):
        ecl = _get_lunar_eclipse()
        if ecl.is_eclipse:
            diag = eclipse_diagram_data(ecl)
            assert diag.mid_eclipse_xy[0] == 0.0

    def test_str_output(self):
        ecl = _get_lunar_eclipse()
        diag = eclipse_diagram_data(ecl, 23.18, 75.77)
        s = str(diag)
        if ecl.is_eclipse:
            assert "Eclipse Projection" in s
        else:
            assert "No eclipse" in s

    def test_no_eclipse_diagram(self):
        ecl = compute_lunar_eclipse(2024, 3, 25.0)
        if not ecl.is_eclipse:
            diag = eclipse_diagram_data(ecl)
            assert diag.is_eclipse is False
            assert diag.path == []

    def test_diagram_valana_matches_contacts(self):
        ecl = _get_lunar_eclipse()
        diag = eclipse_diagram_data(ecl, 23.18, 75.77)
        cp = eclipse_contact_points(ecl, 23.18, 75.77)
        assert diag.valana == cp["valana"]


# =====================================================================
#  Edge Cases
# =====================================================================

class TestEdgeCases:
    def test_equator_observer(self):
        ecl = _get_lunar_eclipse()
        diag = eclipse_diagram_data(ecl, 0.0, 0.0)
        assert isinstance(diag, EclipseDiagram)

    def test_high_latitude(self):
        ecl = _get_lunar_eclipse()
        diag = eclipse_diagram_data(ecl, 65.0, 25.0)
        assert isinstance(diag, EclipseDiagram)

    def test_ancient_eclipse(self):
        ecl = compute_lunar_eclipse(628, 1, 15.0)
        diag = eclipse_diagram_data(ecl, 23.18, 75.77)
        assert isinstance(diag, EclipseDiagram)


def test_lunar_and_solar_paths_use_opposite_contact_and_latitude_signs():
    from suryasiddhanta._types import LunarEclipse, SolarEclipse

    lunar = LunarEclipse(2460409.5, True, "partial", 10.0, 30.0, 80.0,
                         0.1, 20.0, None, "")
    solar = SolarEclipse(2460409.5, True, "partial", 30.0, 30.0,
                         0.1, "", moon_latitude=10.0)
    lunar_path = project_eclipse_path(lunar, n_points=2)
    solar_path = project_eclipse_path(solar, n_points=2)
    assert lunar_path[0][0] > 0 > lunar_path[-1][0]
    assert all(y == -10.0 for _, y in lunar_path)
    assert solar_path[0][0] < 0 < solar_path[-1][0]
    assert all(y == 10.0 for _, y in solar_path)
    assert eclipse_diagram_data(lunar).first_contact_xy == lunar_path[0]
    assert eclipse_diagram_data(solar).first_contact_xy == solar_path[0]


def test_contact_angles_follow_projected_contact_quadrants():
    from suryasiddhanta._types import LunarEclipse, SolarEclipse

    lunar = LunarEclipse(2460409.5, True, "partial", 10.0, 30.0, 80.0,
                         0.1, 20.0, None, "")
    solar = SolarEclipse(2460409.5, True, "partial", 30.0, 30.0,
                         0.1, "", moon_latitude=10.0)
    for eclipse, east in ((lunar, True), (solar, False)):
        contacts = eclipse_contact_points(eclipse)
        first = eclipse_diagram_data(eclipse).first_contact_xy
        expected = (math.degrees(math.atan2(*first)) + contacts["valana"]) % 360
        assert abs((contacts["first_contact_pa"] - expected + 180) % 360 - 180) < 0.02
