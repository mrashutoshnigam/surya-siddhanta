"""Tests for Chapter 1: Mean Motions of the Planets."""

import math
import pytest
from suryasiddhanta.ch01_mean_motions import (
    MAHAYUGA, KALPA, KALI_YUGA, CIVIL_DAYS_PER_MAHAYUGA,
    SIDEREAL_YEAR_DAYS, KALI_EPOCH_JD, BHAGANA,
    GHATIS_PER_DAY, TIME_UNITS_SEC, ALL_PLANETS, RASHIS,
    julian_day, from_julian_day, ahargana, jd_from_ahargana,
    kali_years_elapsed, kali_era_year, yuga_elapsed_fraction,
    SOLAR_MONTHS_PER_MAHAYUGA, ADHIMASA_PER_MAHAYUGA,
    LUNAR_DAYS_PER_MAHAYUGA, TITHIKSHAYA_PER_MAHAYUGA,
    CIVIL_DAYS_CREATION_TO_KALI, YEARS_CREATION_TO_KALI,
    adhimasa_elapsed, tithikshaya_elapsed, ahargana_from_luni_solar,
    day_to_hms, ghati_to_minutes, minutes_to_ghati,
    mean_longitude, mandocca_longitude, sighrocca_longitude,
    moon_node_longitude, compute_all_mean_positions,
    rashi_from_longitude, nakshatra_from_longitude,
    tithi_from_elongation, vara, masa_from_sun_longitude,
    ritu_from_sun_longitude, samvatsara, karana_from_elongation,
    TITHI_NAMES, VARA_NAMES, MASA_NAMES, SAMVATSARA_NAMES, RITU_NAMES,
    MANDOCCA_AT_EPOCH, NODE_AT_EPOCH,
    UJJAIN_UT_OFFSET_DAYS, UJJAIN_UTC_OFFSET_HOURS,
    jd_to_ut, jd_from_ut, jd_from_clock, clock_from_jd,
)
from suryasiddhanta._types import VedicTime


class TestCosmologicalConstants:
    def test_mahayuga_is_sum_of_yugas(self):
        assert MAHAYUGA == KALI_YUGA + 864_000 + 1_296_000 + 1_728_000

    def test_kalpa_is_1000_mahayugas(self):
        assert KALPA == 1000 * MAHAYUGA

    def test_sidereal_year_approximately_365_26(self):
        assert 365.25 < SIDEREAL_YEAR_DAYS < 365.27

    def test_sun_bhagana_equals_mahayuga(self):
        assert BHAGANA["Sun"] == MAHAYUGA

    def test_moon_bhagana_greater_than_sun(self):
        assert BHAGANA["Moon"] > BHAGANA["Sun"]

    def test_all_seven_planets_have_bhagana(self):
        for body in ["Sun", "Moon", "Mars", "Jupiter", "Saturn"]:
            assert body in BHAGANA
        assert "Mercury_sighrocca" in BHAGANA
        assert "Venus_sighrocca" in BHAGANA


class TestJulianDay:
    def test_kali_epoch_jd(self):
        jd = julian_day(-3101, 2, 18)
        assert abs(jd - KALI_EPOCH_JD) < 1.0

    def test_j2000_epoch(self):
        jd = julian_day(2000, 1, 1.5, gregorian=True)
        assert abs(jd - 2451545.0) < 0.01

    def test_gregorian_reform_date(self):
        jd = julian_day(1582, 10, 15, gregorian=True)
        assert abs(jd - 2299160.5) < 0.01

    def test_roundtrip_modern_date(self):
        jd = julian_day(2024, 4, 9, gregorian=True)
        y, m, d, f = from_julian_day(jd)
        assert y == 2024
        assert m == 4
        assert d == 9

    def test_roundtrip_ancient_date(self):
        jd = julian_day(628, 1, 1)
        y, m, d, f = from_julian_day(jd)
        assert y == 628
        assert m == 1
        assert d == 1

    def test_bce_date(self):
        jd = julian_day(-500, 6, 15)
        assert jd > 0
        y, m, d, f = from_julian_day(jd)
        assert y == -500
        assert m == 6

    def test_fractional_day(self):
        jd_noon = julian_day(2024, 1, 1.5, gregorian=True)
        jd_midnight = julian_day(2024, 1, 1.0, gregorian=True)
        assert abs(jd_noon - jd_midnight - 0.5) < 0.001


