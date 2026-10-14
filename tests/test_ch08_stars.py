"""Tests for Chapter 8: Of the Stars."""

import math
import pytest
from suryasiddhanta.ch01_mean_motions import julian_day
from suryasiddhanta.ch08_stars import (
    NAKSHATRA_DATA, NAKSHATRA_SPAN,
    get_nakshatra, list_nakshatras, load_catalog_json,
    star_position, StarPosition,
    identify_star, nearest_star,
    star_rise_set, StarRiseSet,
    nakshatra_of,
)


# =====================================================================
#  Nakshatra Catalog
# =====================================================================

class TestNakshatraCatalog:
    def test_count(self):
        assert len(NAKSHATRA_DATA) == 27

    def test_span_constant(self):
        assert abs(NAKSHATRA_SPAN - 13.3333) < 0.001

    def test_numbers_sequential(self):
        for i, nak in enumerate(NAKSHATRA_DATA):
            assert nak.number == i + 1

    def test_all_have_devanagari(self):
        for nak in NAKSHATRA_DATA:
            assert len(nak.devanagari) > 0

    def test_all_have_star_id(self):
        for nak in NAKSHATRA_DATA:
            assert len(nak.star) > 0

    def test_longitudes_in_range(self):
        for nak in NAKSHATRA_DATA:
            assert 0 <= nak.longitude < 360, f"{nak.name} lon={nak.longitude}"

    def test_latitudes_bounded(self):
        for nak in NAKSHATRA_DATA:
            assert -90 <= nak.latitude <= 90, f"{nak.name} lat={nak.latitude}"

    def test_spans_cover_zodiac(self):
        assert NAKSHATRA_DATA[0].span_start == 0.0
        assert abs(NAKSHATRA_DATA[-1].span_end - 360.0) < 0.01

    def test_spans_contiguous(self):
        for i in range(len(NAKSHATRA_DATA) - 1):
            assert abs(NAKSHATRA_DATA[i].span_end
                       - NAKSHATRA_DATA[i + 1].span_start) < 0.001

    def test_gana_valid(self):
        valid = {"Deva", "Manushya", "Rakshasa"}
        for nak in NAKSHATRA_DATA:
            assert nak.gana in valid, f"{nak.name} gana={nak.gana}"

    def test_gana_counts(self):
        ganas = [nak.gana for nak in NAKSHATRA_DATA]
        assert ganas.count("Deva") == 9
        assert ganas.count("Manushya") == 9
        assert ganas.count("Rakshasa") == 9


# =====================================================================
#  Catalog Lookup
# =====================================================================

class TestGetNakshatra:
    def test_by_name(self):
        nak = get_nakshatra("Rohini")
        assert nak.number == 4
        assert nak.star == "α Tauri"

    def test_by_number(self):
        nak = get_nakshatra(14)
        assert nak.name == "Chitra"
        assert nak.longitude == 180.0

    def test_unknown_name_raises(self):
        with pytest.raises(KeyError, match="Unknown nakshatra"):
            get_nakshatra("Nonexistent")

    def test_bad_number_raises(self):
        with pytest.raises(KeyError):
            get_nakshatra(99)

    def test_bad_type_raises(self):
        with pytest.raises(TypeError):
            get_nakshatra(3.14)

    def test_list_nakshatras(self):
        names = list_nakshatras()
        assert len(names) == 27
        assert names[0] == "Ashvini"
        assert names[-1] == "Revati"


# =====================================================================
#  JSON Catalog
# =====================================================================

class TestCatalogJSON:
    def test_loads(self):
        data = load_catalog_json()
        assert "nakshatras" in data

    def test_27_entries(self):
        data = load_catalog_json()
        assert len(data["nakshatras"]) == 27

    def test_has_source(self):
        data = load_catalog_json()
        assert "Burgess" in data["source"]

    def test_fields_present(self):
        data = load_catalog_json()
        entry = data["nakshatras"][0]
        for field in ("number", "name", "devanagari", "star",
                      "longitude", "latitude", "deity", "gana"):
            assert field in entry


# =====================================================================
#  Star Position
# =====================================================================

