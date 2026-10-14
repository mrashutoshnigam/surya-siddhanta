"""
Tests for Chapter 11 — the patas (Vyatipata and Vaidhrita).

Validates the ayana-valana declination correction of SS xi.4-11, the
two-stage event search (longitude-sum crossing refined to declination
equality), and the event intervals of SS xi.12-23.
"""

import pytest

from suryasiddhanta.ch02_true_places import OBLIQUITY_DEGREES
from suryasiddhanta.ch11_pata import (
    PATA_KINDS, VAIDHRITA_SUM, VYATIPATA_SUM, active_pata, ayana_valana,
    find_next_pata, find_patas, longitude_sum, moon_declination,
    moon_declination_exact, moon_latitude_deg, sun_declination,
)

# The SS valana rule deviates from the rigorous spherical declination by
# at most 0.023 deg over all longitudes and |latitude| <= 4.5 deg; 0.05
# leaves headroom without letting a real regression through.
VALANA_TOLERANCE_DEG = 0.05


def test_ayana_valana_extremes():
    """
    Ayana valana equals the obliquity at the equinoxes, where the ecliptic
    is most inclined to the equator, and vanishes at the solstices, where
    the two are parallel. Expected: +/-24 deg and 0 deg respectively.
    """
    assert ayana_valana(0.0) == pytest.approx(OBLIQUITY_DEGREES, abs=1e-9)
    assert ayana_valana(180.0) == pytest.approx(-OBLIQUITY_DEGREES, abs=1e-9)
    assert ayana_valana(90.0) == pytest.approx(0.0, abs=1e-9)
    assert ayana_valana(270.0) == pytest.approx(0.0, abs=1e-9)


def test_moon_declination_matches_rigorous(jd_2024):
    """
    The chapter's first-order latitude correction should track the rigorous
    spherical declination across a full lunation. Expected: agreement to
    better than 0.05 deg at every step.
    """
    for step in range(30):
        jd = jd_2024 + step
        assert abs(moon_declination(jd) - moon_declination_exact(jd)) < VALANA_TOLERANCE_DEG


def test_moon_declination_differs_from_zero_latitude_value(jd_2024):
    """
    The latitude correction must actually do something: over a lunation the
    Moon's declination has to depart from the bare declination of its
    longitude. Expected: at least one step differing by over 0.5 deg.
    """
    from suryasiddhanta.ch03_direction_place_time import declination
    from suryasiddhanta.ch11_pata import _tropical_longitude

    diffs = [
        abs(moon_declination(jd_2024 + s)
            - declination(_tropical_longitude("Moon", jd_2024 + s)))
        for s in range(30)
    ]
    assert max(diffs) > 0.5


def test_sun_declination_bounded(jd_2024):
    """
    Solar declination is bounded by the obliquity the SS uses. Expected:
    |declination| never exceeds 24 deg across a year of weekly samples.
    """
    for step in range(0, 365, 7):
        assert abs(sun_declination(jd_2024 + step)) <= OBLIQUITY_DEGREES + 1e-9


def test_moon_latitude_within_ss_maximum(jd_2024):
    """
    The SS caps the Moon's latitude at 270 arcmin. Expected: every sample
    over a lunation stays within 4.5 deg.
    """
    for step in range(30):
        assert abs(moon_latitude_deg(jd_2024 + step)) <= 4.5 + 1e-9


def test_find_next_pata_returns_event(jd_2024):
    """
    Patas fall roughly every 12.7 days, so one must lie within the default
    60-day window. Expected: a well-ordered event of a known kind, marked
    as still to come.
    """
    ev = find_next_pata(jd_2024)
    assert ev is not None
    assert ev.kind in PATA_KINDS
    assert ev.jd_begin < ev.jd_middle < ev.jd_end
    assert ev.is_past is False


def test_pata_declination_condition_holds(jd_2024):
    """
    At the refined middle of a pata the declinations are equal in amount:
    same sign for Vyatipata, opposite sign for Vaidhrita. Expected: the
    relevant combination is within 0.05 deg of zero for every refined event
    in half a year.
    """
    events = find_patas(jd_2024, jd_2024 + 180)
    assert events
    assert all(ev.refined for ev in events), (
        "every pata in an ordinary half-year should meet the declination "
        "condition somewhere in the refinement window")
    for ev in events:
        ds = sun_declination(ev.jd_middle)
        dm = moon_declination(ev.jd_middle)
        if ev.kind == "Vyatipata":
            assert abs(dm - ds) < 0.05
        else:
            assert abs(dm + ds) < 0.05


