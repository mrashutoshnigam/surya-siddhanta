"""Tests for Chapter 2: True Places of the Planets."""

import math
import pytest
from suryasiddhanta.ch01_mean_motions import (
    julian_day, KALI_EPOCH_JD, ALL_PLANETS,
)
from suryasiddhanta.ch02_true_places import (
    R_SINE, JYA_TABLE, JYA_STEP_ARCMIN, OBLIQUITY_DEGREES,
    normalize, normalize_signed, to_dms, from_dms, angular_error,
    deg_to_arcmin, arcmin_to_deg, deg_to_arcsec, arcsec_to_deg,
    jya, jya_normalized, koti, utkrama_jya, arcjya,
    ss_sin, ss_cos, ss_arcsin,
    get_bhuja_koti, get_quadrant, is_odd_quadrant,
    table_accuracy_report,
    MANDA_EPICYCLE, SIGHRA_EPICYCLE, PLANETS_WITH_SIGHRA,
    corrected_manda_epicycle, manda_correction, manda_longitude,
    corrected_sighra_epicycle, sighra_correction,
    true_longitude_full,
    ayanamsha, sidereal_to_tropical, tropical_to_sidereal,
    compute, compute_all,
)


# =====================================================================
#  Constants
# =====================================================================

class TestConstants:
    def test_r_sine(self):
        assert R_SINE == 3438

    def test_jya_table_length(self):
        assert len(JYA_TABLE) == 24

    def test_jya_table_monotonic(self):
        for i in range(23):
            assert JYA_TABLE[i] < JYA_TABLE[i + 1]

    def test_jya_table_last_entry_equals_r(self):
        assert JYA_TABLE[23] == R_SINE

    def test_jya_table_first_entry(self):
        assert JYA_TABLE[0] == 225

    def test_step_size(self):
        assert JYA_STEP_ARCMIN == 225

    def test_obliquity(self):
        assert OBLIQUITY_DEGREES == 24.0


# =====================================================================
#  All 24 Jya Values — exact match to SS text
# =====================================================================

class TestJyaTableExact:
    EXPECTED = [
        225, 449, 671, 890, 1105, 1315, 1520, 1719,
        1910, 2093, 2267, 2431, 2585, 2728, 2859, 2978,
        3084, 3177, 3256, 3321, 3372, 3409, 3431, 3438,
    ]

    @pytest.mark.parametrize("i", range(24))
    def test_jya_value(self, i):
        assert JYA_TABLE[i] == self.EXPECTED[i]


# =====================================================================
#  Angle Utilities
# =====================================================================

class TestNormalize:
    def test_zero(self):
        assert normalize(0.0) == 0.0

    def test_positive(self):
        assert normalize(370.0) == pytest.approx(10.0)

    def test_negative(self):
        assert normalize(-10.0) == pytest.approx(350.0)

    def test_720(self):
        assert normalize(720.0) == pytest.approx(0.0)


class TestNormalizeSigned:
    def test_zero(self):
        assert normalize_signed(0.0) == 0.0

    def test_positive_wrap(self):
        assert normalize_signed(270.0) == pytest.approx(-90.0)

    def test_exactly_180(self):
        assert normalize_signed(180.0) == pytest.approx(180.0)

    def test_negative(self):
        assert normalize_signed(-10.0) == pytest.approx(-10.0)


class TestDms:
    def test_to_dms_exact(self):
        d, m, s = to_dms(45.5)
        assert d == 45
        assert m == 30
        assert abs(s) < 0.1

    def test_roundtrip(self):
        val = 123.456
        d, m, s = to_dms(val)
        back = from_dms(d, m, s)
        assert abs(back - val) < 0.001

    def test_from_dms_simple(self):
        assert from_dms(30, 30, 0.0) == pytest.approx(30.5)


class TestAngularError:
    def test_same(self):
        assert angular_error(100.0, 100.0) == 0.0

    def test_small(self):
        assert angular_error(10.0, 350.0) == pytest.approx(20.0)

    def test_opposite(self):
        assert angular_error(0.0, 180.0) == pytest.approx(180.0)

    def test_wrap(self):
        assert angular_error(1.0, 359.0) == pytest.approx(2.0)


