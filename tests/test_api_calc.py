"""Tests for the /calc/* and /corpus/* FastAPI routes."""
import pytest
from fastapi.testclient import TestClient

from suryasiddhanta.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_solar_eclipse_without_a_place_is_geocentric():
    """
    Omitting latitude and longitude must give the geocentric prediction,
    not a topocentric one at 0°N 0°E. Expected: no lambana/nati and no
    daylight fields, matching ch05.compute_solar_eclipse.
    """
    r = client.post("/calc/eclipse/solar", json={"year": 2024, "month": 4, "day": 1})
    assert r.status_code == 200
    body = r.json()
    assert body.get("lambana_arcmin") is None
    assert "locally_visible" not in body


def test_solar_eclipse_at_a_place_reports_daylight():
    """
    With both coordinates the route is topocentric and carries the Sun's
    altitude and local visibility. Expected: both fields present.
    """
    r = client.post("/calc/eclipse/solar",
                    json={"year": 2024, "month": 4, "day": 1, "latitude": 23.18, "longitude": 75.78})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["locally_visible"], bool)
    assert -90.0 <= body["sun_altitude_deg"] <= 90.0


def test_solar_eclipse_with_one_coordinate_is_rejected():
    """Expected: 400 when only one of latitude/longitude is given."""
    r = client.post("/calc/eclipse/solar", json={"year": 2024, "month": 4, "latitude": 23.18})
    assert r.status_code == 400