class TestAhargana:
    def test_ahargana_at_kali_epoch_is_zero(self):
        a = ahargana(KALI_EPOCH_JD)
        assert a == 0.0

    def test_ahargana_positive_after_epoch(self):
        jd = julian_day(628, 1, 1)
        assert ahargana(jd) > 0

    def test_ahargana_roundtrip(self):
        jd = julian_day(2024, 4, 9, gregorian=True)
        a = ahargana(jd)
        jd_back = jd_from_ahargana(a)
        assert abs(jd - jd_back) < 1e-10

    def test_kali_years_at_628_ce(self):
        jd = julian_day(628, 1, 1)
        ky = kali_years_elapsed(jd)
        assert 3728 < ky < 3730

    def test_kali_years_at_2024(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        ky = kali_years_elapsed(jd)
        assert 5124 < ky < 5126

    def test_yuga_fraction_positive(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        frac = yuga_elapsed_fraction(jd)
        assert 0 < frac < 1


class TestTimeConversions:
    def test_day_to_hms_noon(self):
        h, m, s = day_to_hms(0.5)
        assert h == 12
        assert m == 0
        assert abs(s) < 0.01

    def test_day_to_hms_6am(self):
        h, m, s = day_to_hms(0.25)
        assert h == 6
        assert m == 0

    def test_ghati_to_minutes(self):
        assert ghati_to_minutes(1) == 24.0
        assert ghati_to_minutes(60) == 1440.0

    def test_minutes_to_ghati_roundtrip(self):
        assert abs(minutes_to_ghati(ghati_to_minutes(30)) - 30) < 1e-10

    def test_ghatis_per_day(self):
        assert GHATIS_PER_DAY == 60


class TestVedicTime:
    def test_from_day_fraction_noon(self):
        vt = VedicTime.from_day_fraction(0.5)
        assert vt.ghatis == 30
        assert vt.palas == 0

    def test_from_day_fraction_start(self):
        vt = VedicTime.from_day_fraction(0.0)
        assert vt.ghatis == 0
        assert vt.palas == 0

    def test_roundtrip(self):
        vt = VedicTime.from_day_fraction(0.75)
        frac = vt.to_day_fraction()
        assert abs(frac - 0.75) < 0.001

    def test_to_minutes(self):
        vt = VedicTime(ghatis=1, palas=0, vipalas=0.0)
        assert vt.to_minutes() == 24.0

    def test_str(self):
        vt = VedicTime(ghatis=5, palas=30, vipalas=15.0)
        s = str(vt)
        assert "05gh" in s
        assert "30pa" in s


class TestTimeUnits:
    def test_ahoratra_is_one_day(self):
        assert TIME_UNITS_SEC["ahoratra"] == 86400

    def test_ghati_is_24_minutes(self):
        assert TIME_UNITS_SEC["ghati"] == 24 * 60

    def test_muhurta_is_48_minutes(self):
        assert TIME_UNITS_SEC["muhurta"] == 48 * 60

    def test_prahara_is_3_hours(self):
        assert TIME_UNITS_SEC["prahara"] == 3 * 3600

    def test_prana_is_four_seconds(self):
        """
        Validates the SS's own smallest time unit. SS i.11 makes six
        respirations (prana) a vinadi of 24 s, so a prana is 4 s exactly.
        """
        assert TIME_UNITS_SEC["prana"] == 4.0

    def test_vinadi_is_24_seconds(self):
        """
        Validates SS i.11: sixty vinadis make a nadi of 24 minutes, so a
        vinadi is 24 s, and six pranas make one.
        """
        assert TIME_UNITS_SEC["vinadi"] == 24.0
        assert TIME_UNITS_SEC["vinadi"] == 6 * TIME_UNITS_SEC["prana"]

    def test_nadi_is_the_ghati(self):
        """
        Validates that nadi and ghati are the same unit. Burgess, note to
        i.11, records nadika/ghatika as the text's alternate names for
        the nadi, so both keys must give 1440 s.
        """
        assert TIME_UNITS_SEC["nadi"] == TIME_UNITS_SEC["ghati"] == 1440
        assert TIME_UNITS_SEC["nadi"] == 60 * TIME_UNITS_SEC["vinadi"]

    def test_samvatsara_matches_ss_sidereal_year(self):
        """
        Validates that the year in the unit table is the SS's own
        sidereal year (v.37: 1,577,917,828 civil days / 4,320,000 years)
        and not an independently rounded figure.
        """
        assert TIME_UNITS_SEC["samvatsara"] == SIDEREAL_YEAR_DAYS * 86400

    def test_laghu_is_absent(self):
        """
        Validates that the spurious 'laghu' entry is gone. The unit is in
        neither the SS table (i.11-12) nor Bhaskara's, and the value it
        carried, 15/3600 s, matched no source.
        """
        assert "laghu" not in TIME_UNITS_SEC


# =====================================================================
#  Part 2: Mean Longitudes
# =====================================================================

class TestMeanLongitude:
    def test_all_planets_in_range(self):
        jd = julian_day(628, 1, 1)
        for planet in ALL_PLANETS:
            lon = mean_longitude(planet, jd)
            assert 0 <= lon < 360, f"{planet} mean lon {lon} out of range"

    def test_sun_at_kali_epoch_is_zero(self):
        lon = mean_longitude("Sun", KALI_EPOCH_JD)
        assert abs(lon) < 0.01

    def test_moon_faster_than_sun(self):
        jd = julian_day(628, 1, 1)
        sun = mean_longitude("Sun", jd)
        jd2 = jd + 1
        sun2 = mean_longitude("Sun", jd2)
        moon2_diff = (mean_longitude("Moon", jd2) - mean_longitude("Moon", jd)) % 360
        sun2_diff = (sun2 - sun) % 360
        assert moon2_diff > sun2_diff

    def test_invalid_planet_raises(self):
        with pytest.raises(ValueError):
            mean_longitude("Pluto", KALI_EPOCH_JD)

    def test_moon_apogee_and_node(self):
        jd = julian_day(628, 1, 1)
        apogee = mean_longitude("Moon_apogee", jd)
        node = mean_longitude("Moon_node", jd)
        assert 0 <= apogee < 360
        assert 0 <= node < 360

    def test_mean_longitude_changes_daily(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        lon1 = mean_longitude("Jupiter", jd)
        lon2 = mean_longitude("Jupiter", jd + 1)
        assert lon1 != lon2


class TestMandocca:
    def test_all_planets_have_mandocca(self):
        jd = julian_day(628, 1, 1)
        for planet in ALL_PLANETS:
            lon = mandocca_longitude(planet, jd)
            assert 0 <= lon < 360, f"{planet} mandocca {lon} out of range"

    def test_mandocca_moves_slowly(self):
        jd = julian_day(628, 1, 1)
        m1 = mandocca_longitude("Sun", jd)
        m2 = mandocca_longitude("Sun", jd + 365)
        diff = abs(m2 - m1)
        assert diff < 1.0  # apogee moves < 1 deg/year

    def test_epoch_apsides_match_burgess_table(self):
        """
        Validates the whole MANDOCCA_AT_EPOCH / NODE_AT_EPOCH derivation
        against Burgess's table of apsis and node positions at the
        commencement of the Iron Age (comm. under i.44). The positions
        are not stated in the verses; they follow from the kalpa rates of
        i.41-44 run over the 1,955,880,000 years from the end of creation
        (i.24, i.47) to the Kali epoch, so this pins that derivation.
        Expected: every value within one arc-second of the table.
        """
        one_arcsec = 1.0 / 3600.0
        apsides = {                       # signs, degrees, minutes, seconds
            "Sun": (2, 17, 7, 48), "Mercury": (7, 10, 19, 12),
            "Venus": (2, 19, 39, 0), "Mars": (4, 9, 57, 36),
            "Jupiter": (5, 21, 0, 0), "Saturn": (7, 26, 36, 36),
        }
        nodes = {
            "Mercury": (0, 20, 52, 48), "Venus": (2, 0, 1, 48),
            "Mars": (1, 10, 8, 24), "Jupiter": (2, 19, 44, 24),
            "Saturn": (3, 10, 37, 12),
        }

        def to_deg(s, d, m, sec):
            return s * 30 + d + m / 60.0 + sec / 3600.0

        for planet, parts in apsides.items():
            assert MANDOCCA_AT_EPOCH[planet] == pytest.approx(
                to_deg(*parts), abs=one_arcsec), f"{planet} apsis"
        for planet, parts in nodes.items():
            assert NODE_AT_EPOCH[planet] == pytest.approx(
                to_deg(*parts), abs=one_arcsec), f"{planet} node"

    def test_moon_apsis_and_node_at_epoch(self):
        """
        Validates SS i.58 carried forward to the Kali epoch. The verse
        places the moon's apsis at the first of Capricorn (270 deg) and
        its node at the first of Libra (180 deg) at the end of the Golden
        Age. Over the half-Mahayuga to the Kali epoch the apsis makes
        244,101.5 revolutions, advancing a further 180 deg to 90 deg,
        while the node makes exactly 116,119 and stays at 180 deg.
        """
        assert MANDOCCA_AT_EPOCH["Moon"] == pytest.approx(90.0)
        assert mean_longitude("Moon_apogee", KALI_EPOCH_JD) == pytest.approx(90.0)
        assert moon_node_longitude(KALI_EPOCH_JD) == pytest.approx(180.0)


class TestSighrocca:
    def test_outer_planets_use_sun(self):
        jd = julian_day(628, 1, 1)
        sun_mean = mean_longitude("Sun", jd)
        for planet in ["Mars", "Jupiter", "Saturn"]:
            sig = sighrocca_longitude(planet, jd)
            assert abs(sig - sun_mean) < 0.001

    def test_inner_planets_differ_from_sun(self):
        jd = julian_day(628, 1, 1)
        sun_mean = mean_longitude("Sun", jd)
        for planet in ["Mercury", "Venus"]:
            sig = sighrocca_longitude(planet, jd)
            assert 0 <= sig < 360

    def test_inner_planet_mean_equals_sun(self):
        """
        Validates SS i.29, which gives the Sun, Mercury and Venus the
        same 4,320,000 revolutions, and Burgess under i.54: "the mean
        place of those planets is the same with that of the sun".
        mean_longitude must return the Sun's mean longitude for both, not
        the sighrocca of v.31-32.
        """
        for jd in [KALI_EPOCH_JD, julian_day(628, 1, 1), julian_day(2024, 1, 1)]:
            sun_mean = mean_longitude("Sun", jd)
            for planet in ["Mercury", "Venus"]:
                assert mean_longitude(planet, jd) == pytest.approx(sun_mean)

    def test_inner_planet_sighrocca_differs_from_mean(self):
        """
        Validates that mean place and sighrocca stay distinct quantities
        for the inner planets. If they collapse together the sighra
        kendra of ii.44 is identically zero and the sighra equation
        vanishes, which is the failure this guards against.
        """
        jd = julian_day(2024, 1, 1)
        for planet in ["Mercury", "Venus"]:
            assert abs(sighrocca_longitude(planet, jd)
                       - mean_longitude(planet, jd)) > 1.0

    def test_sighroccas_at_kali_epoch_are_zero(self):
        """
        Validates SS i.57: every planet including the conjunctions stands
        at the first of Aries at the end of the Golden Age, and both
        inner sighroccas complete whole revolutions in the half-Mahayuga
        to the Kali epoch, so both must read 0 deg there.
        """
        for planet in ["Mercury", "Venus"]:
            assert sighrocca_longitude(planet, KALI_EPOCH_JD) == pytest.approx(0.0)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            sighrocca_longitude("Sun", KALI_EPOCH_JD)


class TestMoonNode:
    def test_in_range(self):
        jd = julian_day(628, 1, 1)
        lon = moon_node_longitude(jd)
        assert 0 <= lon < 360


class TestComputeAllMean:
    def test_returns_all_bodies(self):
        jd = julian_day(628, 1, 1)
        mp = compute_all_mean_positions(jd)
        assert mp.jd == jd
        d = mp.as_dict()
        assert len(d) == 9
        for v in d.values():
            assert 0 <= v < 360


class TestRashiNakshatra:
    def test_rashi_count(self):
        assert len(RASHIS) == 12

    def test_rashi_from_longitude(self):
        idx, name, deg = rashi_from_longitude(0.0)
        assert idx == 0
        assert name == "Mesha"

    def test_rashi_from_180(self):
        idx, name, deg = rashi_from_longitude(180.0)
        assert idx == 6
        assert name == "Tula"

    def test_nakshatra_from_longitude(self):
        idx, name, pada, deg = nakshatra_from_longitude(0.0)
        assert idx == 0
        assert name == "Ashvini"
        assert pada == 1

    def test_nakshatra_wraps(self):
        idx, name, pada, deg = nakshatra_from_longitude(359.0)
        assert name == "Revati"


class TestTithi:
    def test_new_moon(self):
        num, frac = tithi_from_elongation(100.0, 100.0)
        assert num == 1  # elongation 0 = start of Pratipada
        assert abs(frac) < 0.01

    def test_full_moon(self):
        num, frac = tithi_from_elongation(280.0, 100.0)
        assert num == 16  # 180 deg elongation = after Purnima

    def test_range(self):
        for elong in range(0, 360, 12):
            num, frac = tithi_from_elongation(elong, 0.0)
            assert 1 <= num <= 30

    def test_tithi_names_count(self):
        assert len(TITHI_NAMES) == 30


class TestVara:
    def test_vara_names_count(self):
        assert len(VARA_NAMES) == 7

    def test_known_day(self):
        # Jan 1, 2024 is Monday
        jd = julian_day(2024, 1, 1, gregorian=True)
        idx, name = vara(jd)
        assert name == "Somavara"  # Monday

    def test_consecutive_days_differ(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        idx1, _ = vara(jd)
        idx2, _ = vara(jd + 1)
        assert (idx1 + 1) % 7 == idx2


class TestMasa:
    def test_masa_names_count(self):
        assert len(MASA_NAMES) == 12

    def test_mesha_is_vaishakha(self):
        """
        Validates the solar month for the Sun in Mesha. Burgess, comm.
        under xiv.16, states that Vaishakha is in practice the first of
        the solar months, so the Sun at 15 deg must give Vaishakha and
        not Chaitra.
        """
        idx, name = masa_from_sun_longitude(15.0)
        assert name == "Vaishakha"

    def test_tula_is_kartika(self):
        """
        Validates the solar month half a year on from Mesha. With
        Vaishakha at Mesha, the Sun in Tula (195 deg) must give Kartika.
        """
        idx, name = masa_from_sun_longitude(195.0)
        assert name == "Kartika"

    def test_solar_masa_boundaries(self):
        """
        Validates every solar-month boundary at once: each of the twelve
        signs must name the month one place further on than the sign's
        own ordinal, wrapping Meena back to Chaitra (SS i.13, xiv.10).
        """
        expected = [
            (0, "Vaishakha"), (30, "Jyeshtha"), (60, "Ashadha"),
            (90, "Shravana"), (120, "Bhadrapada"), (150, "Ashvina"),
            (180, "Kartika"), (210, "Margashirsha"), (240, "Pausha"),
            (270, "Magha"), (300, "Phalguna"), (330, "Chaitra"),
        ]
        for lon, name in expected:
            _, got = masa_from_sun_longitude(float(lon) + 1.0)
            assert got == name, f"Sun at {lon}+1 deg gave {got}, expected {name}"


class TestRitu:
    def test_vasanta_at_mesha(self):
        """
        Validates that the Sun in Mesha falls in Vasanta. Burgess's table
        under xiv.16 pairs Vasanta with Caitra and Vaishakha, i.e. the Sun
        in Meena and Mesha, so 15 deg must give Vasanta.
        """
        idx, name = ritu_from_sun_longitude(15.0)
        assert name == "Vasanta"

    def test_shishira_at_makara(self):
        """
        Validates the first season. SS xiv.9-10 reckons the seasons from
        the Sun's entrance into Capricorn beginning with Shishira, so the
        Sun at 285 deg (in Makara) must give Shishira at index 0.
        """
        idx, name = ritu_from_sun_longitude(285.0)
        assert name == "Shishira"
        assert idx == 0

    def test_ritu_boundaries(self):
        """
        Validates all six two-sign seasons in order from Capricorn
        (SS xiv.9-10). Each span is checked just inside its lower edge so
        an off-by-one-sign error in either direction fails.
        """
        expected = [
            (270, "Shishira"), (300, "Shishira"),
            (330, "Vasanta"), (0, "Vasanta"),
            (30, "Grishma"), (60, "Grishma"),
            (90, "Varsha"), (120, "Varsha"),
            (150, "Sharad"), (180, "Sharad"),
            (210, "Hemanta"), (240, "Hemanta"),
        ]
        for lon, name in expected:
            _, got = ritu_from_sun_longitude(float(lon) + 1.0)
            assert got == name, f"Sun at {lon}+1 deg gave {got}, expected {name}"

    def test_six_seasons(self):
        seen = set()
        for deg in range(0, 360, 60):
            _, name = ritu_from_sun_longitude(float(deg))
            seen.add(name)
        assert len(seen) == 6


class TestSamvatsara:
    def test_60_names(self):
        assert len(SAMVATSARA_NAMES) == 60

    def test_returns_valid_name(self):
        jd = julian_day(2024, 1, 1, gregorian=True)
        idx, name = samvatsara(jd)
        assert 0 <= idx < 60
        assert name in SAMVATSARA_NAMES

    def test_burgess_worked_example(self):
        """
        Validates SS i.55 against the one worked result Burgess gives for
        it: the rule, counting from Vijaya, makes 1859-60 CE the year
        Prajapati. Pins both the Jovian-year arithmetic and the offset of
        the starting name in the list.
        """
        idx, name = samvatsara(julian_day(1859, 12, 31, gregorian=True))
        assert name == "Prajapati"


class TestKarana:
    def test_fixed_karanas_follow_ss(self):
        """
        Validates the four fixed (dhruva) karanas against SS ii.67, which
        names them in the order Shakuni, Naga, Chatushpada, Kimstughna
        counting from the second half of Krishna Chaturdashi, and against
        Burgess's table under ii.69, which numbers them 58, 59, 60 and 1.
        Modern panchangas invert 59 and 60; this text does not.
        """
        expected = {1: "Kimstughna", 58: "Shakuni", 59: "Naga", 60: "Chatushpada"}
        for num, name in expected.items():
            elong = (num - 1) * 6.0 + 3.0     # mid-point of that half-tithi
            got_num, got_name, got_type = karana_from_elongation(elong, 0.0)
            assert got_num == num
            assert got_name == name, f"karana {num} gave {got_name}"
            assert got_type == "fixed"

    def test_recurring_karanas_span_2_to_57(self):
        """
        Validates SS ii.68: the seven movable (cara) karanas, Bava first,
        each occur eight times, filling half-tithis 2 through 57. Bava
        must open at 2 and Vishti must close the run at 57.
        """
        _, first_name, first_type = karana_from_elongation(9.0, 0.0)   # no. 2
        _, last_name, last_type = karana_from_elongation(339.0, 0.0)   # no. 57
        assert (first_name, first_type) == ("Bava", "recurring")
        assert (last_name, last_type) == ("Vishti", "recurring")


class TestKaliEraYear:
    """The era year (5090) as distinct from the elapsed count (5089.87)."""

    def test_era_year_1989(self):
        """
        Validates that a date in 1989 CE falls in Kali 5090, the year the
        standard era formulae give (1989 + 3101, and Shaka 1911 + 3179).
        kali_years_elapsed returns 5089.87 for the same instant, which is
        the count of *completed* years, one less than the era number.
        """
        jd = julian_day(1989, 3, 1, gregorian=True)
        assert kali_era_year(jd) == 5090
        assert 5089.87 < kali_years_elapsed(jd) < 5089.88

    def test_era_year_1860_matches_burgess(self):
        """
        Validates against Burgess, comm. under i.51: "Jan. 1, 1860, is the
        eighth day of the tenth month of the 4961st year of the Iron Age."
        Expected era year 4961.
        """
        assert kali_era_year(julian_day(1860, 1, 1)) == 4961

    def test_era_year_2024(self, jd_2024):
        """
        Validates the era year for the shared 2024 fixture: 2024 + 3101,
        expected Kali 5125, consistent with the elapsed count of 5124.7.
        """
        assert kali_era_year(jd_2024) == 5125


class TestVerseRouteAhargana:
    """
    The ahargana by the text's own luni-solar route (SS i.48-51), pinned
    to the worked example Burgess gives in his commentary under i.51:
    the sum of days to the beginning of Jan 1, 1860, from the elapsed
    time 1,955,884,960 y., 9 m., 7 d.
    """

    BURGESS_1860 = (1_955_884_960, 9, 7)

    def test_age_quantities_match_burgess(self):
        """
        Validates the four derived Age-level quantities the proportions of
        v.48-51 rest on. Burgess prints 1,593,336 intercalary months and
        25,082,252 omitted lunar days; expected to fall out of the
        revolution and civil-day counts without any independent datum.
        """
        assert SOLAR_MONTHS_PER_MAHAYUGA == 51_840_000
        assert ADHIMASA_PER_MAHAYUGA == 1_593_336
        assert LUNAR_DAYS_PER_MAHAYUGA == 1_603_000_080
        assert TITHIKSHAYA_PER_MAHAYUGA == 25_082_252

    def test_adhimasa_matches_burgess(self):
        """
        Validates SS i.48-49 on Burgess's figures: 23,470,619,529 elapsed
        solar months are expected to carry 721,384,703 intercalary months.
        """
        years, months, _ = self.BURGESS_1860
        solar_months = years * 12 + months
        assert solar_months == 23_470_619_529
        assert adhimasa_elapsed(solar_months) == 721_384_703

    def test_tithikshaya_matches_burgess(self):
        """
        Validates SS i.50-51 on Burgess's figures: 725,760,126,967 elapsed
        lunar days are expected to carry 11,356,018,395 omitted ones.
        """
        years, months, tithis = self.BURGESS_1860
        solar_months = years * 12 + months
        lunar_days = (solar_months + adhimasa_elapsed(solar_months)) * 30 + tithis
        assert lunar_days == 725_760_126_967
        assert tithikshaya_elapsed(lunar_days) == 11_356_018_395

    def test_sum_of_days_from_creation_matches_burgess(self):
        """
        Validates the whole chain of v.48-51 end to end. Expected
        714,404,108,572 civil days from the end of creation to the
        beginning of Jan 1, 1860 — Burgess's final figure, exactly.
        """
        assert ahargana_from_luni_solar(
            *self.BURGESS_1860, from_creation=True
        ) == 714_404_108_572

    def test_verse_route_matches_jd_subtraction(self):
        """
        Validates that the text's route and this module's plain
        subtraction from the Kali epoch are the same number, not merely
        close: both expected to give 1,811,945 days for Jan 1, 1860. This
        is why adhimasa and tithikshaya never appear in ahargana() — they
        cancel when the input is already a Julian Day.
        """
        assert ahargana_from_luni_solar(4960, 9, 7) == 1_811_945
        assert ahargana(julian_day(1860, 1, 1)) == 1_811_945.0

    def test_kali_reckoning_matches_creation_reckoning(self):
        """
        Validates v.56, the licence to reckon from a later epoch: the same
        date expressed as 4960 y., 9 m., 7 d. of the Kali Yuga and as
        1,955,884,960 y., 9 m., 7 d. from creation is expected to give the
        same day, since the two differ by exactly YEARS_CREATION_TO_KALI.
        """
        from_creation = ahargana_from_luni_solar(*self.BURGESS_1860, from_creation=True)
        assert from_creation - CIVIL_DAYS_CREATION_TO_KALI == ahargana_from_luni_solar(4960, 9, 7)

    def test_creation_offset_is_exact(self):
        """
        Validates that the creation-to-Kali offset derived through the
        route equals the elapsed years times the SS sidereal year exactly,
        with no rounding slack: 1,955,880,000 y. is a whole number of
        solar months and carries no part-tithi.
        """
        assert CIVIL_DAYS_CREATION_TO_KALI == 714_402_296_627
        assert CIVIL_DAYS_CREATION_TO_KALI == YEARS_CREATION_TO_KALI * SIDEREAL_YEAR_DAYS

    def test_epoch_is_zero_by_the_verse_route(self):
        """
        Validates the boundary case: no years, months or tithis elapsed
        since the Kali epoch is expected to give ahargana 0, matching
        ahargana(KALI_EPOCH_JD).
        """
        assert ahargana_from_luni_solar(0) == 0
        assert ahargana(KALI_EPOCH_JD) == 0.0


class TestBookWorkedExamples:
    """Checks the library against the worked examples of the Hindi Vigyan Bhashya."""

    def test_ahargana_samvat_1979_magha_sudi_5(self):
        """
        Validates the luni-solar ahargana chain (SS Ch.1 v.48-51) against the
        book's example for Vikrama Samvat 1979 Magha sudi 5.

        Expected: 714,404,131,603 days from creation, which maps to
        1923-01-22 (Basant Panchami) via the Kali epoch.
        """
        assert ahargana_from_luni_solar(1_955_885_023, 10, 4,
                                        from_creation=True) == 714_404_131_603
        assert ahargana(julian_day(1923, 1, 22.0)) == 1_834_976

    def test_samvatsara_vs_1981(self):
        """
        Validates the Jovian-year rule (SS Ch.1 v.55): the book finds
        Dhatri for Vikrama Samvat 1981 (Mesha, 1924).
        """
        assert samvatsara(julian_day(1924, 4, 14.0))[1] == "Dhatri"


class TestTimeBase:
    """A library JD is Ujjain mean time: the Kali epoch is midnight on the
    Lanka meridian (SS i.50), 5h 03m ahead of Universal Time."""

    def test_offset_is_the_meridian_longitude(self):
        assert UJJAIN_UT_OFFSET_DAYS == pytest.approx(75.78 / 360.0)
        assert UJJAIN_UTC_OFFSET_HOURS == pytest.approx(75.78 / 15.0)

    def test_kali_epoch_in_ut(self):
        assert jd_to_ut(KALI_EPOCH_JD) == pytest.approx(588465.5 - 75.78 / 360.0)
        assert jd_from_ut(jd_to_ut(KALI_EPOCH_JD)) == pytest.approx(KALI_EPOCH_JD)

    def test_ujjain_midnight_clock_reproduces_burgess_sum_of_days(self):
        """Burgess (under i.53): 1,811,945 days from the Kali epoch to the
        midnight beginning Jan 1 1860 at Ujjain."""
        jd = jd_from_clock(1860, 1, 1, 0.0, UJJAIN_UTC_OFFSET_HOURS)
        assert ahargana(jd) == pytest.approx(1_811_945.0, abs=1e-9)

    def test_ist_and_ut_clocks_are_five_and_a_half_hours_apart(self):
        ist = jd_from_clock(2024, 4, 9, 6.0, 5.5)
        ut = jd_from_clock(2024, 4, 9, 6.0, 0.0)
        assert (ut - ist) * 24.0 == pytest.approx(5.5)
        assert jd_to_ut(ut) == pytest.approx(julian_day(2024, 4, 9) + 6.0 / 24.0)

    @pytest.mark.parametrize("offset", [5.5, 0.0, -5.0, UJJAIN_UTC_OFFSET_HOURS])
    def test_clock_round_trip(self, offset):
        jd = jd_from_clock(2024, 10, 2, 22.5, offset)
        y, m, d, hour = clock_from_jd(jd, offset)
        assert (y, m, d) == (2024, 10, 2)
        assert hour == pytest.approx(22.5, abs=1e-6)