# =====================================================================
#  Unit Conversions
# =====================================================================

class TestUnitConversions:
    def test_deg_to_arcmin(self):
        assert deg_to_arcmin(1.0) == 60.0

    def test_arcmin_to_deg(self):
        assert arcmin_to_deg(60.0) == 1.0

    def test_deg_to_arcsec(self):
        assert deg_to_arcsec(1.0) == 3600.0

    def test_arcsec_to_deg(self):
        assert arcsec_to_deg(3600.0) == 1.0

    def test_roundtrip(self):
        assert arcsec_to_deg(deg_to_arcsec(45.5)) == pytest.approx(45.5)


# =====================================================================
#  Jya (Sine) Function
# =====================================================================

class TestJya:
    def test_zero(self):
        assert jya(0.0) == 0.0

    def test_90(self):
        assert jya(90.0) == R_SINE

    def test_180(self):
        assert abs(jya(180.0)) < 1.0

    def test_270(self):
        assert jya(270.0) == -R_SINE

    def test_360(self):
        assert abs(jya(360.0)) < 1.0

    def test_45_positive(self):
        assert jya(45.0) > 0

    def test_135_positive(self):
        assert jya(135.0) > 0

    def test_225_negative(self):
        assert jya(225.0) < 0

    def test_315_negative(self):
        assert jya(315.0) < 0

    def test_at_table_points(self):
        for i in range(24):
            angle = (i + 1) * JYA_STEP_ARCMIN / 60.0
            assert abs(jya(angle) - JYA_TABLE[i]) < 0.01

    def test_agrees_with_modern_sin(self):
        for angle in [15, 30, 45, 60, 75]:
            ss_val = jya(angle) / R_SINE
            modern = math.sin(math.radians(angle))
            assert abs(ss_val - modern) < 0.005


class TestJyaNormalized:
    def test_range(self):
        for angle in range(0, 360, 15):
            val = jya_normalized(float(angle))
            assert -1.01 <= val <= 1.01

    def test_sin_90(self):
        assert abs(jya_normalized(90.0) - 1.0) < 0.001


class TestKoti:
    def test_koti_0_equals_r(self):
        assert abs(koti(0.0) - R_SINE) < 1.0

    def test_koti_90_equals_zero(self):
        assert abs(koti(90.0)) < 1.0

    def test_koti_is_cosine(self):
        for angle in [30, 45, 60]:
            ss_val = koti(angle) / R_SINE
            modern = math.cos(math.radians(angle))
            assert abs(ss_val - modern) < 0.005


class TestUtkramaJya:
    def test_zero_at_zero(self):
        assert abs(utkrama_jya(0.0)) < 1.0

    def test_r_at_90(self):
        assert abs(utkrama_jya(90.0) - R_SINE) < 1.0

    def test_mid_value(self):
        val = utkrama_jya(60.0)
        modern = R_SINE * (1.0 - math.cos(math.radians(60.0)))
        assert abs(val - modern) < 10


# =====================================================================
#  Arcjya (Inverse Sine)
# =====================================================================

class TestArcjya:
    def test_zero(self):
        assert arcjya(0) == 0.0

    def test_max(self):
        assert arcjya(R_SINE) == 90.0

    def test_negative(self):
        assert arcjya(-R_SINE) == -90.0

    def test_roundtrip_table_points(self):
        for i in range(24):
            angle_deg = (i + 1) * JYA_STEP_ARCMIN / 60.0
            val = JYA_TABLE[i]
            recovered = arcjya(val)
            assert abs(recovered - angle_deg) < 0.1

    def test_roundtrip_jya(self):
        for angle in [10, 20, 30, 45, 60, 75, 80]:
            val = jya(angle)
            back = arcjya(val)
            assert abs(back - angle) < 0.5