class TestStarPosition:
    def test_returns_dataclass(self):
        jd = julian_day(2024, 6, 15.0)
        pos = star_position("Rohini", jd)
        assert isinstance(pos, StarPosition)

    def test_sidereal_matches_catalog(self):
        jd = julian_day(2024, 6, 15.0)
        pos = star_position("Rohini", jd)
        assert pos.sidereal_lon == 49.5
        assert pos.sidereal_lat == -5.0

    def test_tropical_differs_from_sidereal(self):
        jd = julian_day(2024, 6, 15.0)
        pos = star_position("Rohini", jd)
        assert pos.tropical_lon != pos.sidereal_lon

    def test_ayanamsha_populated(self):
        jd = julian_day(2024, 6, 15.0)
        pos = star_position("Rohini", jd)
        assert abs(pos.ayanamsha_val) < 27.1

    def test_ra_in_range(self):
        jd = julian_day(2024, 6, 15.0)
        pos = star_position("Chitra", jd)
        assert 0 <= pos.right_ascension < 360

    def test_dec_bounded(self):
        jd = julian_day(2024, 6, 15.0)
        for nak in ("Rohini", "Svati", "Magha", "Revati"):
            pos = star_position(nak, jd)
            assert -90 <= pos.declination_val <= 90

    def test_different_epochs_differ(self):
        jd1 = julian_day(628, 1, 1.0)
        jd2 = julian_day(2024, 1, 1.0)
        p1 = star_position("Rohini", jd1)
        p2 = star_position("Rohini", jd2)
        assert p1.tropical_lon != p2.tropical_lon
        assert p1.sidereal_lon == p2.sidereal_lon

    def test_str_output(self):
        jd = julian_day(2024, 6, 15.0)
        pos = star_position("Magha", jd)
        s = str(pos)
        assert "Magha" in s
        assert "Sidereal" in s


# =====================================================================
#  Star Identification
# =====================================================================

class TestIdentifyStar:
    def test_exact_match(self):
        matches = identify_star(49.5, -5.0)
        assert len(matches) >= 1
        assert matches[0].name == "Rohini"

    def test_near_match(self):
        matches = identify_star(50.0, -4.0, tolerance_deg=5.0)
        names = [m.name for m in matches]
        assert "Rohini" in names

    def test_no_match_tight_tolerance(self):
        matches = identify_star(0.0, 0.0, tolerance_deg=0.01)
        assert len(matches) == 0

    def test_sorted_by_proximity(self):
        matches = identify_star(100.0, 0.0, tolerance_deg=20.0)
        if len(matches) >= 2:
            from suryasiddhanta.ch08_stars import _angular_sep
            d1 = _angular_sep(100.0, 0.0,
                              matches[0].longitude, matches[0].latitude)
            d2 = _angular_sep(100.0, 0.0,
                              matches[1].longitude, matches[1].latitude)
            assert d1 <= d2


class TestNearestStar:
    def test_returns_tuple(self):
        nak, sep = nearest_star(49.5, -5.0)
        assert nak.name == "Rohini"
        assert sep < 0.01

    def test_separation_nonnegative(self):
        nak, sep = nearest_star(100.0, 0.0)
        assert sep >= 0

    def test_arbitrary_position(self):
        nak, sep = nearest_star(200.0, 10.0)
        assert nak is not None
        assert sep < 180


# =====================================================================
#  Star Rise/Set
# =====================================================================

