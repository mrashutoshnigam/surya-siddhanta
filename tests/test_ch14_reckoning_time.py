"""Tests for Chapter 14: the modes of reckoning time (ch14_reckoning_time).

Pinned to the chapter's own structure: the nine manas, the shadasitimukhas,
the sankranti punyakala, the Fathers' clock, the months-and-asterisms table
and Jupiter's twelve-year cycle. Everything runs offline.
"""
from __future__ import annotations

import itertools
import math

import pytest

from suryasiddhanta import ch01_mean_motions as ch01
from suryasiddhanta import ch12_cosmography as ch12
from suryasiddhanta import ch14_reckoning_time as ch14

KEYS = ["brahma", "daiva", "pitrya", "prajapatya", "barhaspatya",
        "saura", "savana", "candra", "naksatra"]


# ── the nine manas ──────────────────────────────────────────────

def test_nine_manas_in_the_order_of_verse_one():
    """xiv.1: nine modes, in the verse's order. Expected: the nine keys."""
    assert [m.key for m in ch14.manas()] == KEYS


def test_practical_manas_are_the_four_of_verse_two():
    """xiv.2: four modes are used in practice. Expected: solar, civil, lunar, sidereal."""
    assert {m.key for m in ch14.manas() if m.practical} == {"saura", "savana", "candra", "naksatra"}


def test_unit_lengths():
    """The unit lengths in civil days follow from the Ch.1 constants.

    Expected: a civil day is 1; a tithi is a thirtieth of a lunar month; the
    gods' day is the sidereal year; Brahma's day is a kalpa of civil days.
    """
    assert ch14.mana("savana").unit_days == 1.0
    assert ch14.mana("candra").unit_days == pytest.approx(ch12.SYNODIC_MONTH_DAYS / 30)
    assert ch14.mana("pitrya").unit_days == pytest.approx(ch12.SYNODIC_MONTH_DAYS)
    assert ch14.mana("daiva").unit_days == pytest.approx(ch01.SIDEREAL_YEAR_DAYS)
    assert ch14.mana("brahma").unit_days == pytest.approx(ch01.CIVIL_DAYS_PER_KALPA)
    assert ch14.mana("saura").unit_days == pytest.approx(ch01.SIDEREAL_YEAR_DAYS / 360)
    assert ch14.mana("naksatra").unit_days < 1.0


def test_jovian_year_is_about_361_days():
    """xiv.17: a twelfth of Jupiter's revolution. Expected: about 361.03 days."""
    assert ch14.mana("barhaspatya").unit_days == pytest.approx(361.03, abs=0.01)


def test_manvantara_structure_sums_to_a_kalpa():
    """xiv.21 with i.15-18: fourteen manvantaras of 71 mahayugas plus fifteen krita sandhis.

    Expected: exactly one kalpa of years, and the manvantara mana is 71
    mahayugas of civil days.
    """
    years = 14 * 71 * ch01.MAHAYUGA + 15 * ch01.KRITA_YUGA
    assert years == ch01.KALPA
    assert ch14.mana("prajapatya").unit_days == pytest.approx(71 * ch01.CIVIL_DAYS_PER_MAHAYUGA)


def test_convert_round_trips_across_all_81_pairs():
    """convert is a pure ratio. Expected: a round trip returns the value for every pair."""
    pairs = list(itertools.product(KEYS, KEYS))
    assert len(pairs) == 81
    for a, b in pairs:
        assert ch14.convert(ch14.convert(7.5, a, b), b, a) == pytest.approx(7.5)


def test_civil_day_is_sixty_nadis_and_a_month_thirty_tithis():
    """By construction. Expected: a lunar month is 30 tithis; a year is 360 solar days."""
    assert ch14.convert(1, "pitrya", "candra") == pytest.approx(30.0)
    assert ch14.convert(1, "daiva", "saura") == pytest.approx(360.0)


def test_unknown_mana_names_the_valid_ones():
    """Expected: ValueError listing the keys."""
    with pytest.raises(ValueError, match="brahma"):
        ch14.mana("nope")
    with pytest.raises(ValueError):
        ch14.convert(1, "savana", "nope")


def test_reckon_at_the_kali_epoch(jd_kali_epoch):
    """The epoch is ahargana 0 and Kali year 0.

    Expected: the civil reading is 0 days and the solar year reading is 0.
    """
    pano = ch14.reckon(jd_kali_epoch)
    by = {r.key: r for r in pano.readings}
    assert [r.key for r in pano.readings] == KEYS
    assert by["savana"].count == pytest.approx(0.0)
    assert by["saura"].count == pytest.approx(0.0)