# =====================================================================
#  Convenience Wrappers
# =====================================================================

class TestSsFunctions:
    def test_ss_sin_30(self):
        assert abs(ss_sin(30.0) - 0.5) < 0.005

    def test_ss_cos_60(self):
        assert abs(ss_cos(60.0) - 0.5) < 0.005

    def test_ss_arcsin_half(self):
        assert abs(ss_arcsin(0.5) - 30.0) < 0.5

    def test_ss_sin_cos_identity(self):
        for angle in [15, 30, 45, 60, 75]:
            s = ss_sin(float(angle))
            c = ss_cos(float(angle))
            assert abs(s * s + c * c - 1.0) < 0.01


# =====================================================================
#  Bhuja / Koti
# =====================================================================

class TestBhujaKoti:
    def test_first_quadrant(self):
        b, k = get_bhuja_koti(45.0)
        assert b == pytest.approx(45.0)
        assert k == pytest.approx(45.0)

    def test_second_quadrant(self):
        b, k = get_bhuja_koti(120.0)
        assert b == pytest.approx(60.0)
        assert k == pytest.approx(30.0)

    def test_third_quadrant(self):
        b, k = get_bhuja_koti(200.0)
        assert b == pytest.approx(20.0)
        assert k == pytest.approx(70.0)

    def test_fourth_quadrant(self):
        b, k = get_bhuja_koti(350.0)
        assert b == pytest.approx(10.0)
        assert k == pytest.approx(80.0)

    def test_sum_always_90(self):
        for angle in range(0, 360, 15):
            b, k = get_bhuja_koti(float(angle))
            assert abs(b + k - 90.0) < 0.001

    def test_boundary_0(self):
        b, k = get_bhuja_koti(0.0)
        assert b == pytest.approx(0.0)
        assert k == pytest.approx(90.0)

    def test_boundary_90(self):
        b, k = get_bhuja_koti(90.0)
        assert b == pytest.approx(90.0)
        assert k == pytest.approx(0.0)


class TestQuadrant:
    def test_q1(self):
        assert get_quadrant(45.0) == 1

    def test_q2(self):
        assert get_quadrant(135.0) == 2

    def test_q3(self):
        assert get_quadrant(225.0) == 3

    def test_q4(self):
        assert get_quadrant(315.0) == 4

    def test_boundary_90(self):
        assert get_quadrant(90.0) == 2

    def test_boundary_180(self):
        assert get_quadrant(180.0) == 3

    def test_boundary_270(self):
        assert get_quadrant(270.0) == 4

    def test_wrap(self):
        assert get_quadrant(400.0) == 1


class TestIsOddQuadrant:
    def test_q1_odd(self):
        assert is_odd_quadrant(45.0) is True

    def test_q2_even(self):
        assert is_odd_quadrant(135.0) is False

    def test_q3_odd(self):
        assert is_odd_quadrant(225.0) is True

    def test_q4_even(self):
        assert is_odd_quadrant(315.0) is False


# =====================================================================
#  Table Accuracy Report
# =====================================================================

class TestTableAccuracy:
    def test_returns_24_entries(self):
        report = table_accuracy_report()
        assert len(report) == 24

    def test_all_errors_small(self):
        report = table_accuracy_report()
        for angle, stats in report.items():
            assert stats["error"] < 5.0, f"Large error at {angle}°"

    def test_has_expected_keys(self):
        report = table_accuracy_report()
        first = list(report.values())[0]
        assert "ss_jya" in first
        assert "modern_val" in first
        assert "error" in first
        assert "error_pct" in first


# =====================================================================
#  Part 2: Manda & Sighra Corrections
# =====================================================================

class TestMandaEpicycleConstants:
    def test_all_seven_planets(self):
        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            assert p in MANDA_EPICYCLE

    def test_sun_epicycle(self):
        ep = MANDA_EPICYCLE["Sun"]
        # SS ii.34: 14 deg at even quadrants, 20 min less at odd
        assert ep.even == 14.0
        assert abs(ep.odd - (13 + 40 / 60)) < 1e-9

    def test_mars_epicycle_largest(self):
        assert MANDA_EPICYCLE["Mars"].even == 75.0


