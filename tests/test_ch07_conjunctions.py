"""Tests for Chapter 7: Planetary Conjunctions."""

import math
import pytest
from suryasiddhanta.ch01_mean_motions import julian_day
from suryasiddhanta.ch07_conjunctions import (
    angular_separation, longitude_difference,
    find_conjunction, planet_planet_conjunction,
    planet_star_conjunction, nearest_conjunction,
    classify_conjunction,
    Conjunction, YOGATARA, PLANETS,
)


# =====================================================================
#  Angular Separation
# =====================================================================

class TestAngularSeparation:
    def test_same_point(self):
        sep = angular_separation(45.0, 10.0, 45.0, 10.0)
        assert abs(sep) < 0.001

    def test_opposite_points(self):
        sep = angular_separation(0.0, 0.0, 180.0, 0.0)
        assert abs(sep - 180.0) < 0.001

    def test_90_degrees(self):
        sep = angular_separation(0.0, 0.0, 90.0, 0.0)
        assert abs(sep - 90.0) < 0.001

    def test_latitude_only(self):
        sep = angular_separation(0.0, 30.0, 0.0, 0.0)
        assert abs(sep - 30.0) < 0.001

    def test_symmetric(self):
        sep1 = angular_separation(10.0, 5.0, 50.0, -3.0)
        sep2 = angular_separation(50.0, -3.0, 10.0, 5.0)
        assert abs(sep1 - sep2) < 0.001

    def test_nonnegative(self):
        for lon1 in range(0, 360, 45):
            for lon2 in range(0, 360, 45):
                sep = angular_separation(float(lon1), 0.0, float(lon2), 0.0)
                assert sep >= 0

    def test_max_180(self):
        for lon in range(0, 360, 30):
            for lat in range(-60, 61, 30):
                sep = angular_separation(float(lon), float(lat), 0.0, 0.0)
                assert sep <= 180.001

    def test_small_separation(self):
        sep = angular_separation(100.0, 0.0, 100.5, 0.3)
        assert 0.3 < sep < 1.0


# =====================================================================
#  Longitude Difference
# =====================================================================

class TestLongitudeDifference:
    def test_same(self):
        d = longitude_difference(100.0, 100.0)
        assert abs(d) < 0.001

    def test_positive(self):
        d = longitude_difference(100.0, 90.0)
        assert abs(d - 10.0) < 0.001

    def test_negative(self):
        d = longitude_difference(90.0, 100.0)
        assert abs(d + 10.0) < 0.001

    def test_wrap_positive(self):
        d = longitude_difference(10.0, 350.0)
        assert abs(d - 20.0) < 0.001

    def test_wrap_negative(self):
        d = longitude_difference(350.0, 10.0)
        assert abs(d + 20.0) < 0.001

    def test_range(self):
        for lon1 in range(0, 360, 15):
            for lon2 in range(0, 360, 15):
                d = longitude_difference(float(lon1), float(lon2))
                assert -180 <= d <= 180

    def test_opposition(self):
        d = longitude_difference(0.0, 180.0)
        assert abs(abs(d) - 180.0) < 0.001


# =====================================================================
#  Yogatara Catalog
# =====================================================================

class TestYogataraCatalog:
    def test_count(self):
        assert len(YOGATARA) == 27

    def test_all_have_coordinates(self):
        for name, (lon, lat) in YOGATARA.items():
            assert isinstance(lon, (int, float))
            assert isinstance(lat, (int, float))

    def test_longitudes_in_range(self):
        for name, (lon, _) in YOGATARA.items():
            assert 0 <= lon < 360, f"{name} lon={lon}"

    def test_latitudes_bounded(self):
        for name, (_, lat) in YOGATARA.items():
            assert -90 <= lat <= 90, f"{name} lat={lat}"

    def test_known_stars_present(self):
        assert "Rohini" in YOGATARA
        assert "Chitra" in YOGATARA
        assert "Revati" in YOGATARA
        assert "Magha" in YOGATARA

    def test_rohini_near_taurus(self):
        lon, _ = YOGATARA["Rohini"]
        assert 40 < lon < 60

    def test_chitra_at_180(self):
        lon, _ = YOGATARA["Chitra"]
        assert lon == 180.0


# =====================================================================
#  Find Conjunction
# =====================================================================