def test_longitude_sum_near_target_at_crossing(jd_2024):
    """
    The nominal instant is defined by the longitude rule alone. Expected:
    at jd_sum_crossing the tropical longitude sum sits on 180 deg for a
    Vyatipata and 360/0 deg for a Vaidhrita, within 0.1 deg.
    """
    events = find_patas(jd_2024, jd_2024 + 90)
    assert events
    for ev in events:
        target = VYATIPATA_SUM if ev.kind == "Vyatipata" else VAIDHRITA_SUM
        s = longitude_sum(ev.jd_sum_crossing)
        diff = min(abs(s - target), abs(s - (target - 360.0)),
                   abs(s + 360.0 - target))
        assert diff < 0.1


def test_declination_refinement_shifts_the_instant(jd_2024):
    """
    The chapter's whole point is that the true pata is not the longitude-sum
    crossing, because the Moon's latitude moves its declination. Expected:
    over a year at least one refined event shifts by more than a minute.
    """
    events = find_patas(jd_2024, jd_2024 + 365)
    shifts = [abs(ev.jd_middle - ev.jd_sum_crossing) for ev in events if ev.refined]
    assert shifts
    assert max(shifts) > 1.0 / 1440.0


def test_refinement_shift_stays_bounded(jd_2024):
    """
    The declination refinement corrects the nominal instant by hours, and
    near a solstice — where both declinations crawl — by as much as a
    couple of days. Expected: no event drifts more than 3 days from its
    longitude-sum crossing, which would mean it had latched onto a
    neighbouring pata's root.
    """
    for ev in find_patas(jd_2024, jd_2024 + 365):
        assert abs(ev.jd_middle - ev.jd_sum_crossing) < 3.0


def test_durations_never_hit_the_clamp(jd_2024):
    """
    The half-duration clamp is a guard against a vanishing declination
    rate, not a normal outcome. Expected: every pata in a year comes in
    well under the 24-hour clamped maximum.
    """
    for ev in find_patas(jd_2024, jd_2024 + 365):
        assert ev.duration_hours < 12.0


def test_find_patas_over_a_year(jd_2024):
    """
    The longitude sum gains about 14.2 deg/day, hitting 180 or 360 every
    ~12.7 days. Expected: roughly 29 patas in a year, both kinds present,
    ordered by their true instant.
    """
    events = find_patas(jd_2024, jd_2024 + 365)
    assert 25 <= len(events) <= 33
    assert {ev.kind for ev in events} == set(PATA_KINDS)
    for a, b in zip(events, events[1:]):
        assert a.jd_middle < b.jd_middle


def test_durations_are_plausible(jd_2024):
    """
    Half-duration is the combined semi-diameters (~32.2 arcmin) over the
    difference of the daily motions (~660-900 arcmin/day). Expected: a
    whole duration of about 1.7 to 2.4 hours (4.3 to 5.9 ghatis), and
    duration_ghatis consistent with the interval at 60 ghatis to the day.
    """
    for ev in find_patas(jd_2024, jd_2024 + 180):
        assert 1.6 < ev.duration_hours < 2.5
        assert ev.duration_ghatis == pytest.approx(
            (ev.jd_end - ev.jd_begin) * 60.0, rel=1e-4)


def test_half_duration_follows_the_verse(jd_2024):
    """
    SS xi.14: half-sum of the discs x 60 / difference of the daily motions
    gives the half-duration in nadis. Expected: each event's duration equals
    twice that figure computed independently from the true longitudes.
    """
    from suryasiddhanta.ch04_lunar_eclipses import APPARENT_DIAMETER_ARCMIN
    from suryasiddhanta.ch01_mean_motions import from_julian_day
    from suryasiddhanta.ch02_true_places import compute

    def lon(body, jd):
        y, m, d, f = from_julian_day(jd)
        return compute(body, y, m, d + f).true_longitude

    half_sum = (APPARENT_DIAMETER_ARCMIN["Sun"] + APPARENT_DIAMETER_ARCMIN["Moon"]) / 2
    for ev in find_patas(jd_2024, jd_2024 + 60):
        t = ev.jd_middle
        moon = (lon("Moon", t + 0.5) - lon("Moon", t - 0.5)) % 360 * 60
        sun = (lon("Sun", t + 0.5) - lon("Sun", t - 0.5)) % 360 * 60
        half_nadis = half_sum * 60 / (moon - sun)
        assert ev.duration_ghatis == pytest.approx(2 * half_nadis, rel=2e-3)