class TestSighraEpicycleConstants:
    def test_five_planets(self):
        assert len(SIGHRA_EPICYCLE) == 5

    def test_no_sun_moon(self):
        assert "Sun" not in SIGHRA_EPICYCLE
        assert "Moon" not in SIGHRA_EPICYCLE

    def test_venus_largest(self):
        assert SIGHRA_EPICYCLE["Venus"].even == 262.0

    def test_saturn_smallest(self):
        assert SIGHRA_EPICYCLE["Saturn"].even == 39.0


class TestCorrectedMandaEpicycle:
    def test_at_zero_kendra(self):
        # kendra 0 = end of even quadrant (apsis line) -> even size
        val = corrected_manda_epicycle("Sun", 0.0)
        assert val == MANDA_EPICYCLE["Sun"].even

    def test_at_90_kendra(self):
        # kendra 90 = end of odd quadrant -> odd size
        val = corrected_manda_epicycle("Sun", 90.0)
        assert val == MANDA_EPICYCLE["Sun"].odd

    def test_interpolation_sine(self):
        # SS ii.38: even + (odd - even) * sin(bhuja)
        import math
        val = corrected_manda_epicycle("Sun", 45.0)
        ep = MANDA_EPICYCLE["Sun"]
        expected = ep.even + (ep.odd - ep.even) * math.sin(math.radians(45))
        assert abs(val - expected) < 1e-9

    def test_invalid_planet_raises(self):
        with pytest.raises(ValueError):
            corrected_manda_epicycle("Pluto", 0.0)


class TestMandaCorrection:
    def test_zero_kendra_gives_zero(self):
        corr = manda_correction("Sun", 100.0, 100.0)
        assert abs(corr) < 0.01

    def test_returns_bounded(self):
        jd = julian_day(628, 1, 1)
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            from suryasiddhanta.ch01_mean_motions import mean_longitude as ml, mandocca_longitude as ma
            corr = manda_correction(planet, ml(planet, jd), ma(planet, jd))
            assert -20 < corr < 20, f"{planet} manda_corr {corr} out of bounds"

    def test_sun_small_correction(self):
        jd = julian_day(628, 1, 1)
        from suryasiddhanta.ch01_mean_motions import mean_longitude as ml, mandocca_longitude as ma
        corr = manda_correction("Sun", ml("Sun", jd), ma("Sun", jd))
        assert abs(corr) < 3.0

    def test_sign_flips_at_180(self):
        """
        Validates the manda sign against SS Ch.2 v.29/v.45.

        The SS manda kendra is mandocca - graha: the phala is added when that
        kendra is under 180 deg (graha before apogee, speeding up) and
        subtracted when over 180 deg (graha past apogee, slowing down).
        Expected: graha 90 deg past apogee gets a negative phala; graha 90 deg
        before apogee (270 deg past) gets a positive one.
        """
        corr1 = manda_correction("Mars", 100.0, 10.0)  # graha - apogee = 90
        corr2 = manda_correction("Mars", 280.0, 10.0)  # graha - apogee = 270
        assert corr1 < 0
        assert corr2 > 0

    def test_sun_equation_of_centre_tracks_modern_formula(self):
        """
        Validates the Sun's true longitude against the standard equation of
        centre over a full year.

        The SS Sun differs from the modern one by a near-constant offset
        (ayanamsha / year-length rounding). With the correct manda sign the
        error is flat to within 1 deg; the inverted sign produced a +/-4 deg
        swing. Expected: spread of (SS tropical - modern) under 1 deg.
        """
        from suryasiddhanta.ch02_true_places import (
            true_longitude_full, sidereal_to_tropical, normalize_signed)
        errs = []
        for k in range(0, 360, 15):
            jd = julian_day(2024, 1, 1) + k
            t = (jd - 2451545.0) / 36525.0
            m = math.radians(357.52911 + 35999.05029 * t)
            c = 1.9146 * math.sin(m) + 0.019993 * math.sin(2 * m)
            modern = (280.46646 + 36000.76983 * t + c) % 360.0
            ss = sidereal_to_tropical(true_longitude_full("Sun", jd)["true_longitude"], jd)
            errs.append(normalize_signed(ss - modern))
        assert max(errs) - min(errs) < 1.0

    def test_invalid_planet_raises(self):
        with pytest.raises(ValueError):
            manda_correction("Pluto", 0.0, 0.0)