class TestFindConjunction:
    def test_returns_list(self):
        start_jd = julian_day(2024, 1, 1.0)
        end_jd = start_jd + 30
        result = find_conjunction("Jupiter", "Saturn", start_jd, end_jd)
        assert isinstance(result, list)

    def test_same_planet_empty(self):
        start_jd = julian_day(2024, 1, 1.0)
        end_jd = start_jd + 365
        result = find_conjunction("Mars", "Mars", start_jd, end_jd)
        assert result == []

    def test_venus_mars_finds_conjunction(self):
        """Venus and Mars should conjunct within ~2 years."""
        start_jd = julian_day(2024, 1, 1.0)
        end_jd = start_jd + 730
        results = find_conjunction("Venus", "Mars", start_jd, end_jd)
        assert len(results) >= 1

    def test_conjunction_fields(self):
        start_jd = julian_day(2024, 1, 1.0)
        end_jd = start_jd + 730
        results = find_conjunction("Venus", "Mars", start_jd, end_jd)
        if results:
            c = results[0]
            assert isinstance(c, Conjunction)
            assert c.body1 == "Venus"
            assert c.body2 == "Mars"
            assert start_jd <= c.jd <= end_jd
            assert 0 <= c.longitude < 360
            assert c.separation_deg >= 0

    def test_conjunction_type_valid(self):
        start_jd = julian_day(2024, 1, 1.0)
        end_jd = start_jd + 730
        results = find_conjunction("Venus", "Mars", start_jd, end_jd)
        for c in results:
            assert c.conjunction_type in ("yuddha", "samagama")

    def test_chronological_order(self):
        start_jd = julian_day(2024, 1, 1.0)
        end_jd = start_jd + 730
        results = find_conjunction("Mercury", "Venus", start_jd, end_jd)
        for i in range(len(results) - 1):
            assert results[i].jd < results[i + 1].jd

    def test_separation_small(self):
        """At conjunction, longitude separation should be near zero."""
        start_jd = julian_day(2024, 1, 1.0)
        end_jd = start_jd + 730
        results = find_conjunction("Venus", "Mars", start_jd, end_jd)
        for c in results:
            # equal longitude: separation is the latitude difference only
            assert c.separation_deg < 10.0

    def test_yuddha_requires_close_discs(self):
        """
        Validates that conjunction_type follows the disc separation
        (latitude included), not just the longitude match.

        Expected: yuddha exactly when separation < 1 deg for tara-graha pairs.
        """
        start_jd = julian_day(2020, 1, 1.0)
        for a, b in [("Venus", "Mars"), ("Mercury", "Venus"), ("Mars", "Saturn")]:
            for c in find_conjunction(a, b, start_jd, start_jd + 3650):
                assert (c.conjunction_type == "yuddha") == (c.separation_deg < 1.0)


# =====================================================================
#  Planet-Planet Conjunction
# =====================================================================

class TestPlanetPlanetConjunction:
    def test_returns_list(self):
        results = planet_planet_conjunction("Venus", "Mars", 2024, 1, 24)
        assert isinstance(results, list)

    def test_finds_conjunction(self):
        results = planet_planet_conjunction("Venus", "Mars", 2024, 1, 24)
        assert len(results) >= 1

    def test_default_months(self):
        results = planet_planet_conjunction("Mercury", "Venus", 2024)
        assert isinstance(results, list)

    def test_str_output(self):
        results = planet_planet_conjunction("Venus", "Mars", 2024, 1, 24)
        if results:
            s = str(results[0])
            assert "Conjunction" in s
            assert "Venus" in s
            assert "Mars" in s

    def test_ancient_date(self):
        results = planet_planet_conjunction("Mars", "Jupiter", 628, 1, 24)
        assert isinstance(results, list)


# =====================================================================
#  Planet-Star Conjunction
# =====================================================================

class TestPlanetStarConjunction:
    def test_returns_list(self):
        results = planet_star_conjunction("Jupiter", "Rohini", 2024)
        assert isinstance(results, list)

    def test_unknown_star_raises(self):
        with pytest.raises(ValueError, match="Unknown star"):
            planet_star_conjunction("Mars", "Nonexistent", 2024)

    def test_sun_crosses_star(self):
        """Sun traverses full zodiac yearly, should cross Rohini."""
        results = planet_star_conjunction("Sun", "Rohini", 2024, months=14)
        assert len(results) >= 1

    def test_star_conjunction_type(self):
        results = planet_star_conjunction("Sun", "Rohini", 2024, months=14)
        for c in results:
            assert c.conjunction_type == "star_conjunction"

    def test_star_lat_stored(self):
        results = planet_star_conjunction("Sun", "Chitra", 2024, months=14)
        if results:
            c = results[0]
            assert c.body2 == "Chitra"
            assert c.body2_lat == YOGATARA["Chitra"][1]

    def test_high_lat_star_separation(self):
        """Svati at lat=37 deg: even at longitude match, separation > 0."""
        results = planet_star_conjunction("Sun", "Svati", 2024, months=14)
        if results:
            assert results[0].separation_deg > 30

    def test_notes_populated(self):
        results = planet_star_conjunction("Sun", "Magha", 2024, months=14)
        if results:
            assert "Star at" in results[0].notes


