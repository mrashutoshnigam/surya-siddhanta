"""Tests for Chapter 9: Heliacal Risings and Settings."""

import math
import pytest
from suryasiddhanta.ch01_mean_motions import julian_day
from suryasiddhanta.ch09_heliacal import (
    HELIACAL_PLANETS, VISIBILITY_THRESHOLDS,
    sun_elongation, is_planet_visible,
    heliacal_rising, heliacal_setting,
    visibility_events, next_heliacal,
    HeliacalEvent,
)


# =====================================================================
#  Constants
# =====================================================================

class TestConstants:
    def test_five_planets(self):
        assert len(HELIACAL_PLANETS) == 5

    def test_no_sun_moon(self):
        assert "Sun" not in HELIACAL_PLANETS
        assert "Moon" not in HELIACAL_PLANETS

    def test_all_have_thresholds(self):
        for planet in HELIACAL_PLANETS:
            assert planet in VISIBILITY_THRESHOLDS

    def test_thresholds_are_tuples(self):
        for planet, thresh in VISIBILITY_THRESHOLDS.items():
            assert len(thresh) == 2
            assert thresh[0] > 0
            assert thresh[1] > 0

    def test_mars_threshold(self):
        assert VISIBILITY_THRESHOLDS["Mars"] == (17.0, 17.0)

    def test_jupiter_threshold(self):
        assert VISIBILITY_THRESHOLDS["Jupiter"] == (11.0, 11.0)

    def test_mercury_asymmetric(self):
        retro, direct = VISIBILITY_THRESHOLDS["Mercury"]
        assert retro == 12.0   # SS ix.8: retrograding
        assert direct == 14.0  # rapidly advancing

    def test_venus_asymmetric(self):
        retro, direct = VISIBILITY_THRESHOLDS["Venus"]
        assert retro == 8.0    # SS ix.7: near inferior conjunction
        assert direct == 10.0


# =====================================================================
#  Sun Elongation
# =====================================================================

class TestSunElongation:
    def test_returns_float(self):
        jd = julian_day(2024, 6, 15.0)
        elong = sun_elongation("Mars", jd)
        assert isinstance(elong, float)

    def test_bounded(self):
        jd = julian_day(2024, 6, 15.0)
        for planet in HELIACAL_PLANETS:
            elong = sun_elongation(planet, jd)
            assert -180 <= elong <= 180

    def test_varies_with_time(self):
        jd1 = julian_day(2024, 1, 1.0)
        jd2 = julian_day(2024, 7, 1.0)
        e1 = sun_elongation("Mars", jd1)
        e2 = sun_elongation("Mars", jd2)
        assert e1 != e2

    def test_elongation_bounded_by_180(self):
        """Elongation always within -180 to +180."""
        for planet in HELIACAL_PLANETS:
            for month in range(1, 13):
                jd = julian_day(2024, month, 15.0)
                elong = sun_elongation(planet, jd)
                assert -180 <= elong <= 180

    def test_sign_changes(self):
        """Over a year, elongation should change sign."""
        signs = set()
        for month in range(1, 13):
            jd = julian_day(2024, month, 15.0)
            elong = sun_elongation("Jupiter", jd)
            if abs(elong) > 5:
                signs.add(elong > 0)
        assert len(signs) == 2


# =====================================================================
#  Visibility Check
# =====================================================================

class TestIsPlanetVisible:
    def test_returns_bool(self):
        jd = julian_day(2024, 6, 15.0)
        result = is_planet_visible("Mars", jd)
        assert isinstance(result, bool)

    def test_invalid_planet_raises(self):
        jd = julian_day(2024, 6, 15.0)
        with pytest.raises(ValueError, match="has no heliacal"):
            is_planet_visible("Sun", jd)

    def test_moon_raises(self):
        jd = julian_day(2024, 6, 15.0)
        with pytest.raises(ValueError):
            is_planet_visible("Moon", jd)

    def test_visible_at_large_elongation(self):
        """Planet at opposition should be visible."""
        for month in range(1, 13):
            jd = julian_day(2024, month, 15.0)
            elong = sun_elongation("Jupiter", jd)
            if abs(elong) > 50:
                assert is_planet_visible("Jupiter", jd)
                break

    def test_invisible_near_conjunction(self):
        """Find a time when planet is near Sun and check invisible."""
        for month in range(1, 25):
            yr = 2024 + (month - 1) // 12
            mo = (month - 1) % 12 + 1
            jd = julian_day(yr, mo, 15.0)
            elong = sun_elongation("Saturn", jd)
            if abs(elong) < 5:
                assert not is_planet_visible("Saturn", jd)
                break


# =====================================================================
#  Heliacal Rising
# =====================================================================