def test_active_pata_agrees_with_event_interval(jd_2024):
    """
    active_pata reports an event exactly when the instant lies inside one.
    Expected: the event's own middle is active, and a moment two days past
    its end is not.
    """
    ev = find_next_pata(jd_2024)
    assert ev is not None
    inside = active_pata(ev.jd_middle)
    assert inside is not None
    assert inside.kind == ev.kind
    assert inside.is_past is False
    assert active_pata(ev.jd_end + 2.0) is None


def test_kind_filter(jd_2024):
    """
    A caller may ask for one kind of pata. Expected: each kind is found
    within the default window and the returned event matches the request.
    """
    for kind in PATA_KINDS:
        ev = find_next_pata(jd_2024, kind=kind)
        assert ev is not None and ev.kind == kind


def test_unknown_kind_rejected(jd_2024):
    """
    Lata is a pata of later siddhantas, not of the SS. Expected: an
    unrecognised name raises ValueError rather than scanning silently.
    """
    with pytest.raises(ValueError):
        find_next_pata(jd_2024, kind="Lata")


def test_reversed_range_rejected(jd_2024):
    """
    A backwards search window is a caller error. Expected: ValueError, not
    an empty list that hides the mistake.
    """
    with pytest.raises(ValueError):
        find_patas(jd_2024, jd_2024 - 10)


def test_works_at_the_ayanamsha_zero_year(jd_499):
    """
    The search must hold up far from the modern epoch, where the SS
    ayanamsha is zero and sidereal and tropical longitudes coincide.
    Expected: events found in 499 CE with the same ordering invariants.
    """
    events = find_patas(jd_499, jd_499 + 90)
    assert events
    for ev in events:
        assert ev.jd_begin < ev.jd_middle < ev.jd_end
        assert ev.kind in PATA_KINDS


def test_tool_find_patas_returns_events():
    """
    The chatbot find_patas tool wraps the chapter function as JSON.
    Expected: a populated event list whose entries carry formatted times,
    duration and both declinations.
    """
    import json
    from suryasiddhanta.chatbot.tools import TOOL_FUNCTIONS

    body = json.loads(TOOL_FUNCTIONS["find_patas"](year=2024, month=1, day=1, days=60))
    assert body["count"] == len(body["events"])
    assert body["events"], "60 days must contain at least one pata"
    first = body["events"][0]
    for key in ("kind", "begin", "middle", "end", "duration_ghatis",
                "sun_declination", "moon_declination"):
        assert key in first
    assert first["kind"] in ("Vyatipata", "Vaidhrita")


def test_tool_find_patas_warns_about_the_yoga():
    """
    The pata shares its name with a nitya-yoga, so the tool output must
    say so or the model will conflate them. Expected: the summary mentions
    the yoga.
    """
    import json
    from suryasiddhanta.chatbot.tools import TOOL_FUNCTIONS

    body = json.loads(TOOL_FUNCTIONS["find_patas"](year=2024, month=1, day=1, days=30))
    assert "yoga" in body["summary"].lower()


def test_tool_pata_details_reports_active_state():
    """
    compute_pata_details says whether a pata is running at a given moment
    and always names the next one. Expected: an 'active' key (possibly
    null) and a 'next' entry of a known kind.
    """
    import json
    from suryasiddhanta.chatbot.tools import TOOL_FUNCTIONS

    body = json.loads(TOOL_FUNCTIONS["compute_pata_details"](
        year=2024, month=1, day=1, hour=12))
    assert "active" in body
    assert body["next"]["kind"] in ("Vyatipata", "Vaidhrita")
    assert "summary" in body


def test_tool_schemas_registered():
    """
    Both tools must appear in the schema list the agent is given, not just
    in the dispatcher. Expected: both names present in TOOL_DEFINITIONS.
    """
    from suryasiddhanta.chatbot.tools import TOOL_DEFINITIONS

    names = {t["name"] for t in TOOL_DEFINITIONS}
    assert {"find_patas", "compute_pata_details"} <= names


def test_window_edges_do_not_drop_patas():
    """
    Validates that a narrow search window finds every pata whose true
    instant lies inside it, even if the nominal longitude-sum crossing
    falls outside.

    Expected: for each pata found in a wide window, a window tightly
    bracketing its true middle returns that same pata.
    """
    from suryasiddhanta.ch01_mean_motions import julian_day
    from suryasiddhanta.ch11_pata import find_patas
    start = julian_day(2024, 1, 1.0)
    wide = find_patas(start, start + 120)
    assert wide
    for ev in wide:
        narrow = find_patas(ev.jd_middle - 0.01, ev.jd_middle + 0.01)
        assert any(abs(n.jd_middle - ev.jd_middle) < 1e-3 and n.kind == ev.kind
                   for n in narrow)