# =====================================================================
#  Nearest Conjunction
# =====================================================================

class TestNearestConjunction:
    def test_returns_conjunction_or_none(self):
        jd = julian_day(2024, 6, 15.0)
        result = nearest_conjunction("Venus", "Mars", jd)
        assert result is None or isinstance(result, Conjunction)

    def test_nearest_is_closest(self):
        jd = julian_day(2024, 6, 15.0)
        result = nearest_conjunction("Venus", "Mars", jd, search_days=500)
        if result:
            all_results = find_conjunction(
                "Venus", "Mars", jd - 500, jd + 500)
            distances = [abs(c.jd - jd) for c in all_results]
            assert abs(result.jd - jd) <= min(distances) + 0.01

    def test_no_result_short_range(self):
        jd = julian_day(2024, 1, 1.0)
        result = nearest_conjunction("Jupiter", "Saturn", jd, search_days=5)
        assert result is None or isinstance(result, Conjunction)


# =====================================================================
#  Classify Conjunction
# =====================================================================

class TestClassifyConjunction:
    def test_yuddha(self):
        assert classify_conjunction(0.5) == "yuddha"

    def test_samagama(self):
        assert classify_conjunction(3.0) == "samagama"

    def test_wide_separation_is_still_samagama(self):
        """SS v.20 sets no upper bound: anything over 1 deg is samagama."""
        assert classify_conjunction(10.0) == "samagama"

    def test_sun_or_moon_never_yuddha(self):
        """
        Validates SS v.1: only the five tara-graha fight.

        Expected: a 0.2 deg meeting involving the Sun or Moon is samagama.
        """
        assert classify_conjunction(0.2, both_taragraha=False) == "samagama"

    def test_boundary_1deg(self):
        assert classify_conjunction(0.99) == "yuddha"
        assert classify_conjunction(1.01) == "samagama"

    def test_zero(self):
        assert classify_conjunction(0.0) == "yuddha"


# =====================================================================
#  Edge Cases
# =====================================================================

class TestEdgeCases:
    def test_short_range(self):
        start_jd = julian_day(2024, 1, 1.0)
        result = find_conjunction("Jupiter", "Saturn", start_jd, start_jd + 1)
        assert isinstance(result, list)

    def test_conjunction_dataclass_defaults(self):
        c = Conjunction(
            body1="Mars", body2="Jupiter",
            jd=2460000.0, longitude=100.0,
            separation_deg=0.5,
            conjunction_type="yuddha",
        )
        assert c.body1_lat == 0.0
        assert c.body2_lat == 0.0
        assert c.notes == ""

    def test_str_contains_date(self):
        c = Conjunction(
            body1="Mars", body2="Jupiter",
            jd=2460000.0, longitude=100.0,
            separation_deg=0.5,
            conjunction_type="yuddha",
        )
        s = str(c)
        assert "Mars" in s
        assert "Jupiter" in s
        assert "yuddha" in s

    def test_planets_list(self):
        assert len(PLANETS) == 7
        assert "Sun" in PLANETS
        assert "Moon" in PLANETS
        assert "Jupiter" in PLANETS

    def test_angular_separation_poles(self):
        sep = angular_separation(0.0, 90.0, 0.0, -90.0)
        assert abs(sep - 180.0) < 0.001


def test_planet_conjunction_carries_computed_latitudes():
    from suryasiddhanta.ch02_true_places import planet_latitude

    start = julian_day(2024, 1, 1.0)
    result = find_conjunction("Venus", "Mars", start, start + 730)[0]
    assert result.body1_lat == pytest.approx(planet_latitude("Venus", result.jd) / 60, abs=0.001)
    assert result.body2_lat == pytest.approx(planet_latitude("Mars", result.jd) / 60, abs=0.001)


def test_planet_star_separation_uses_planet_latitude():
    from suryasiddhanta.ch02_true_places import planet_latitude

    result = planet_star_conjunction("Venus", "Rohini", 2024, months=24)[0]
    latitude = planet_latitude("Venus", result.jd) / 60
    expected = angular_separation(result.longitude, latitude, 49.5, -5.0)
    assert result.body1_lat == pytest.approx(latitude, abs=0.001)
    assert result.separation_deg == pytest.approx(expected, abs=0.001)