def test_reckon_places_today_in_the_seventh_manvantara(jd_2024):
    """The present era is the seventh manvantara (Vaivasvata).

    Expected: manvantara 7, not in a sandhi, with a plausible year within it.
    """
    d = ch14.reckon(jd_2024).details["manvantara"]
    assert d["number"] == 7 and d["in_sandhi"] is False
    assert 0 < d["year_within"] < 71 * ch01.MAHAYUGA


# ── the solar year ──────────────────────────────────────────────

def test_shadasitimukha_longitudes_and_spacing():
    """xiv.4-6: 266, 352, 78 and 164 degrees, 86 apart from Libra, 16 left in Virgo.

    Expected: exact longitudes and arcs; they sum to 360.
    """
    marks = ch14.shadasitimukhas(2024)
    assert [m["longitude"] for m in marks[:4]] == [266, 352, 78, 164]
    assert [m["arc_degrees"] for m in marks[:4]] == [86, 86, 86, 86]
    assert marks[4]["arc_degrees"] == 16
    assert sum(m["arc_degrees"] for m in marks) == 360


def test_shadasitimukha_days_are_not_equal():
    """The arcs are uniform but the Sun's motion is not.

    Expected: each 86-degree interval lasts between 84 and 90 days (the Sun is
    slowest near his apogee, in Gemini and Virgo), and they are not all the same.
    """
    days = [m["measured_days"] for m in ch14.shadasitimukhas(2024)[:4]]
    assert all(84.0 < d < 90.5 for d in days)
    assert max(days) - min(days) > 0.1


def test_sankrantis_tagged_by_kind():
    """xiv.7: Aries and Libra are visuvat, Cancer and Capricorn ayana.

    Expected: twelve events in order with the right kinds, and increasing JDs.
    """
    ev = ch14.sankrantis(2024)
    assert len(ev) == 12
    assert [e.longitude for e in ev] == [30.0 * i for i in range(12)]
    assert {e.sign: e.kind for e in ev if e.kind != "plain"} == {
        "Mesha": "visuvat", "Tula": "visuvat", "Karka": "ayana", "Makara": "ayana"}
    assert all(a.jd < b.jd for a, b in zip(ev, ev[1:]))


def test_sankranti_falls_in_mid_april_now():
    """The sidereal Mesha entry is in mid-April today. Expected: 13-15 April 2024."""
    jd = ch14.sankrantis(2024)[0].jd
    y, m, d, _ = ch01.from_julian_day(jd)
    assert (y, m) == (2024, 4) and 12 <= d <= 15


def test_punyakala_total_and_symmetry():
    """xiv.11: the disk's crossing time. Expected: about 33 nadis, half each side."""
    e = ch14.sankrantis(2024)[0]
    assert e.punyakala_total_nadis == pytest.approx(33.0, abs=1.5)
    assert e.punyakala_each_side_nadis == pytest.approx(e.punyakala_total_nadis / 2)
    assert ch14.punyakala_nadis(e.jd) == pytest.approx(e.punyakala_total_nadis)


def test_ayanas_and_visuvats():
    """xiv.9: dakshinayana begins at Cancer, uttarayana at Capricorn.

    Expected: the events sit at the right signs, and the gap to the tropical
    solstice is the ayanamsha.
    """
    a = ch14.ayanas(2024)
    assert a["dakshinayana"]["sign"] == "Karka" and a["uttarayana"]["sign"] == "Makara"
    assert a["dakshinayana"]["jd"] < a["uttarayana"]["jd"]
    assert a["dakshinayana"]["tropical_longitude"] - 90.0 == pytest.approx(
        a["dakshinayana"]["ayanamsha"], abs=1e-3)
    v = ch14.visuvats(2024)
    assert v["vernal"]["sign"] == "Mesha" and v["autumnal"]["sign"] == "Tula"


def test_six_ritus_of_two_signs():
    """xiv.10: six seasons of two signs each, counted from Capricorn.

    Expected: six, each about two months, tiling a year without gaps.
    """
    rs = ch14.solar_year(2024).ritus
    assert len(rs) == 6
    assert all(55.0 < r["days"] < 66.0 for r in rs)
    assert all(a["end_jd"] == b["start_jd"] for a, b in zip(rs, rs[1:]))
    assert [(r["start_sign"], r["name"]) for r in rs] == [
        ("Vrishabha", "Grishma"), ("Karka", "Varsha"),
        ("Kanya", "Sharad"), ("Vrishchika", "Hemanta"),
        ("Makara", "Shishira"), ("Meena", "Vasanta"),
    ]


def test_year_out_of_range_is_rejected():
    """Expected: a year far outside the solver's range raises ValueError."""
    with pytest.raises(ValueError):
        ch14.solar_year(900000)


# ── the Fathers' clock ──────────────────────────────────────────

def _jd_at_elongation(target: float) -> float:
    """A JD near the first moment after 2024-01-01 when the Moon is `target` ahead."""
    return ch14._next_elongation_jd(ch01.julian_day(2024, 1, 1.0), target)