class TestStarRiseSet:
    def test_returns_dataclass(self):
        jd = julian_day(2024, 6, 15.0)
        rs = star_rise_set("Rohini", jd, 23.18, 75.77)
        assert isinstance(rs, StarRiseSet)

    def test_normal_star_rises_and_sets(self):
        jd = julian_day(2024, 6, 15.0)
        rs = star_rise_set("Rohini", jd, 23.18, 75.77)
        assert rs.rises
        assert rs.sets
        assert not rs.is_circumpolar
        assert not rs.is_never_visible

    def test_rise_before_set_or_after(self):
        jd = julian_day(2024, 6, 15.0)
        rs = star_rise_set("Rohini", jd, 23.18, 75.77)
        if rs.rise_jd and rs.set_jd:
            assert rs.rise_jd > jd or rs.set_jd > jd

    def test_rise_jd_populated(self):
        jd = julian_day(2024, 6, 15.0)
        rs = star_rise_set("Magha", jd, 23.18, 75.77)
        if rs.rises and not rs.is_circumpolar:
            assert rs.rise_jd is not None
            assert rs.rise_jd > jd

    def test_hour_angle_positive(self):
        jd = julian_day(2024, 6, 15.0)
        rs = star_rise_set("Rohini", jd, 23.18, 75.77)
        if rs.rises:
            assert rs.hour_angle_deg > 0

    def test_equator_observer(self):
        jd = julian_day(2024, 6, 15.0)
        rs = star_rise_set("Rohini", jd, 0.0, 0.0)
        assert rs.rises
        assert rs.sets

    def test_high_dec_star_high_lat(self):
        """Star with high declination at high latitude may be circumpolar."""
        jd = julian_day(2024, 6, 15.0)
        rs = star_rise_set("Shravana", jd, 75.0, 0.0)
        assert isinstance(rs, StarRiseSet)

    def test_str_output(self):
        jd = julian_day(2024, 6, 15.0)
        rs = star_rise_set("Rohini", jd, 23.18, 75.77)
        s = str(rs)
        assert "Rohini" in s


# =====================================================================
#  Nakshatra Housing
# =====================================================================

class TestNakshatraOf:
    def test_ashvini_start(self):
        nak = nakshatra_of(0.0)
        assert nak.name == "Ashvini"

    def test_ashvini_mid(self):
        nak = nakshatra_of(6.0)
        assert nak.name == "Ashvini"

    def test_bharani(self):
        nak = nakshatra_of(15.0)
        assert nak.name == "Bharani"

    def test_revati(self):
        nak = nakshatra_of(350.0)
        assert nak.name == "Revati"

    def test_boundary(self):
        nak = nakshatra_of(13.3334)
        assert nak.name == "Bharani"

    def test_full_circle(self):
        """All 27 nakshatras reachable."""
        seen = set()
        for deg in range(0, 360, 5):
            nak = nakshatra_of(float(deg))
            seen.add(nak.name)
        assert len(seen) == 27

    def test_wrap_360(self):
        nak = nakshatra_of(360.0)
        assert nak.name == "Ashvini"


# =====================================================================
#  Edge Cases
# =====================================================================

class TestEdgeCases:
    def test_ancient_date_position(self):
        jd = julian_day(628, 1, 1.0)
        pos = star_position("Chitra", jd)
        assert isinstance(pos, StarPosition)

    def test_all_stars_have_position(self):
        jd = julian_day(2024, 6, 15.0)
        for nak in NAKSHATRA_DATA:
            pos = star_position(nak.name, jd)
            assert 0 <= pos.tropical_lon < 360
            assert 0 <= pos.right_ascension < 360

    def test_svati_high_latitude(self):
        """Svati (Arcturus) at lat=37 deg is far from ecliptic."""
        nak = get_nakshatra("Svati")
        assert nak.latitude == 37.0

    def test_pushya_zero_latitude(self):
        nak = get_nakshatra("Pushya")
        assert nak.latitude == 0.0

    def test_revati_near_360(self):
        nak = get_nakshatra("Revati")
        assert nak.longitude > 359


def test_abhijit_is_found_as_star_without_changing_27_houses():
    nak = get_nakshatra("Abhijit")
    assert get_nakshatra(28) is nak
    assert (nak.longitude, nak.latitude) == pytest.approx((266 + 40 / 60, 60.0))
    assert star_position("Abhijit", julian_day(2024, 6, 15)).sidereal_lon == nak.longitude
    assert identify_star(nak.longitude, nak.latitude, tolerance_deg=0.01)[0].name == "Abhijit"
    assert nearest_star(nak.longitude, nak.latitude)[0].name == "Abhijit"
    assert len(list_nakshatras()) == 27
    assert nakshatra_of(nak.longitude).name == "Uttara Ashadha"