class TestMandaLongitude:
    def test_in_range(self):
        jd = julian_day(628, 1, 1)
        for planet in ["Sun", "Moon", "Mars"]:
            from suryasiddhanta.ch01_mean_motions import mean_longitude as ml, mandocca_longitude as ma
            lon = manda_longitude(planet, ml(planet, jd), ma(planet, jd))
            assert 0 <= lon < 360


class TestCorrectedSighraEpicycle:
    def test_at_zero(self):
        val = corrected_sighra_epicycle("Mars", 0.0)
        assert val == SIGHRA_EPICYCLE["Mars"].even

    def test_at_90(self):
        val = corrected_sighra_epicycle("Mars", 90.0)
        assert val == SIGHRA_EPICYCLE["Mars"].odd

    def test_invalid_planet_raises(self):
        with pytest.raises(ValueError):
            corrected_sighra_epicycle("Sun", 0.0)


class TestSighraCorrection:
    def test_zero_kendra_gives_zero(self):
        corr = sighra_correction("Mars", 100.0, 100.0)
        assert abs(corr) < 0.01

    def test_returns_bounded(self):
        jd = julian_day(628, 1, 1)
        for planet in PLANETS_WITH_SIGHRA:
            from suryasiddhanta.ch01_mean_motions import (
                mean_longitude as ml, sighrocca_longitude as sl,
            )
            corr = sighra_correction(planet, ml(planet, jd), sl(planet, jd))
            assert -180 < corr < 180, f"{planet} sighra_corr {corr} out of bounds"

    def test_sign_positive_first_half(self):
        corr = sighra_correction("Mars", 10.0, 100.0)  # kendra = 90
        assert corr > 0

    def test_sign_negative_second_half(self):
        corr = sighra_correction("Mars", 100.0, 10.0)  # kendra = 270
        assert corr < 0

    def test_invalid_planet_raises(self):
        with pytest.raises(ValueError):
            sighra_correction("Sun", 0.0, 0.0)


# =====================================================================
#  Full 4-Step Pipeline
# =====================================================================