def test_new_moon_is_the_fathers_midday():
    """xiv.14: the end of the month is their midday. Expected: hour 12 at new moon."""
    c = ch14.pitrya_clock(_jd_at_elongation(0.0))
    assert c.hour == pytest.approx(12.0, abs=0.01)
    assert c.phase == "midday"


def test_full_moon_is_the_fathers_midnight():
    """xiv.14: the end of the half-month is their midnight. Expected: hour 0 at full moon."""
    c = ch14.pitrya_clock(_jd_at_elongation(180.0))
    assert min(c.hour, 24.0 - c.hour) == pytest.approx(0.0, abs=0.01)
    assert c.phase == "midnight"


def test_pitrya_next_events_lie_ahead():
    """Expected: the next noon and midnight are after the moment, within a month."""
    jd = ch01.julian_day(2024, 1, 10.0)
    c = ch14.pitrya_clock(jd)
    assert jd < c.next_noon_jd < jd + 31 and jd < c.next_midnight_jd < jd + 31
    assert 0.0 <= c.hour < 24.0 and 1 <= c.tithi <= 30


# ── months and asterisms ────────────────────────────────────────

def test_month_table_holds_all_27_once():
    """xiv.15-16: twelve months, 27 asterisms without repeats, three months with three."""
    table = ch14.month_asterisms()
    names = [a for row in table for a in row["asterisms"]]
    assert len(table) == 12 and len(names) == 27 and len(set(names)) == 27
    assert sum(1 for row in table if len(row["asterisms"]) == 3) == 3
    assert {i + 1 for i, row in enumerate(table) if len(row["asterisms"]) == 3} == {5, 11, 12}


def test_every_month_contains_its_namesake_asterism():
    """The table checks itself: each month holds its own asterism, and all are real."""
    known = set(ch01._NAKSHATRA_NAMES)
    for row in ch14.month_asterisms():
        assert row["namesake"] in row["asterisms"]
        assert set(row["asterisms"]) <= known


def test_asterism_month_lookup():
    """Expected: Krittika belongs to Kartika, Bharani to Ashvina; unknown names raise."""
    assert ch14.asterism_month("Krittika") == "Kartika"
    assert ch14.asterism_month("Bharani") == "Ashvina"
    with pytest.raises(ValueError):
        ch14.asterism_month("Nowhere")


# ── Jupiter's years ─────────────────────────────────────────────

def test_jovian_cycle_returns_after_twelve_years():
    """xiv.17: twelve Jovian years are one revolution.

    Expected: the name after twelve steps is the starting name, every step
    advances 0, 1 or 2 names (spans of two or three asterisms against a 30
    degree step), and the twelve steps advance exactly 12 names in all.
    """
    cycle = ch14.barhaspatya_cycle(2024, 12)
    assert len(cycle) == 12
    jd0 = cycle[0].jd
    step = ch14.mana("barhaspatya").unit_days
    again = ch14.barhaspatya_year(jd0 + 12 * step)
    assert again.name == cycle[0].name
    idx = [y.name_index for y in cycle] + [again.name_index]
    advances = [(b - a) % 12 for a, b in zip(idx, idx[1:])]
    assert all(a in (0, 1, 2) for a in advances) and sum(advances) == 12


def test_mean_method_is_a_commentary_source(jd_2024):
    """
    xiv.17 names the year from Jupiter's heliacal setting and rising; the
    mean-longitude reckoning is Burgess's reading, not the verse's rule.
    Expected: the default mean method reports source commentary.
    """
    y = ch14.barhaspatya_year(jd_2024)
    assert y.method == "mean" and y.source == "commentary"
    assert y.name in {r["month"] for r in ch14.month_asterisms()}
    assert y.sixty_year_name == ch01.samvatsara(jd_2024)[1]


def test_unknown_method_is_rejected(jd_2024):
    """Expected: ValueError naming the valid methods."""
    with pytest.raises(ValueError, match="mean"):
        ch14.barhaspatya_year(jd_2024, method="guess")


def test_heliacal_method_runs_and_is_commentary(jd_2024):
    """Expected: the heliacal method returns a commentary-sourced year with a name."""
    y = ch14.barhaspatya_year(jd_2024, method="heliacal")
    assert y.source == "commentary" and y.name


# ── the one edit to ch12 ────────────────────────────────────────

def test_sun_crossing_jd_is_public_and_aliased(jd_2024):
    """Expected: ch12.sun_crossing_jd is the old private solver, still reachable as _last_crossing."""
    assert ch12._last_crossing is ch12.sun_crossing_jd
    jd = ch12.sun_crossing_jd(jd_2024, 0.0)
    assert jd <= jd_2024 and jd_2024 - jd < 370