def test_planet_position(all_planets):
    r = client.post("/calc/planet-position", json={"planet": "Mars", "year": 628, "month": 1, "day": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["planet"] == "Mars"
    assert 0 <= body["true_longitude"] < 360


def test_all_planets(all_planets):
    r = client.post("/calc/all-planets", json={"year": 2024, "month": 1, "day": 1})
    assert r.status_code == 200
    body = r.json()
    assert len(body["planets"]) == len(all_planets)


def test_panchanga():
    r = client.post("/calc/panchanga", json={"year": 2024, "month": 1, "day": 1})
    assert r.status_code == 200
    body = r.json()
    for key in ("tithi", "vara", "nakshatra", "yoga", "karana", "masa", "ritu", "samvatsara"):
        assert key in body


def test_lunar_eclipse():
    r = client.post("/calc/eclipse/lunar", json={"year": 2024, "month": 4})
    assert r.status_code == 200
    assert "is_eclipse" in r.json()


def test_solar_eclipse():
    r = client.post("/calc/eclipse/solar", json={"year": 2024, "month": 4, "day": 8})
    assert r.status_code == 200
    assert "is_eclipse" in r.json()


def test_conjunctions():
    r = client.post("/calc/conjunctions", json={"planet1": "Mars", "planet2": "Jupiter", "year": 2024})
    assert r.status_code == 200
    assert "conjunctions" in r.json()


def test_stars(ujjain_location):
    lat, lon = ujjain_location
    r = client.post("/calc/stars", json={
        "nakshatra": "Rohini", "year": 2024, "month": 1, "day": 1,
        "latitude": lat, "longitude": lon,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["info"]["name"] == "Rohini"
    assert len(body["sky_map"]) == 27


def test_heliacal():
    r = client.post("/calc/heliacal", json={"planet": "Venus", "year": 2024})
    assert r.status_code == 200
    assert "events" in r.json()


def test_moon(ujjain_location):
    lat, lon = ujjain_location
    r = client.post("/calc/moon", json={"year": 2024, "month": 6, "day": 15, "latitude": lat, "longitude": lon})
    assert r.status_code == 200
    body = r.json()
    assert "phase" in body and "horn" in body and "rise_set" in body


def test_cosmography_earth():
    """
    POST /calc/cosmography/earth reports the earth's size and how the sky
    behaves at the place asked for. Expected: the treatise's 1600-yojana
    diameter, a parallel shorter than the equator at Ujjain's latitude,
    and the sphere named oblique there.
    """
    r = client.post("/calc/cosmography/earth", json={"latitude": 23.18, "longitude": 75.78})
    assert r.status_code == 200
    body = r.json()
    assert body["earth_diameter_yojanas"] == 1600.0
    assert body["earth_circumference_yojanas"] == pytest.approx(5059.644, abs=1e-3)
    assert body["corrected_circumference_yojanas"] < body["earth_circumference_yojanas"]
    assert body["sphere_aspect"]["kind"] == "oblique"
    assert body["polar_day_limit"]["latitude"] == pytest.approx(66.0)
    # Ujjain is on the Lanka meridian (SS i.62), so no desantara.
    assert body["desantara"]["yojanas"] == pytest.approx(0.0)
    assert body["desantara"]["ghatis"] == pytest.approx(0.0)
    assert body["desantara"]["corrections_arcmin"]["Moon"] == pytest.approx(0.0)


def test_cosmography_desantara_from_greenwich():
    """
    Greenwich lies 75.78 degrees west of the Lanka meridian. Expected:
    that share of a day in ghatis, and the Moon's correction added (SS i.61).
    """
    r = client.post("/calc/cosmography/earth", json={"latitude": 51.48, "longitude": 0.0})
    assert r.status_code == 200
    desantara = r.json()["desantara"]
    assert desantara["ghatis"] == pytest.approx(75.78 / 6.0, abs=1e-4)
    assert desantara["corrections_arcmin"]["Moon"] > 0.0


def test_cosmography_orbits_whole_table():
    """
    POST /calc/cosmography/orbits with no body returns the whole table.
    Expected: twelve entries innermost first, the Moon's stated 324,000
    yojanas leading, and one shared linear speed for every planet.
    """
    r = client.post("/calc/cosmography/orbits", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["daily_linear_motion_yojanas"] == pytest.approx(11858.717, abs=1e-3)
    assert body["orbits"][0]["body"] == "Moon"
    assert body["orbits"][0]["stated_yojanas"] == 324000
    assert len(body["orbits"]) == 12


def test_cosmography_orbits_one_body():
    """
    POST /calc/cosmography/orbits with a body narrows to it. Expected: a
    single entry whose derived orbit sits within the text's own rounding
    of the figure v.89 states for Saturn.
    """
    r = client.post("/calc/cosmography/orbits", json={"body": "Saturn"})
    assert r.status_code == 200
    orbits = r.json()["orbits"]
    assert len(orbits) == 1
    assert orbits[0]["body"] == "Saturn"
    assert abs(orbits[0]["stated_difference"]) < 2.0


def test_cosmography_orbits_unknown_body_is_a_client_error():
    """
    A body the chapter gives no orbit for must come back as a 400, not a
    crash. Expected: status 400 from _tool's error handling.
    """
    r = client.post("/calc/cosmography/orbits", json={"body": "Pluto"})
    assert r.status_code == 400


def test_cosmography_time():
    """
    POST /calc/cosmography/time reports the days of the orders of beings
    and the regents. Expected: twenty-four hora lords, a day regent drawn
    from the seven planets, and Brahma's day part-elapsed.
    """
    r = client.post("/calc/cosmography/time", json={"year": 2024, "month": 4, "day": 9})
    assert r.status_code == 200
    body = r.json()
    assert body["regents"]["day"] == "Mars"          # 9 April 2024 is a Tuesday
    assert len(body["regents"]["horas"]) == 24
    assert 0.0 < body["brahma_day"]["fraction_elapsed"] < 1.0
    assert body["day_lengths_in_days"]["fathers"] == pytest.approx(29.5305, abs=1e-3)


def test_cosmography_worlds():
    """
    POST /calc/cosmography/worlds returns the descriptive material, and
    must not invent what the text withholds. Expected: nine inquiries,
    seven patalas flagged as unnamed, and no table of upper lokas.
    """
    r = client.post("/calc/cosmography/worlds", json={})
    assert r.status_code == 200
    body = r.json()
    assert len(body["inquiries"]) == 9
    assert body["patalas"]["count"] == 7
    assert body["patalas"]["named_in_text"] is False
    assert "lokas" not in body
    assert body["cities_clock_at_yamakoti_noon"]["Lanka"] == pytest.approx(6.0)


def test_cosmography_worlds_one_section():
    """
    POST /calc/cosmography/worlds with a section narrows the payload.
    Expected: only that section, and a 400 for a section that is not one.
    """
    r = client.post("/calc/cosmography/worlds", json={"section": "reference_places"})
    assert r.status_code == 200
    assert {p["name"] for p in r.json()["reference_places"]} >= {"Meru", "Lanka", "Yamakoti"}
    assert client.post("/calc/cosmography/worlds", json={"section": "lokas"}).status_code == 400


def test_place_time(ujjain_location):
    lat, lon = ujjain_location
    r = client.post("/calc/place-time", json={"year": 2024, "month": 1, "day": 1, "latitude": lat, "longitude": lon})
    assert r.status_code == 200
    body = r.json()
    for key in ("ahargana", "ayanamsha", "day_length", "lagna", "gnomon"):
        assert key in body
    assert body["ahargana"]["kali_era_year"] == 5125


def test_ahargana_verse_route():
    """
    POST /calc/ahargana-verse runs the process of SS i.48-51.
    Expected: Burgess's worked example for Jan 1, 1860 (comm. under i.51),
    1,955,884,960 y. 9 m. 7 d. from creation, reproduced intermediate by
    intermediate, ending in 714,404,108,572 civil days.
    """
    r = client.post(
        "/calc/ahargana-verse",
        json={"years": 1955884960, "months": 9, "tithis": 7, "from_creation": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["solar_months"] == 23470619529
    assert body["adhimasa"] == 721384703
    assert body["lunar_days"] == 725760126967
    assert body["tithikshaya"] == 11356018395
    assert body["civil_days"] == 714404108572


def test_ahargana_verse_route_from_kali_epoch():
    """
    POST /calc/ahargana-verse with the default era takes the same date as
    4960 y. 9 m. 7 d. of the Kali Yuga.
    Expected: 1,811,945 civil days, the same figure /calc/place-time
    reports as the ahargana for 1860-01-01.
    """
    r = client.post("/calc/ahargana-verse", json={"years": 4960, "months": 9, "tithis": 7})
    assert r.status_code == 200
    assert r.json()["civil_days"] == 1811945


def test_daily_panchanga():
    r = client.post("/calc/daily-panchanga", json={"year": 2024, "month": 1, "day": 1})
    assert r.status_code == 200
    assert "tithi" in r.json()


def test_daily_panchanga_range():
    r = client.post("/calc/daily-panchanga/range", json={"year": 2024, "month": 1, "day": 1, "days": 3})
    assert r.status_code == 200
    assert len(r.json()["days"]) == 3


def test_planet_position_invalid_planet_errors():
    r = client.post("/calc/planet-position", json={"planet": "Pluto", "year": 2024})
    assert r.status_code == 400


def test_corpus_chapters():
    r = client.get("/corpus/chapters")
    assert r.status_code == 200
    assert len(r.json()["chapters"]) > 0


def test_corpus_verse():
    r = client.get("/corpus/verse/2/39")
    assert r.status_code == 200
    assert r.json()["id"] == "SS.2.39"


def test_corpus_verse_not_found():
    r = client.get("/corpus/verse/99/99")
    assert r.status_code == 404


def test_corpus_search():
    r = client.get("/corpus/search", params={"q": "apsis"})
    assert r.status_code == 200
    assert len(r.json()["results"]) > 0


def test_patas():
    """
    POST /calc/patas returns the patas found in the range, one entry per
    event. Expected: a non-empty list over 60 days with count matching.
    """
    r = client.post("/calc/patas", json={"year": 2024, "month": 1, "day": 1, "days": 60})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == len(body["events"])
    assert body["events"], "60 days must contain at least one pata"
    assert body["events"][0]["kind"] in ("Vyatipata", "Vaidhrita")


def test_pata_active():
    """
    POST /calc/pata/active always names the next pata, whether or not one
    is running. Expected: an 'active' key and a 'next' of a known kind.
    """
    r = client.post("/calc/pata/active", json={"year": 2024, "month": 1, "day": 1, "hour": 12})
    assert r.status_code == 200
    body = r.json()
    assert "active" in body
    assert body["next"]["kind"] in ("Vyatipata", "Vaidhrita")


def test_instruments_sphere_with_and_without_stars():
    """
    POST /calc/instruments/sphere returns the drawable armillary sphere of
    Ch.13. Expected: 46 hoops with the stars (4 great, horizon, 6 solar,
    35 stellar) each carrying a unit normal for the 3D page, 11 without
    the stars, and the three lagnas plus the Sun among the points.
    """
    payload = {"year": 2024, "month": 4, "day": 9, "hour": 7.0,
               "latitude": 23.18, "longitude": 75.78}
    r = client.post("/calc/instruments/sphere", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert len(body["hoops"]) == 46
    assert all(len(h["normal"]) == 3 for h in body["hoops"])
    assert {p["key"] for p in body["points"]} == {"lagna", "asta_lagna", "madhya_lagna", "sun"}
    assert len(body["zenith"]) == 3

    r = client.post("/calc/instruments/sphere", json={**payload, "include_stars": False})
    assert r.status_code == 200
    assert len(r.json()["hoops"]) == 11


def test_instruments_sphere_rejects_a_polar_latitude():
    """
    The sphere's sines are undefined at the poles, so the schema caps the
    latitude. Expected: 422 for latitude 95.
    """
    r = client.post("/calc/instruments/sphere", json={"year": 2024, "latitude": 95})
    assert r.status_code == 422


def test_instruments_clepsydra():
    """
    POST /calc/instruments/clepsydra does the water-clock arithmetic of
    xiii.23. Expected: ten sinkings are 240 minutes, and the day and night
    at Ujjain on 9 April 2024 add to sixty sinkings.
    """
    r = client.post("/calc/instruments/clepsydra",
                    json={"sinkings": 10, "year": 2024, "month": 4, "day": 9})
    assert r.status_code == 200
    body = r.json()
    assert body["elapsed"]["total_minutes"] == pytest.approx(240.0)
    day = body["day_and_night"]
    assert day["day_ghatis"] + day["night_ghatis"] == pytest.approx(60.0, abs=1e-3)


def test_instruments_clepsydra_needs_some_input():
    """With nothing to convert the tool reports an error. Expected: 400."""
    r = client.post("/calc/instruments/clepsydra", json={})
    assert r.status_code == 400


def test_instruments_time_from_the_gnomon():
    """
    POST /calc/instruments/time with the man-instrument: a shadow equal to
    the gnomon means an altitude of 45 deg. Expected: a time within the
    half-day, labelled as the text's own method.
    """
    r = client.post("/calc/instruments/time",
                    json={"instrument": "nara", "value": 12, "year": 2024,
                          "month": 4, "day": 9, "latitude": 23.18})
    assert r.status_code == 200
    body = r.json()
    assert body["sun_altitude_deg"] == pytest.approx(45.0)
    assert 0.0 < body["ghatis_since_sunrise"] < body["half_day_ghatis"]
    assert body["source"] == "verse"


def test_instruments_time_rejects_an_impossible_chord():
    """
    A staff chord longer than the diurnal circle's diameter is a domain
    error from the library, not a crash. Expected: 400.
    """
    r = client.post("/calc/instruments/time",
                    json={"instrument": "yashti", "value": 99999, "year": 2024,
                          "month": 4, "day": 9})
    assert r.status_code == 400


def test_instruments_time_rejects_an_unknown_instrument():
    """The instrument is a closed set in the schema. Expected: 422 for 'sundial'."""
    r = client.post("/calc/instruments/time",
                    json={"instrument": "sundial", "value": 1, "year": 2024})
    assert r.status_code == 422


def test_instruments_catalog():
    """
    POST /calc/instruments/catalog returns the descriptive half of Ch.13.
    Expected: eleven instruments, and the seven fixed stars verified
    against corpus record SS.8.24.
    """
    r = client.post("/calc/instruments/catalog", json={})
    assert r.status_code == 200
    body = r.json()
    assert len(body["instruments"]) == 11
    assert len(body["fixed_stars"]) == 7
    assert all(s["corpus_record"] == "SS.8.24" for s in body["fixed_stars"])


def test_utc_offset_moves_the_instant():
    """A clock time is read in `utc_offset`: the same 06:00 in UT is
    5.5 hours later than in IST, so the Moon has moved on."""
    ist = client.post("/calc/all-planets", json={"year": 2024, "month": 4, "day": 9.25}).json()
    ut = client.post("/calc/all-planets",
                     json={"year": 2024, "month": 4, "day": 9.25, "utc_offset": 0.0}).json()
    assert (ut["jd"] - ist["jd"]) * 24.0 == pytest.approx(5.5)
    moon = lambda b: next(p for p in b["planets"] if p["planet"] == "Moon")["true_longitude"]
    assert (moon(ut) - moon(ist)) % 360.0 == pytest.approx(13.2 * 5.5 / 24.0, abs=0.6)


def test_weekday_follows_the_civil_date():
    """Midnight IST is 23:33 the evening before in Ujjain mean time, but
    the weekday turns at local midnight (SS i.66): 9 April 2024 is a Tuesday."""
    body = client.post("/calc/panchanga", json={"year": 2024, "month": 4, "day": 9}).json()
    assert body["vara"]["name"] == "Mangalavara"