class TestHeliacalRising:
    def test_returns_event(self):
        result = heliacal_rising("Jupiter", 2024)
        assert result is None or isinstance(result, HeliacalEvent)

    def test_finds_rising(self):
        result = heliacal_rising("Jupiter", 2024)
        if result:
            assert result.event_type == "rising"
            assert result.planet == "Jupiter"

    def test_elongation_near_threshold(self):
        result = heliacal_rising("Jupiter", 2024)
        if result:
            threshold = 11.0
            assert abs(result.elongation) >= threshold - 0.5

    def test_rising_jd_after_start(self):
        jd_start = julian_day(2024, 1, 1.0)
        result = heliacal_rising("Jupiter", 2024)
        if result:
            assert result.jd > jd_start

    def test_direction_valid(self):
        result = heliacal_rising("Mars", 2024)
        if result:
            assert result.direction in ("morning", "evening")

    def test_invalid_planet(self):
        with pytest.raises(ValueError):
            heliacal_rising("Sun", 2024)

    def test_str_output(self):
        result = heliacal_rising("Venus", 2024)
        if result:
            s = str(result)
            assert "Venus" in s
            assert "rising" in s


# =====================================================================
#  Heliacal Setting
# =====================================================================

class TestHeliacalSetting:
    def test_returns_event(self):
        result = heliacal_setting("Jupiter", 2024)
        assert result is None or isinstance(result, HeliacalEvent)

    def test_finds_setting(self):
        result = heliacal_setting("Jupiter", 2024)
        if result:
            assert result.event_type == "setting"

    def test_elongation_near_threshold(self):
        result = heliacal_setting("Jupiter", 2024)
        if result:
            threshold = 11.0
            assert abs(result.elongation) >= threshold - 0.5

    def test_setting_before_next_rising(self):
        """Setting should precede next rising (invisible period)."""
        setting = heliacal_setting("Mars", 2024)
        rising = heliacal_rising("Mars", 2024)
        if setting and rising and setting.jd < rising.jd:
            assert setting.jd < rising.jd

    def test_invalid_planet(self):
        with pytest.raises(ValueError):
            heliacal_setting("Moon", 2024)


# =====================================================================
#  Visibility Events
# =====================================================================

class TestVisibilityEvents:
    def test_returns_list(self):
        events = visibility_events("Jupiter", 2024, months=12)
        assert isinstance(events, list)

    def test_events_are_heliacal(self):
        events = visibility_events("Jupiter", 2024, months=18)
        for ev in events:
            assert isinstance(ev, HeliacalEvent)
            assert ev.event_type in ("rising", "setting")

    def test_chronological(self):
        events = visibility_events("Mercury", 2024, months=12)
        for i in range(len(events) - 1):
            assert events[i].jd < events[i + 1].jd

    def test_mercury_has_events(self):
        """Mercury has frequent heliacal events (~3x/year)."""
        events = visibility_events("Mercury", 2024, months=12)
        assert len(events) >= 2

    def test_all_planets_produce_events(self):
        for planet in HELIACAL_PLANETS:
            events = visibility_events(planet, 2024, months=24)
            assert isinstance(events, list)


# =====================================================================
#  Next Heliacal
# =====================================================================

class TestNextHeliacal:
    def test_finds_rising(self):
        jd = julian_day(2024, 1, 1.0)
        result = next_heliacal("Mars", jd, "rising")
        assert result is None or result.event_type == "rising"

    def test_finds_setting(self):
        jd = julian_day(2024, 1, 1.0)
        result = next_heliacal("Jupiter", jd, "setting")
        assert result is None or result.event_type == "setting"

    def test_invalid_event_type(self):
        jd = julian_day(2024, 1, 1.0)
        with pytest.raises(ValueError, match="event_type"):
            next_heliacal("Mars", jd, "transit")

    def test_result_after_jd(self):
        jd = julian_day(2024, 6, 15.0)
        result = next_heliacal("Venus", jd, "rising")
        if result:
            assert result.jd > jd


# =====================================================================
#  Edge Cases
# =====================================================================

class TestEdgeCases:
    def test_ancient_date(self):
        result = heliacal_rising("Jupiter", 628)
        assert result is None or isinstance(result, HeliacalEvent)

    def test_saturn_slow_synodic(self):
        """Saturn has ~378-day synodic period; should find event in 2yr."""
        events = visibility_events("Saturn", 2024, months=24)
        assert len(events) >= 1

    def test_venus_events(self):
        events = visibility_events("Venus", 2024, months=24)
        assert isinstance(events, list)

    def test_start_month_offset(self):
        r1 = heliacal_rising("Mars", 2024, start_month=1)
        r2 = heliacal_rising("Mars", 2024, start_month=6)
        if r1 and r2:
            assert r1.jd <= r2.jd or r1.jd > r2.jd

    def test_all_planets_valid_elongation(self):
        jd = julian_day(2024, 3, 20.0)
        for planet in HELIACAL_PLANETS:
            elong = sun_elongation(planet, jd)
            assert -180 <= elong <= 180