class TestTrueLongitudeFull:
    def test_sun_manda_only(self):
        jd = julian_day(628, 1, 1)
        result = true_longitude_full("Sun", jd)
        assert result["steps"] == ["manda_only"]
        assert 0 <= result["true_longitude"] < 360
        assert "sighrocca" not in result

    def test_moon_manda_only(self):
        jd = julian_day(628, 1, 1)
        result = true_longitude_full("Moon", jd)
        assert result["steps"] == ["manda_only"]
        assert 0 <= result["true_longitude"] < 360

    def test_mars_four_steps(self):
        jd = julian_day(628, 1, 1)
        result = true_longitude_full("Mars", jd)
        assert result["steps"] == ["half_sighra", "half_manda", "full_manda", "full_sighra"]
        assert 0 <= result["true_longitude"] < 360
        assert "sighrocca" in result

    def test_all_planets_produce_valid(self):
        jd = julian_day(628, 1, 1)
        for planet in ALL_PLANETS:
            result = true_longitude_full(planet, jd)
            assert 0 <= result["true_longitude"] < 360, f"{planet} out of range"

    def test_all_planets_at_modern_date(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        for planet in ALL_PLANETS:
            result = true_longitude_full(planet, jd)
            assert 0 <= result["true_longitude"] < 360, f"{planet} out of range"

    def test_true_differs_from_mean(self):
        jd = julian_day(628, 1, 1)
        for planet in ALL_PLANETS:
            result = true_longitude_full(planet, jd)
            diff = abs(result["true_longitude"] - result["mean_lon"])
            if diff > 180:
                diff = 360 - diff
            assert diff > 0.001, f"{planet} true == mean (no correction applied)"

    def test_result_has_planet_and_jd(self):
        jd = julian_day(628, 1, 1)
        result = true_longitude_full("Jupiter", jd)
        assert result["planet"] == "Jupiter"
        assert result["jd"] == jd

    def test_mercury_has_sighra_fields(self):
        jd = julian_day(628, 1, 1)
        result = true_longitude_full("Mercury", jd)
        assert "sighra_corr1" in result
        assert "sighra_corr2" in result
        assert "manda_corr1" in result

    def test_venus_has_sighra_fields(self):
        jd = julian_day(628, 1, 1)
        result = true_longitude_full("Venus", jd)
        assert "sighra_kendra" in result


# =====================================================================
#  Part 3: Ayanamsha, compute(), compute_all()
# =====================================================================

class TestAyanamsha:
    def test_zero_at_499_ce(self):
        jd = julian_day(499, 1, 1)
        ayan = ayanamsha(jd)
        assert abs(ayan) < 1.0

    def test_bounded(self):
        for year in [628, 1000, 1582, 2024]:
            jd = julian_day(year, 1, 1, gregorian=(year > 1582))
            ayan = ayanamsha(jd)
            assert -27.0 <= ayan <= 27.0

    def test_positive_after_zero_year(self):
        jd = julian_day(1000, 1, 1)
        assert ayanamsha(jd) > 0

    def test_oscillatory(self):
        jd1 = julian_day(500, 1, 1)
        jd2 = julian_day(2300, 1, 1, gregorian=True)
        a1 = ayanamsha(jd1)
        a2 = ayanamsha(jd2)
        assert a1 * a2 < 0 or abs(a1) < 1 or abs(a2) < 1


class TestSiderealTropical:
    def test_roundtrip(self):
        jd = julian_day(628, 1, 1)
        sid = 100.0
        trop = sidereal_to_tropical(sid, jd)
        back = tropical_to_sidereal(trop, jd)
        assert abs(back - sid) < 0.001

    def test_tropical_greater_when_ayan_positive(self):
        jd = julian_day(1000, 1, 1)
        if ayanamsha(jd) > 0:
            trop = sidereal_to_tropical(100.0, jd)
            assert trop > 100.0


class TestCompute:
    def test_sun_628(self):
        pos = compute("Sun", 628, 1, 1)
        assert pos.planet == "Sun"
        assert 0 <= pos.true_longitude < 360
        assert pos.year == 628
        assert pos.month == 1

    def test_all_planets_628(self):
        for planet in ALL_PLANETS:
            pos = compute(planet, 628, 1, 1)
            assert 0 <= pos.true_longitude < 360, f"{planet} out of range"
            assert pos.planet == planet

    def test_all_planets_2024(self):
        for planet in ALL_PLANETS:
            pos = compute(planet, 2024, 4, 9, gregorian=True)
            assert 0 <= pos.true_longitude < 360

    def test_has_nakshatra(self):
        pos = compute("Jupiter", 628, 1, 1)
        assert "name" in pos.nakshatra
        assert "pada" in pos.nakshatra
        assert 1 <= pos.nakshatra["pada"] <= 4

    def test_has_rashi(self):
        pos = compute("Jupiter", 628, 1, 1)
        assert "name" in pos.rashi
        assert "index" in pos.rashi
        assert 0 <= pos.rashi["index"] < 12

    def test_has_ayanamsha(self):
        pos = compute("Sun", 628, 1, 1)
        assert -27 <= pos.ayanamsha <= 27

    def test_tropical_differs_from_sidereal(self):
        pos = compute("Sun", 628, 1, 1)
        assert pos.tropical_longitude != pos.true_longitude

    def test_sun_no_sighra(self):
        pos = compute("Sun", 628, 1, 1)
        assert pos.sighrocca is None
        assert pos.sighra_kendra is None
        assert pos.sighra_corr is None

    def test_mars_has_sighra(self):
        pos = compute("Mars", 628, 1, 1)
        assert pos.sighrocca is not None
        assert pos.sighra_corr is not None

    def test_str_output(self):
        pos = compute("Jupiter", 628, 1, 1)
        s = str(pos)
        assert "Jupiter" in s
        assert "Nakshatra" in s
        assert "Rashi" in s

    def test_to_dict(self):
        pos = compute("Sun", 628, 1, 1)
        d = pos.to_dict()
        assert "true_longitude" in d
        assert "nakshatra" in d
        assert "rashi" in d
        assert "ayanamsha" in d

    def test_invalid_planet_raises(self):
        with pytest.raises(ValueError):
            compute("Pluto", 628, 1, 1)


class TestComputeAll:
    def test_returns_seven(self):
        positions = compute_all(628, 1, 1)
        assert len(positions) == 7

    def test_all_valid(self):
        positions = compute_all(628, 1, 1)
        for planet, pos in positions.items():
            assert pos.planet == planet
            assert 0 <= pos.true_longitude < 360

    def test_modern_date(self):
        positions = compute_all(2024, 4, 9, gregorian=True)
        assert "Sun" in positions
        assert "Saturn" in positions
        for pos in positions.values():
            assert 0 <= pos.true_longitude < 360

    def test_sun_moon_differ(self):
        positions = compute_all(628, 1, 1)
        assert positions["Sun"].true_longitude != positions["Moon"].true_longitude

    def test_each_has_nakshatra_rashi(self):
        positions = compute_all(628, 1, 1)
        for pos in positions.values():
            assert "name" in pos.nakshatra
            assert "name" in pos.rashi


class TestInnerPlanetElongation:
    """
    Guards the one physical constraint the SS's inner-planet geometry
    cannot violate: Mercury and Venus are carried on sighra epicycles
    centred on the sun's mean place (ii.43-45), so neither can ever
    appear far from the sun.
    """

    def test_mercury_elongation_bounded(self):
        """
        Validates that Mercury stays within 28 deg of the sun, its
        greatest elongation. A failure here means the sighra kendra of
        ii.44 has collapsed — which happens if mean_longitude returns the
        sighrocca of i.31 instead of the sun's mean place (i.29, Burgess
        under i.54), leaving the sighra equation identically zero.
        """
        for year, month, day in [(499, 3, 21), (628, 1, 1), (1999, 8, 11),
                                 (2024, 1, 1), (2024, 4, 15)]:
            greg = year >= 1582
            sun = compute("Sun", year, month, day, gregorian=greg).true_longitude
            mer = compute("Mercury", year, month, day, gregorian=greg).true_longitude
            elong = abs(normalize_signed(mer - sun))
            assert elong <= 28.0, f"{year}-{month:02d}-{day:02d}: Mercury {elong:.2f} deg from sun"

    def test_venus_elongation_bounded(self):
        """
        Validates the same constraint for Venus, whose greatest
        elongation is about 48 deg.
        """
        for year, month, day in [(499, 3, 21), (628, 1, 1), (1999, 8, 11),
                                 (2024, 1, 1), (2024, 4, 15)]:
            greg = year >= 1582
            sun = compute("Sun", year, month, day, gregorian=greg).true_longitude
            ven = compute("Venus", year, month, day, gregorian=greg).true_longitude
            elong = abs(normalize_signed(ven - sun))
            assert elong <= 48.0, f"{year}-{month:02d}-{day:02d}: Venus {elong:.2f} deg from sun"

    def test_sighra_kendra_is_not_degenerate(self):
        """
        Validates that the inner planets actually receive a sighra
        equation. With mean place and sighrocca distinct, sighra_corr2 of
        the four-step process (ii.43-44) must be non-trivial; if the two
        collapse together it rounds to zero and the bug is silent in the
        longitude alone.
        """
        jd = julian_day(2024, 1, 1, gregorian=True)
        for planet in ["Mercury", "Venus"]:
            result = true_longitude_full(planet, jd)
            assert abs(result["sighra_corr2"]) > 0.1, f"{planet} sighra correction vanished"


class TestVikshepa:
    """Celestial latitude per SS Ch.2 v.56-57."""

    def test_jupiter_book_example(self):
        """
        Validates the book's worked Jupiter shara (Samvat 1978 Vasant Panchami).

        Vikshepa kendra 3s 27d26'35", madhya vikshepa 60', antya karna 3608.
        Expected: 50'43" (50.72') north.
        """
        from suryasiddhanta.ch02_true_places import spashta_vikshepa
        lat = spashta_vikshepa(3 * 30 + 27 + 26 / 60 + 35 / 3600, 60.0, 3608.0)
        assert abs(lat - (50 + 43 / 60)) < 0.1

    def test_sign_follows_kendra_half(self):
        """North (positive) when kendra < 180, south otherwise."""
        from suryasiddhanta.ch02_true_places import spashta_vikshepa
        assert spashta_vikshepa(90.0, 120.0) > 0
        assert spashta_vikshepa(270.0, 120.0) < 0

    def test_planet_latitudes_within_limits(self):
        """
        Expected: each planet's latitude stays under its maximum
        (Moon 270', others up to ~1.3x mean for small sighra karna).
        """
        from suryasiddhanta.ch02_true_places import planet_latitude
        jd = julian_day(2024, 4, 1.0)
        assert abs(planet_latitude("Moon", jd)) <= 270.0
        assert planet_latitude("Sun", jd) == 0.0
        for p, cap in [("Mars", 200), ("Jupiter", 90), ("Saturn", 200),
                       ("Mercury", 200), ("Venus", 200)]:
            assert abs(planet_latitude(p, jd)) <= cap


class TestBookWorkedExamples:
    """Checks against worked examples in the book's Chapter 2 and 3 commentary."""

    def test_sine_table_interpolation(self):
        """
        Validates SS Ch.2 v.31-32 interpolation: the book's Rsin 66 deg
        example gives 3140, and the inverse recovers 66 deg.
        """
        assert abs(jya(66.0) - 3140.0) < 1.0
        assert abs(arcjya(3140.0) - 66.0) < 0.05

    def test_ayanamsha_samvat_1982(self):
        """
        Validates the trepidation rule (SS Ch.3 v.9-10) against the book's
        example for Samvat 1982 Mesha (Kali year 5026): 21d23'24".
        """
        from suryasiddhanta.ch01_mean_motions import KALI_EPOCH_JD, SIDEREAL_YEAR_DAYS
        jd = KALI_EPOCH_JD + 5026 * SIDEREAL_YEAR_DAYS
        d, m, s = to_dms(ayanamsha(jd))
        assert (d, m) == (21, 23) and abs(s - 24.0) < 1.0

    def test_burgess_ayanamsha_1860(self):
        """Burgess's own example: 1860-01-01 gives 20d24'38.67"."""
        d, m, s = to_dms(ayanamsha(julian_day(1860, 1, 1.0)))
        assert (d, m) == (20, 24) and abs(s - 38.67) < 0.1

    def test_jupiter_pipeline_matches_book_example(self):
        """
        Validates the full four-step pipeline against the book's Jupiter
        example (Samvat 1979 Magha sudi 5 midnight, Ujjain, JD 2423441.5).

        Expected: second manda phala about -166' (book -2d46'), second sighra
        phala about 647', true longitude within 0.2 deg of the book's
        6s 27d53'37" (207.89 deg).
        """
        d = true_longitude_full("Jupiter", 2423441.5)
        assert abs(d["manda_corr2"] * 60 - (-166.0)) < 2.0
        assert abs(d["sighra_corr2"] * 60 - 647.0) < 2.0
        assert abs(d["true_longitude"] - (6 * 30 + 27 + 53 / 60)) < 0.2
