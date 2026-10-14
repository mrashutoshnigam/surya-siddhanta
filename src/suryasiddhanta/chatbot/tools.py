"""
chatbot/tools.py
================
Tool definitions for the Surya Siddhanta AI assistant.

Covers all 13 implemented chapters (ch01–ch13):
  Ch.1  Mean motions, ahargana, time units
  Ch.2  True places, sine table, ayanamsha
  Ch.3  Direction/place/time, gnomon, lagna
  Ch.4  Lunar eclipses
  Ch.5  Solar eclipses
  Ch.6  Eclipse projection & diagrams
  Ch.7  Planetary & star conjunctions
  Ch.8  Nakshatras, star catalog, rise/set
  Ch.9  Heliacal risings & settings
  Ch.10 Lunar horns, phase, illumination
  Ch.11 Patas — Vyatipata and Vaidhrita
  Ch.12 Cosmography — earth, orbits, cosmic time, creation
  Ch.13 Instruments — armillary sphere, clepsydra, time from instruments
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from suryasiddhanta.ch01_mean_motions import UJJAIN_UTC_OFFSET_HOURS, clock_from_jd

#: Clock-time inputs and outputs are civil time in this zone unless a tool
#: is given ``utc_offset``: IST, UTC+5:30. The library itself reckons in
#: Ujjain mean time (UTC+5:03, ch01); these helpers convert at the edge.
DEFAULT_UTC_OFFSET = 5.5


def _lib_day(day: float, utc_offset: float) -> float:
    """
    The ``day`` argument a library call needs for a clock time in
    ``utc_offset``. Library dates are read in Ujjain mean time and
    ``julian_day`` is linear in the day, so shifting the day by the
    difference of the two zones lands on the same instant.
    """
    return float(day) + (UJJAIN_UTC_OFFSET_HOURS - float(utc_offset)) / 24.0


def _zone(utc_offset: float) -> str:
    """Label a UTC offset in hours as 'UTC+05:30'."""
    minutes = round(float(utc_offset) * 60)
    sign = "+" if minutes >= 0 else "-"
    return f"UTC{sign}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"


def _local(jd: float, utc_offset: float = DEFAULT_UTC_OFFSET):
    """A library JD as (year, month, day, fraction of day) in ``utc_offset``."""
    y, m, d, hour = clock_from_jd(jd, float(utc_offset))
    return y, m, d, hour / 24.0


# ── Tool implementations ────────────────────────────────────────

def compute_planet_position(
    planet: str,
    year: int,
    month: int = 1,
    day: float = 1.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute a planet's sidereal position using SS algorithms (Ch.1-2)."""
    try:
        from suryasiddhanta.ch02_true_places import compute
        pos = compute(planet.capitalize(), year, month, _lib_day(day, utc_offset))
        return json.dumps({
            "planet": pos.planet,
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "true_longitude": round(pos.true_longitude, 3),
            "mean_longitude": round(pos.mean_lon, 3),
            "manda_correction": round(pos.manda_corr, 3),
            "sighra_correction": round(pos.sighra_corr, 3) if pos.sighra_corr else None,
            "ayanamsha": round(pos.ayanamsha, 3),
            "tropical_longitude": round(pos.tropical_longitude, 3),
            "nakshatra": pos.nakshatra,
            "rashi": pos.rashi,
            "ahargana": round(pos.ahargana, 1),
            "summary": (
                f"{pos.planet} at {pos.true_longitude:.2f}° sidereal longitude "
                f"on {year}-{month:02d}-{int(day):02d}. "
                f"Nakshatra: {pos.nakshatra['name']} (pada {pos.nakshatra['pada']}), "
                f"Rashi: {pos.rashi['name']}. "
                f"Mean lon {pos.mean_lon:.2f}°, manda correction {pos.manda_corr:+.2f}°."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "planet": planet, "year": year})


def compute_all_planets(
    year: int,
    month: int = 1,
    day: float = 1.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute all 7 classical planet positions for a date (Ch.1-2)."""
    try:
        from suryasiddhanta.ch02_true_places import compute_all
        positions = compute_all(year, month, _lib_day(day, utc_offset))
        result = {"date": f"{year}-{month:02d}-{int(day):02d}", "planets": {}}
        for name, pos in positions.items():
            result["planets"][name] = {
                "true_longitude": round(pos.true_longitude, 3),
                "nakshatra": pos.nakshatra["name"],
                "pada": pos.nakshatra["pada"],
                "rashi": pos.rashi["name"],
                "mean_longitude": round(pos.mean_lon, 3),
                "manda_correction": round(pos.manda_corr, 3),
            }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_panchanga(
    year: int,
    month: int = 1,
    day: float = 1.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute the Panchanga (tithi, vara, nakshatra, yoga, karana) for a date (Ch.1-3)."""
    try:
        from suryasiddhanta.ch01_mean_motions import (
            julian_day, tithi_from_elongation, vara, nakshatra_from_longitude,
            masa_from_sun_longitude, ritu_from_sun_longitude, samvatsara,
        )
        from suryasiddhanta.ch02_true_places import compute

        jd = julian_day(year, month, _lib_day(day, utc_offset))
        sun = compute("Sun", year, month, _lib_day(day, utc_offset))
        moon = compute("Moon", year, month, _lib_day(day, utc_offset))

        tithi_num, tithi_frac = tithi_from_elongation(moon.true_longitude, sun.true_longitude)
        # The weekday turns at local midnight (SS i.66), so it is read off
        # the civil date as given, not the instant shifted to Ujjain time.
        vara_num, vara_name = vara(julian_day(year, month, float(day)))
        nak_num, nak_name, nak_pada, nak_frac = nakshatra_from_longitude(moon.true_longitude)
        masa_num, masa_name = masa_from_sun_longitude(sun.true_longitude)
        ritu_num, ritu_name = ritu_from_sun_longitude(sun.true_longitude)
        samv_num, samv_name = samvatsara(jd)

        # Yoga = (Sun + Moon) / 13°20'
        yoga_val = (sun.true_longitude + moon.true_longitude) % 360.0
        yoga_num = int(yoga_val / (800.0 / 60.0)) + 1

        # Karana = half-tithi
        elongation = (moon.true_longitude - sun.true_longitude) % 360.0
        karana_num = int(elongation / 6.0) + 1

        result = {
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "tithi": {"number": tithi_num, "fraction": round(tithi_frac, 3)},
            "vara": {"number": vara_num, "name": vara_name},
            # nakshatra_from_longitude returns a 0-based index; report it
            # 1-based like tithi/yoga/karana beside it.
            "nakshatra": {"number": nak_num + 1, "name": nak_name, "pada": nak_pada},
            "yoga": {"number": yoga_num},
            "karana": {"number": karana_num},
            "masa": {"number": masa_num, "name": masa_name},
            "ritu": {"number": ritu_num, "name": ritu_name},
            "samvatsara": {"number": samv_num, "name": samv_name},
            "sun_longitude": round(sun.true_longitude, 3),
            "moon_longitude": round(moon.true_longitude, 3),
            "ayanamsha": round(sun.ayanamsha, 3),
            "summary": (
                f"Panchanga for {year}-{month:02d}-{int(day):02d}: "
                f"Tithi #{tithi_num}, Vara {vara_name}, "
                f"Nakshatra {nak_name} (pada {nak_pada}), "
                f"Masa {masa_name}, Ritu {ritu_name}, "
                f"Samvatsara {samv_name}."
            ),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_ahargana(
    year: int,
    month: int = 1,
    day: float = 1.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute ahargana (day count from Kali epoch) and related time info (Ch.1)."""
    try:
        from suryasiddhanta.ch01_mean_motions import (
            julian_day, ahargana, kali_years_elapsed, kali_era_year, vara,
            KALI_EPOCH_JD,
        )
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        a = ahargana(jd)
        ky = kali_years_elapsed(jd)
        era = kali_era_year(jd)
        # The weekday turns at local midnight (SS i.66), so it is read off
        # the civil date as given, not the instant shifted to Ujjain time.
        v_num, v_name = vara(julian_day(year, month, float(day)))
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "julian_day": round(jd, 2),
            "ahargana": round(a, 2),
            "kali_era_year": era,
            "kali_years": round(ky, 2),
            "vara": v_name,
            "kali_epoch_jd": KALI_EPOCH_JD,
            "summary": (
                f"{year}-{month:02d}-{int(day):02d} falls in Kali era year {era} "
                f"({ky:.2f} years elapsed since the epoch, which is what "
                f"kali_years reports — one less than the era number). "
                f"Ahargana = {a:.1f} days. JD = {jd:.2f}. Vara = {v_name}."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_ahargana_verse_route(
    years: int,
    months: int = 0,
    tithis: int = 0,
    from_creation: bool = False,
) -> str:
    """Compute the ahargana by the text's own luni-solar route, SS i.48-51 (Ch.1)."""
    try:
        from suryasiddhanta.ch01_mean_motions import (
            adhimasa_elapsed, tithikshaya_elapsed, ahargana_from_luni_solar,
            YEARS_CREATION_TO_KALI, CIVIL_DAYS_CREATION_TO_KALI,
        )
        total_years = int(years)
        if not from_creation:
            total_years += YEARS_CREATION_TO_KALI
        solar_months = total_years * 12 + int(months)
        adhimasa = adhimasa_elapsed(solar_months)
        lunar_months = solar_months + adhimasa
        lunar_days = lunar_months * 30 + int(tithis)
        tithikshaya = tithikshaya_elapsed(lunar_days)
        civil_days = ahargana_from_luni_solar(
            int(years), int(months), int(tithis), from_creation=bool(from_creation)
        )
        era = "the end of creation" if from_creation else "the Kali epoch"
        note = (
            " Every total above runs from creation even so, because intercalary "
            "months accumulate from there; the last step takes "
            f"{CIVIL_DAYS_CREATION_TO_KALI:,} civil days off, as v.56 allows. "
            "The result is the same number plain subtraction from the Kali epoch "
            "gives — the intercalary months cancel."
            if not from_creation else ""
        )
        return json.dumps({
            "elapsed": {"years": int(years), "months": int(months), "tithis": int(tithis)},
            "reckoned_from": era,
            "totals_reckoned_from": "the end of creation",
            "solar_months": solar_months,
            "adhimasa": adhimasa,
            "lunar_months": lunar_months,
            "lunar_days": lunar_days,
            "tithikshaya": tithikshaya,
            "civil_days": civil_days,
            "creation_to_kali_civil_days": CIVIL_DAYS_CREATION_TO_KALI,
            "summary": (
                f"SS i.48-51, reckoning from {era}: {years} y., {months} m., "
                f"{tithis} d. elapsed = {solar_months:,} solar months, "
                f"+ {adhimasa:,} intercalary (adhimasa) = {lunar_months:,} lunar "
                f"months = {lunar_days:,} lunar days, - {tithikshaya:,} omitted "
                f"(tithikshaya) = {civil_days:,} civil days.{note}"
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_sine_table() -> str:
    """Return the SS 24-entry jya (sine) table with accuracy report (Ch.2)."""
    try:
        from suryasiddhanta.ch02_true_places import (
            JYA_TABLE, R_SINE, table_accuracy_report,
        )
        report = table_accuracy_report()
        entries = []
        for i, val in enumerate(JYA_TABLE):
            angle = (i + 1) * 3.75
            entries.append({
                "index": i + 1,
                "angle_deg": angle,
                "jya_value": val,
                "sin_approx": round(val / R_SINE, 6),
            })
        return json.dumps({
            "R_sine": R_SINE,
            "step_degrees": 3.75,
            "entries": entries,
            "accuracy": report,
            "summary": (
                f"SS sine table: 24 entries at 3°45' intervals, R={R_SINE}. "
                f"Max error: {report.get('max_error_arcmin', 'N/A')} arcminutes."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_ayanamsha(
    year: int,
    month: int = 1,
    day: float = 1.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute SS ayanamsha (sidereal-tropical offset) for a date (Ch.2)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch02_true_places import ayanamsha
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        aya = ayanamsha(jd)
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "ayanamsha_degrees": round(aya, 4),
            "model": "oscillatory trepidation",
            "amplitude": 27.0,
            "period_years": 7200,
            "zero_year": "499 CE",
            "summary": (
                f"SS ayanamsha on {year}-{month:02d}-{int(day):02d}: {aya:.4f}°. "
                f"Model: ±27° oscillation over 7200 years, zero at 499 CE."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_day_length(
    year: int,
    month: int,
    day: float,
    latitude: float,
) -> str:
    """Compute day/night length and sunrise data for a location (Ch.3)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch02_true_places import compute
        from suryasiddhanta.ch03_direction_place_time import (
            day_length_ghatis, night_length_ghatis, declination,
            sunrise_hour_angle, OBLIQUITY_DEGREES,
        )
        sun = compute("Sun", year, month, float(day))
        day_gh = day_length_ghatis(latitude, sun.true_longitude)
        night_gh = night_length_ghatis(latitude, sun.true_longitude)
        dec = declination(sun.true_longitude, OBLIQUITY_DEGREES)
        ha = sunrise_hour_angle(latitude, dec)
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "latitude": latitude,
            "sun_longitude": round(sun.true_longitude, 3),
            "declination": round(dec, 3),
            "day_length_ghatis": round(day_gh, 2),
            "night_length_ghatis": round(night_gh, 2),
            "day_length_hours": round(day_gh * 24.0 / 60.0, 2),
            "sunrise_hour_angle": round(ha, 3),
            "summary": (
                f"Day length at lat {latitude}° on {year}-{month:02d}-{int(day):02d}: "
                f"{day_gh:.1f} ghatis ({day_gh * 24.0 / 60.0:.1f} hours). "
                f"Night: {night_gh:.1f} ghatis. Sun declination: {dec:.2f}°."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_lagna(
    year: int,
    month: int,
    day: float,
    latitude: float,
    longitude: float,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute the ascendant (lagna) for a date/time/place (Ch.3)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch03_direction_place_time import lagna
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        lagna_lon, rashi_num, rashi_name = lagna(jd, latitude, longitude)
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "latitude": latitude,
            "longitude": longitude,
            "lagna_longitude": round(lagna_lon, 3),
            "rashi_number": rashi_num,
            "rashi_name": rashi_name,
            "summary": (
                f"Lagna (ascendant) at ({latitude}°, {longitude}°) on "
                f"{year}-{month:02d}-{int(day):02d}: "
                f"{lagna_lon:.2f}° = {rashi_name} rashi."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_gnomon_shadow(
    year: int,
    month: int,
    day: float,
    latitude: float,
    longitude: float,
    gnomon_length: float = 12.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute gnomon shadow at a date/time/place (Ch.3)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch02_true_places import compute
        from suryasiddhanta.ch03_direction_place_time import (
            declination, equatorial_to_horizontal,
            right_ascension, local_sidereal_time,
            gnomon_shadow, OBLIQUITY_DEGREES,
        )
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        sun = compute("Sun", year, month, _lib_day(day, utc_offset))
        dec = declination(sun.tropical_longitude, OBLIQUITY_DEGREES)
        ra = right_ascension(sun.tropical_longitude, OBLIQUITY_DEGREES)
        lst = local_sidereal_time(jd, longitude)
        az, alt = equatorial_to_horizontal(ra, dec, lst, latitude)
        if alt <= 0:
            return json.dumps({
                "summary": f"Sun below horizon (altitude {alt:.1f}°). No shadow.",
                "altitude": round(alt, 2),
            })
        result = gnomon_shadow(alt, gnomon_length, sun_azimuth_deg=az)
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "latitude": latitude,
            "longitude": longitude,
            "gnomon_length": gnomon_length,
            "shadow_length": round(result.shadow_length, 2),
            "sun_altitude": round(result.altitude_deg, 2),
            "sun_azimuth": round(az, 2),
            "direction": result.direction,
            "summary": (
                f"Gnomon ({gnomon_length}) shadow = {result.shadow_length:.2f} "
                f"at lat {latitude}°. Sun altitude {result.altitude_deg:.1f}°, "
                f"azimuth {az:.1f}° ({result.direction})."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_lunar_eclipse(
    year: int,
    month: int,
    day: float = 15.0,
) -> str:
    """Predict a lunar eclipse using SS method (Ch.4)."""
    try:
        from suryasiddhanta.ch04_lunar_eclipses import compute_lunar_eclipse as _compute
        ec = _compute(year, month, float(day))
        result = {
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "is_eclipse": ec.is_eclipse,
            "eclipse_type": ec.eclipse_type,
            "magnitude": round(ec.magnitude, 3),
            "moon_latitude_arcmin": round(ec.moon_latitude, 1),
            "moon_diameter_arcmin": round(ec.moon_diameter, 1),
            "shadow_diameter_arcmin": round(ec.shadow_diameter, 1),
            "half_duration_min": round(ec.half_duration, 1) if ec.half_duration else None,
            "totality_half_min": round(ec.totality_half, 1) if ec.totality_half else None,
            "notes": ec.notes,
        }
        if ec.is_eclipse:
            result["summary"] = (
                f"{ec.eclipse_type.upper()} lunar eclipse near {year}-{month:02d}. "
                f"Magnitude: {ec.magnitude:.3f}. "
                f"Half-duration: {ec.half_duration:.1f} min. "
                f"Moon latitude: {ec.moon_latitude:.1f}'."
            )
        else:
            result["summary"] = f"No lunar eclipse near {year}-{month:02d}-{int(day):02d}."
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_solar_eclipse(
    year: int,
    month: int,
    day: float = 1.0,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> str:
    """Predict a solar eclipse using SS method (Ch.5), optionally topocentric."""
    try:
        if (latitude is None) != (longitude is None):
            raise ValueError("Provide both latitude and longitude for a local eclipse")
        if latitude is not None and longitude is not None:
            from suryasiddhanta.ch05_solar_eclipses import compute_solar_eclipse_topocentric as _compute
            ec = _compute(year, month, float(day), latitude, longitude)
        else:
            from suryasiddhanta.ch05_solar_eclipses import compute_solar_eclipse as _compute
            ec = _compute(year, month, float(day))
        result = {
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "is_eclipse": ec.is_eclipse,
            "eclipse_type": ec.eclipse_type,
            "magnitude": round(ec.magnitude, 3),
            "sun_diameter_arcmin": round(ec.sun_diameter, 1),
            "moon_diameter_arcmin": round(ec.moon_diameter, 1),
            "lambana_arcmin": round(ec.lambana, 1) if ec.lambana else None,
            "nati_arcmin": round(ec.nati, 1) if ec.nati else None,
            "half_duration_min": round(ec.half_duration, 1) if ec.half_duration else None,
            "notes": ec.notes,
        }
        if ec.locally_visible is not None:
            result["locally_visible"] = ec.locally_visible
            result["sun_altitude_deg"] = ec.sun_altitude_deg
        if ec.is_eclipse:
            result["summary"] = (
                f"{ec.eclipse_type.upper()} solar eclipse near {year}-{month:02d}. "
                f"Magnitude: {ec.magnitude:.3f}."
            )
            if ec.lambana is not None:
                result["summary"] += f" Parallax (lambana): {ec.lambana:.1f}'."
            if ec.locally_visible is False:
                result["summary"] += " The Sun is below the local horizon at conjunction."
        else:
            result["summary"] = f"No solar eclipse near {year}-{month:02d}-{int(day):02d}."
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_eclipse_diagram(
    eclipse_type: str,
    year: int,
    month: int,
    day: float = 15.0,
    latitude: float = 23.0,
    longitude: float = 82.0,
) -> str:
    """Generate eclipse projection diagram data (Ch.6). Returns contact points + path."""
    try:
        if eclipse_type.lower() == "lunar":
            from suryasiddhanta.ch04_lunar_eclipses import compute_lunar_eclipse
            ec = compute_lunar_eclipse(year, month, float(day))
        else:
            from suryasiddhanta.ch05_solar_eclipses import compute_solar_eclipse_topocentric
            ec = compute_solar_eclipse_topocentric(year, month, float(day), latitude, longitude)

        if not ec.is_eclipse:
            return json.dumps({"summary": "No eclipse — cannot generate diagram.", "is_eclipse": False})

        from suryasiddhanta.ch06_eclipse_projection import eclipse_diagram_data
        diag = eclipse_diagram_data(ec, latitude, longitude)
        return json.dumps({
            "eclipse_type": diag.eclipse_type,
            "eclipsed_body": diag.eclipsed_body,
            "eclipsed_radius": round(diag.eclipsed_radius, 2),
            "eclipser_radius": round(diag.eclipser_radius, 2),
            "ayana_valana_deg": round(diag.ayana_valana, 2),
            "aksha_valana_deg": round(diag.aksha_valana, 2),
            "total_valana_deg": round(diag.valana, 2),
            "first_contact_pa": round(diag.first_contact_pa, 2) if diag.first_contact_pa is not None else None,
            "last_contact_pa": round(diag.last_contact_pa, 2) if diag.last_contact_pa is not None else None,
            "path_points": len(diag.path),
            "summary": (
                f"{diag.eclipse_type} eclipse diagram: "
                f"valana {diag.valana:.1f}° "
                f"(ayana {diag.ayana_valana:.1f}° + aksha {diag.aksha_valana:.1f}°). "
                f"Contact PAs: {diag.first_contact_pa:.1f}°/{diag.last_contact_pa:.1f}°."
                if diag.first_contact_pa is not None else
                f"{diag.eclipse_type} eclipse diagram: valana {diag.valana:.1f}°."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def find_conjunctions(
    planet1: str,
    planet2: str,
    year: int,
    month: int = 1,
    months: int = 12,
) -> str:
    """Find planetary conjunctions over a period (Ch.7)."""
    try:
        from suryasiddhanta.ch07_conjunctions import planet_planet_conjunction
        conjs = planet_planet_conjunction(
            planet1.capitalize(), planet2.capitalize(),
            year, month, months,
        )
        results = []
        for c in conjs:
            from suryasiddhanta.ch01_mean_motions import from_julian_day
            y, m, d, _ = _local(c.jd)
            results.append({
                "date": f"{y}-{m:02d}-{int(d):02d}",
                "jd": round(c.jd, 2),
                "longitude": round(c.longitude, 2),
                "separation_deg": round(c.separation_deg, 3),
                "type": c.conjunction_type,
            })
        summary = f"Found {len(results)} conjunction(s) of {planet1}–{planet2} in {year}."
        if results:
            first = results[0]
            summary += f" First: {first['date']} at {first['longitude']:.1f}° ({first['type']})."
        return json.dumps({"conjunctions": results, "summary": summary}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def find_star_conjunction(
    planet: str,
    star_name: str,
    year: int,
    months: int = 12,
) -> str:
    """Find conjunctions of a planet with a yogatara (junction star) (Ch.7)."""
    try:
        from suryasiddhanta.ch07_conjunctions import planet_star_conjunction
        conjs = planet_star_conjunction(planet.capitalize(), star_name, year, months)
        results = []
        for c in conjs:
            from suryasiddhanta.ch01_mean_motions import from_julian_day
            y, m, d, _ = _local(c.jd)
            results.append({
                "date": f"{y}-{m:02d}-{int(d):02d}",
                "longitude": round(c.longitude, 2),
                "separation_deg": round(c.separation_deg, 3),
                "type": c.conjunction_type,
            })
        summary = f"Found {len(results)} conjunction(s) of {planet} with {star_name} in {year}."
        return json.dumps({"conjunctions": results, "summary": summary}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_nakshatra_info(nakshatra_name: str) -> str:
    """Look up nakshatra details from the 27-star catalog (Ch.8)."""
    try:
        from suryasiddhanta.ch08_stars import get_nakshatra
        nak = get_nakshatra(nakshatra_name)
        return json.dumps({
            "number": nak.number,
            "name": nak.name,
            "devanagari": nak.devanagari,
            "longitude": nak.longitude,
            "latitude": nak.latitude,
            "star": nak.star,
            "span_start": nak.span_start,
            "span_end": nak.span_end,
            "deity": nak.deity,
            "gana": nak.gana,
            "summary": (
                f"{nak.name} ({nak.devanagari}): yogatara at "
                f"({nak.longitude:.1f}°, {nak.latitude:.1f}°), "
                f"star {nak.star}. Deity: {nak.deity}, Gana: {nak.gana}. "
                f"Span: {nak.span_start:.2f}°–{nak.span_end:.2f}°."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_star_position(
    star_name: str,
    year: int,
    month: int = 1,
    day: float = 1.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute a yogatara's position at a given epoch (Ch.8)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch08_stars import star_position
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        sp = star_position(star_name, jd)
        return json.dumps({
            "star": sp.name,
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "sidereal_longitude": round(sp.sidereal_lon, 3),
            "sidereal_latitude": round(sp.sidereal_lat, 3),
            "tropical_longitude": round(sp.tropical_lon, 3),
            "right_ascension": round(sp.right_ascension, 3),
            "declination": round(sp.declination_val, 3),
            "ayanamsha": round(sp.ayanamsha_val, 3),
            "summary": (
                f"{sp.name} at epoch {year}: "
                f"sidereal {sp.sidereal_lon:.2f}°, tropical {sp.tropical_lon:.2f}°, "
                f"RA {sp.right_ascension:.2f}°, Dec {sp.declination_val:.2f}°."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_star_rise_set(
    star_name: str,
    year: int,
    month: int,
    day: float,
    latitude: float,
    longitude: float,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute rise/set times of a yogatara (Ch.8)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch08_stars import star_rise_set
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        rs = star_rise_set(star_name, jd, latitude, longitude)
        result = {
            "star": rs.name,
            "rises": rs.rises,
            "sets": rs.sets,
            "is_circumpolar": rs.is_circumpolar,
            "is_never_visible": rs.is_never_visible,
        }
        if rs.rise_jd:
            from suryasiddhanta.ch01_mean_motions import from_julian_day
            ry, rm, rd, _ = _local(rs.rise_jd, utc_offset)
            result["rise_date"] = f"{ry}-{rm:02d}-{int(rd):02d}"
        if rs.set_jd:
            from suryasiddhanta.ch01_mean_motions import from_julian_day
            sy, sm, sd, _ = _local(rs.set_jd, utc_offset)
            result["set_date"] = f"{sy}-{sm:02d}-{int(sd):02d}"
        if rs.is_circumpolar:
            result["summary"] = f"{rs.name} is circumpolar at lat {latitude}° — always above horizon."
        elif rs.is_never_visible:
            result["summary"] = f"{rs.name} is never visible at lat {latitude}°."
        else:
            result["summary"] = f"{rs.name} rises and sets at lat {latitude}°."
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_heliacal_rising(
    planet: str,
    year: int,
    latitude: float = 23.0,
    start_month: int = 1,
) -> str:
    """Find next heliacal rising of a planet (Ch.9)."""
    try:
        from suryasiddhanta.ch09_heliacal import heliacal_rising
        event = heliacal_rising(planet.capitalize(), year, latitude, start_month)
        if event is None:
            return json.dumps({
                "summary": f"No heliacal rising found for {planet} in {year} from month {start_month}."
            })
        from suryasiddhanta.ch01_mean_motions import from_julian_day
        y, m, d, _ = _local(event.jd)
        return json.dumps({
            "planet": event.planet,
            "event_type": event.event_type,
            "date": f"{y}-{m:02d}-{int(d):02d}",
            "jd": round(event.jd, 2),
            "elongation": round(event.elongation, 2),
            "direction": event.direction,
            "summary": (
                f"Heliacal rising of {event.planet}: {y}-{m:02d}-{int(d):02d}. "
                f"Sun elongation: {event.elongation:.1f}°. Direction: {event.direction}."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_heliacal_setting(
    planet: str,
    year: int,
    latitude: float = 23.0,
    start_month: int = 1,
) -> str:
    """Find next heliacal setting of a planet (Ch.9)."""
    try:
        from suryasiddhanta.ch09_heliacal import heliacal_setting
        event = heliacal_setting(planet.capitalize(), year, latitude, start_month)
        if event is None:
            return json.dumps({
                "summary": f"No heliacal setting found for {planet} in {year} from month {start_month}."
            })
        from suryasiddhanta.ch01_mean_motions import from_julian_day
        y, m, d, _ = _local(event.jd)
        return json.dumps({
            "planet": event.planet,
            "event_type": event.event_type,
            "date": f"{y}-{m:02d}-{int(d):02d}",
            "jd": round(event.jd, 2),
            "elongation": round(event.elongation, 2),
            "direction": event.direction,
            "summary": (
                f"Heliacal setting of {event.planet}: {y}-{m:02d}-{int(d):02d}. "
                f"Sun elongation: {event.elongation:.1f}°. Direction: {event.direction}."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_visibility_events(
    planet: str,
    year: int,
    months: int = 12,
) -> str:
    """List all heliacal risings and settings over a period (Ch.9)."""
    try:
        from suryasiddhanta.ch09_heliacal import visibility_events
        events = visibility_events(planet.capitalize(), year, months)
        results = []
        for ev in events:
            from suryasiddhanta.ch01_mean_motions import from_julian_day
            y, m, d, _ = _local(ev.jd)
            results.append({
                "type": ev.event_type,
                "date": f"{y}-{m:02d}-{int(d):02d}",
                "elongation": round(ev.elongation, 2),
                "direction": ev.direction,
            })
        summary = f"{len(results)} visibility event(s) for {planet} in {year}."
        return json.dumps({"events": results, "summary": summary}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_moon_phase(
    year: int,
    month: int,
    day: float = 1.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute lunar phase, illumination, and horn angle (Ch.10)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch10_lunar_horns import (
            moon_elongation, illuminated_fraction, phase_name,
            is_waxing, crescent_width, bright_limb_angle,
        )
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        elong = moon_elongation(jd)
        illum = illuminated_fraction(jd)
        phase = phase_name(jd)
        waxing = is_waxing(jd)
        crescent = crescent_width(jd)
        limb = bright_limb_angle(jd)
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "elongation_deg": round(elong, 2),
            "illuminated_fraction": round(illum, 4),
            "illuminated_percent": round(illum * 100, 1),
            "phase_name": phase,
            "is_waxing": waxing,
            "crescent_width_arcmin": round(crescent, 2),
            "bright_limb_angle_deg": round(limb, 2),
            "summary": (
                f"Moon on {year}-{month:02d}-{int(day):02d}: "
                f"{phase} ({illum * 100:.1f}% illuminated, "
                f"{'waxing' if waxing else 'waning'}). "
                f"Elongation: {elong:.1f}°. "
                f"Crescent width: {crescent:.1f}'. "
                f"Bright limb angle: {limb:.1f}°."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_horn_angle(
    year: int,
    month: int,
    day: float,
    latitude: float,
    longitude: float,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute the horn angle of the lunar crescent from a location (Ch.10)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch10_lunar_horns import (
            horn_angle, illuminated_fraction, phase_name, is_waxing,
        )
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        angle = horn_angle(jd, latitude, longitude)
        illum = illuminated_fraction(jd)
        phase = phase_name(jd)
        waxing = is_waxing(jd)
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "latitude": latitude,
            "longitude": longitude,
            "horn_angle_deg": round(angle, 2),
            "illuminated_fraction": round(illum, 4),
            "phase_name": phase,
            "is_waxing": waxing,
            "summary": (
                f"Lunar horn angle at ({latitude}°, {longitude}°) on "
                f"{year}-{month:02d}-{int(day):02d}: {angle:.1f}°. "
                f"Phase: {phase} ({illum * 100:.1f}%, "
                f"{'waxing' if waxing else 'waning'})."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_moonrise_moonset(
    year: int,
    month: int,
    day: float,
    latitude: float,
    longitude: float,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Compute moonrise and moonset times for a location (Ch.10)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day, from_julian_day
        from suryasiddhanta.ch10_lunar_horns import moonrise, moonset
        jd = julian_day(year, month, _lib_day(day, utc_offset))
        rise_jd = moonrise(jd, latitude, longitude)
        set_jd = moonset(jd, latitude, longitude)
        result = {
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "latitude": latitude,
            "longitude": longitude,
            "zone": _zone(utc_offset),
        }
        parts = []
        if rise_jd:
            ry, rm, rd, rf = _local(rise_jd, utc_offset)
            h, m_val, s = int(rf * 24), int((rf * 24 % 1) * 60), 0
            result["moonrise_jd"] = round(rise_jd, 4)
            result["moonrise_time"] = f"{h:02d}:{m_val:02d}"
            parts.append(f"Moonrise ~{h:02d}:{m_val:02d}")
        else:
            parts.append("No moonrise")
        if set_jd:
            sy, sm, sd, sf = _local(set_jd, utc_offset)
            h, m_val, s = int(sf * 24), int((sf * 24 % 1) * 60), 0
            result["moonset_jd"] = round(set_jd, 4)
            result["moonset_time"] = f"{h:02d}:{m_val:02d}"
            parts.append(f"moonset ~{h:02d}:{m_val:02d}")
        else:
            parts.append("no moonset")
        result["summary"] = (f"At ({latitude}°, {longitude}°) on {year}-{month:02d}-{int(day):02d}: "
                             + ", ".join(parts) + f" ({_zone(utc_offset)}).")
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _jd_datetime(jd: float, utc_offset: float = DEFAULT_UTC_OFFSET) -> str:
    """Format a library JD as 'YYYY-MM-DD HH:MM (UTC+05:30)' in ``utc_offset``."""
    y, m, d, hours = clock_from_jd(jd, float(utc_offset))
    return (f"{y}-{m:02d}-{d:02d} {int(hours):02d}:{int(hours % 1 * 60):02d}"
            f" ({_zone(utc_offset)})")


def find_patas(
    year: int,
    month: int = 1,
    day: float = 1.0,
    days: int = 60,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """List the patas (Vyatipata, Vaidhrita) falling in a date range (Ch.11)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch11_pata import find_patas as _find

        jd0 = julian_day(year, month, _lib_day(day, utc_offset))
        events = _find(jd0, jd0 + int(days))
        return json.dumps({
            "start_date": f"{year}-{month:02d}-{int(day):02d}",
            "days": int(days),
            "count": len(events),
            "events": [
                {
                    "kind": ev.kind,
                    "begin": _jd_datetime(ev.jd_begin, utc_offset),
                    "middle": _jd_datetime(ev.jd_middle, utc_offset),
                    "end": _jd_datetime(ev.jd_end, utc_offset),
                    "nominal_crossing": _jd_datetime(ev.jd_sum_crossing, utc_offset),
                    "jd_middle": ev.jd_middle,
                    "duration_ghatis": round(ev.duration_ghatis, 2),
                    "duration_hours": round(ev.duration_hours, 2),
                    "sun_declination": ev.sun_declination,
                    "moon_declination": ev.moon_declination,
                    "moon_latitude_arcmin": ev.moon_latitude,
                    "longitude_sum": ev.longitude_sum,
                    "refined": ev.refined,
                }
                for ev in events
            ],
            "summary": (
                f"{len(events)} pata(s) in {int(days)} days from "
                f"{year}-{month:02d}-{int(day):02d}. A pata is the moment the "
                f"Sun's and Moon's declinations become equal in amount "
                f"(Ch.11) — not the nitya-yoga of the same name that "
                f"compute_panchanga reports."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "year": year})


def compute_pata_details(
    year: int,
    month: int,
    day: float,
    hour: float = 0.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Report the pata in progress at a moment and the next one due (Ch.11)."""
    try:
        from suryasiddhanta.ch01_mean_motions import julian_day
        from suryasiddhanta.ch11_pata import active_pata, find_next_pata

        jd = julian_day(year, month, _lib_day(day, utc_offset)) + float(hour) / 24.0
        current = active_pata(jd)
        nxt = find_next_pata(jd)
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "hour": hour,
            "active": None if current is None else {
                "kind": current.kind,
                "begin": _jd_datetime(current.jd_begin, utc_offset),
                "end": _jd_datetime(current.jd_end, utc_offset),
                "duration_ghatis": round(current.duration_ghatis, 2),
                "sun_declination": current.sun_declination,
                "moon_declination": current.moon_declination,
            },
            "next": None if nxt is None else {
                "kind": nxt.kind,
                "begin": _jd_datetime(nxt.jd_begin, utc_offset),
                "middle": _jd_datetime(nxt.jd_middle, utc_offset),
                "end": _jd_datetime(nxt.jd_end, utc_offset),
                "duration_ghatis": round(nxt.duration_ghatis, 2),
                "sun_declination": nxt.sun_declination,
                "moon_declination": nxt.moon_declination,
            },
            "summary": (
                (f"{current.kind} in progress until "
                 f"{_jd_datetime(current.jd_end, utc_offset)}. "
                 if current else "No pata in progress. ")
                + (f"Next: {nxt.kind} at {_jd_datetime(nxt.jd_middle, utc_offset)}."
                   if nxt else "No pata within 60 days.")
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "year": year})


def get_earth_dimensions(
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> str:
    """Report the earth's size and how the sky behaves at a place (Ch.12)."""
    try:
        from suryasiddhanta import ch12_cosmography as ch12
        from suryasiddhanta.ch01_mean_motions import (
            LANKA_MERIDIAN_LONGITUDE, MEAN_DAILY_MOTION,
        )

        lat, lon = float(latitude), float(longitude)
        # Difference of longitude from the Lanka meridian (SS i.62), wrapped
        # so a place just across the antimeridian is not reported as far.
        offset = abs((lon - LANKA_MERIDIAN_LONGITUDE + 180.0) % 360.0 - 180.0)
        parallel = ch12.corrected_circumference(lat)
        yojanas = ch12.desantara_yojanas(lat, lon)
        aspect = ch12.sphere_aspect(lat)
        polar = ch12.polar_day_limit()
        return json.dumps({
            "latitude": lat,
            "longitude": lon,
            "earth_diameter_yojanas": ch12.EARTH_DIAMETER_YOJANA,
            "earth_circumference_yojanas": round(ch12.earth_circumference(), 3),
            "corrected_circumference_yojanas": round(parallel, 3),
            "desantara": {
                "yojanas": round(yojanas, 3),
                "ghatis": round(offset / 360.0 * 60.0, 4),
                "corrections_arcmin": {
                    planet: round(
                        ch12.desantara_correction(
                            MEAN_DAILY_MOTION[planet] * 60.0, lat, lon), 4)
                    for planet in ("Sun", "Moon")
                },
                "note": (
                    "Subtracted from the mean place east of the Lanka "
                    "meridian, added west (SS i.61)."
                ),
            },
            "sphere_aspect": aspect,
            "polar_day_limit": {k: (round(v, 4) if isinstance(v, float) else v)
                                for k, v in polar.items()},
            "invisibility_limits": [
                {k: (round(v, 4) if isinstance(v, float) else v)
                 for k, v in entry.items()}
                for entry in ch12.invisibility_limits()
            ],
            "solar_overhead_band": {
                k: (round(v, 4) if isinstance(v, float) else v)
                for k, v in ch12.solar_overhead_band().items()
            },
            "summary": (
                f"The earth is 1,600 yojanas across and "
                f"{ch12.earth_circumference():,.3f} round (SS i.59). At "
                f"latitude {lat}° its parallel is {parallel:,.1f} yojanas and "
                f"the pole stands {aspect['pole_altitude']:.2f}° up; the "
                f"sphere is {aspect['kind']}. The day first reaches sixty "
                f"nadis at {polar['latitude']:.1f}° (SS xii.60)."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "latitude": latitude})


def get_planetary_orbits(body: Optional[str] = None) -> str:
    """Report the orbits, distances and linear speed of the planets (Ch.12)."""
    try:
        from suryasiddhanta import ch12_cosmography as ch12

        orbits = ch12.all_orbits()
        if body:
            wanted = str(body).capitalize()
            orbits = [o for o in orbits if o.body.lower() == str(body).lower()]
            if not orbits:
                return json.dumps({
                    "error": f"No orbit for {wanted!r}",
                    "known": [o.body for o in ch12.all_orbits()],
                })
        return json.dumps({
            "daily_linear_motion_yojanas": round(ch12.daily_linear_motion(), 4),
            "ether_orbit_yojanas": ch12.ETHER_ORBIT_YOJANAS,
            "moon_orbit_yojanas": ch12.MOON_ORBIT_YOJANAS,
            "orbits": [o.to_dict() for o in orbits],
            "order_outward": [e["name"] for e in ch12.orbital_order()],
            "summary": (
                "The Surya Siddhanta holds that every planet covers the same "
                f"{ch12.daily_linear_motion():,.3f} yojanas a day (SS xii.82), "
                "so an orbit is as large as the time the body takes to go "
                "round it. Only the Moon's 324,000 yojanas rests on a real "
                "calculation; the rest are derived from it. Derived orbits "
                "differ from the figures the text states in v.85-89 by under "
                "1.3 yojanas."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "body": body})


def get_cosmic_time(
    year: int,
    month: int = 1,
    day: float = 1.0,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """Report the days of gods, Fathers and Brahma, and the regents (Ch.12)."""
    try:
        from suryasiddhanta import ch12_cosmography as ch12
        from suryasiddhanta.ch01_mean_motions import julian_day

        jd = julian_day(year, month, _lib_day(day, utc_offset))
        elapsed = ch12.brahma_day_elapsed(jd)
        # The regents' days turn at local midnight (SS i.66), so they are read off
        # the civil date as given, not the instant shifted to Ujjain time.
        civil_jd = julian_day(year, month, float(day))
        return json.dumps({
            "date": f"{year}-{month:02d}-{int(day):02d}",
            "julian_day": jd,
            "day_lengths_in_days": {
                "gods_and_demons": round(ch12.day_of_the_gods(), 5),
                "fathers": round(ch12.day_of_the_manes(), 5),
                "mortals": 1.0,
                "brahma": ch12.day_of_brahma(),
            },
            "brahma_day": {
                "years_elapsed": round(elapsed["years_elapsed"], 2),
                "years_remaining": round(elapsed["years_remaining"], 2),
                "fraction_elapsed": round(elapsed["fraction"], 6),
                "kalpa_years": elapsed["kalpa_years"],
            },
            "regents": {
                "day": ch12.regent_of_day(civil_jd),
                "month": ch12.regent_of_month(civil_jd),
                "year": ch12.regent_of_year(civil_jd),
                "horas": [ch12.hora_lord(civil_jd, h) for h in range(24)],
                "order": ch12.REGENT_ORDER,
            },
            "day_and_night": ch12.load_catalog()["day_and_night"],
            "summary": (
                f"{ch12.regent_of_day(civil_jd)} rules the day, "
                f"{ch12.regent_of_month(civil_jd)} the 30-day month and "
                f"{ch12.regent_of_year(civil_jd)} the 360-day year (SS xii.78-79). The gods "
                f"at Meru see a day of six months, the Fathers in the moon a "
                f"day of a lunar month (SS xii.74). Brahma's present day is "
                f"{elapsed['fraction'] * 100:.2f}% elapsed."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "year": year})


def get_cosmology(section: Optional[str] = None) -> str:
    """Report the descriptive cosmology of Ch.12 -- creation, places, worlds."""
    try:
        from suryasiddhanta import ch12_cosmography as ch12

        catalog = ch12.load_catalog()
        sections = ("inquiries", "creation_sequence", "elements",
                    "planet_origins", "patalas", "reference_places",
                    "orbital_order", "regents", "day_and_night")
        if section:
            key = str(section).lower()
            if key not in sections:
                return json.dumps({
                    "error": f"Unknown section {section!r}", "known": list(sections),
                })
            return json.dumps({
                "section": key, "source": catalog["source"],
                key: catalog[key],
            }, indent=2)
        return json.dumps({
            "chapter": catalog["chapter"],
            "chapter_name_en": catalog["chapter_name_en"],
            "chapter_name_iast": catalog["chapter_name_iast"],
            "source": catalog["source"],
            "note": catalog["note"],
            **{key: catalog[key] for key in sections},
            "cities_clock_at_yamakoti_noon": {
                name: round(hour, 3)
                for name, hour in ch12.cities_clock("Yamakoti", 12.0).items()
            },
            "summary": (
                "Maya's nine questions and the Sun's answers (SS xii.1-9). The "
                "earth is a globe standing in space by its own force (xii.32), "
                "with seven unnamed patalas within it (xii.33), Meru at the "
                "north pole and Vadavamukha at the south, and four cities a "
                "quadrant apart on the equator: noon at Yamakoti is sunrise at "
                "Lanka, midnight at Romaka, sunset at Siddhapura (xii.70)."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "section": section})


def get_armillary_sphere(
    year: int,
    month: int = 1,
    day: float = 1.0,
    hour: float = 12.0,
    latitude: float = 23.18,
    longitude: float = 75.78,
    include_stars: bool = True,
    include_geometry: bool = False,
    utc_offset: float = DEFAULT_UTC_OFFSET,
) -> str:
    """
    Report the armillary sphere of Ch.13 set up for a place and moment.

    `hour` is clock time in `utc_offset` (IST by default). The compact form (default) lists each hoop's
    declination and day-radius, which is what a conversational answer
    needs; `include_geometry` adds the unit normals, offsets and point
    vectors the React page draws from, roughly quadrupling the payload.
    """
    try:
        from suryasiddhanta import ch13_instruments as ch13
        from suryasiddhanta.ch01_mean_motions import julian_day

        jd = julian_day(year, month, _lib_day(day, utc_offset) + float(hour) / 24.0)
        sphere = ch13.armillary_sphere(jd, float(latitude), float(longitude),
                                       include_stars=bool(include_stars))
        data = sphere.to_dict()
        if not include_geometry:
            data["hoops"] = [
                {k: h[k] for k in ("key", "name", "group", "declination",
                                   "day_radius", "verse")}
                for h in data["hoops"]
            ]
            for section in ("sign_points", "cardinal_points", "points"):
                for point in data[section]:
                    point.pop("vector", None)
            data.pop("zenith", None)
        points = {p.key: p for p in sphere.points}
        sines = sphere.sines
        data["summary"] = (
            f"The sphere at latitude {latitude}°: the pole raised {latitude}° "
            f"(SS xiii.15), turned to sidereal time {sphere.lst_deg:.2f}°. "
            f"{len(sphere.hoops)} hoops. Lagna {points['lagna'].tropical_longitude:.2f}°, "
            f"meridian point {points['madhya_lagna'].tropical_longitude:.2f}°, "
            f"Sun {points['sun'].tropical_longitude:.2f}° (tropical; SS xiii.13-14). "
            f"Carajya {sines['carajya']:.1f}, antya {sines['antya_great_circle']:.1f} "
            f"in R=3438 units (xiii.14-15; the verse's small-circle antya is "
            f"{sines['antya_small_circle']:.1f})."
        )
        data["hour"] = float(hour)
        data["utc_offset"] = float(utc_offset)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "year": year, "latitude": latitude})


def compute_clepsydra(
    sinkings: Optional[int] = None,
    ghatis: Optional[float] = None,
    partial: float = 0.0,
    year: Optional[int] = None,
    month: int = 1,
    day: float = 1.0,
    latitude: float = 23.18,
    observed_per_day: Optional[float] = None,
) -> str:
    """
    Water-clock arithmetic of Ch.13 v.23: sinkings to time, time to sinkings,
    the day and night in sinkings for a date and place, and the drift of a
    bowl that does not sink exactly sixty times a day. Any combination of
    the four may be asked for at once.
    """
    try:
        from suryasiddhanta import ch13_instruments as ch13
        from suryasiddhanta.ch01_mean_motions import julian_day

        if sinkings is None and ghatis is None and year is None and observed_per_day is None:
            return json.dumps({
                "error": "Give sinkings, ghatis, a date (year) or observed_per_day",
            })
        result: Dict[str, Any] = {
            "sinkings_per_day": ch13.SINKINGS_PER_DAY,
            "minutes_per_sinking": ch13.MINUTES_PER_SINKING,
            "vessel": ch13.load_catalog()["clepsydra_vessel"],
        }
        parts = []
        if sinkings is not None:
            reading = ch13.clepsydra_elapsed(int(sinkings), float(partial))
            result["elapsed"] = reading.to_dict()
            parts.append(
                f"{sinkings} sinkings{' and a ' + format(partial, '.0%') + ' fill' if partial else ''} "
                f"= {reading.to_dict()['ghati_pala_vipala']} ghatis = {reading.to_dict()['clock']}.")
        if ghatis is not None:
            reading = ch13.clepsydra_sinkings(float(ghatis))
            result["for_ghatis"] = reading.to_dict()
            parts.append(
                f"{ghatis} ghatis is {reading.sinkings} sinkings with the bowl "
                f"{reading.partial:.0%} full.")
        if year is not None:
            day_info = ch13.clepsydra_day(julian_day(int(year), int(month), float(day)),
                                          float(latitude))
            result["day_and_night"] = {
                k: (round(v, 4) if isinstance(v, float) else v)
                for k, v in day_info.items()
            }
            parts.append(
                f"On {year}-{int(month):02d}-{int(day):02d} at latitude {latitude}° the "
                f"bowl sinks {day_info['day_ghatis']:.2f} times from sunrise to sunset "
                f"and {day_info['night_ghatis']:.2f} times in the night.")
        if observed_per_day is not None:
            drift = ch13.clepsydra_drift(float(observed_per_day))
            result["drift"] = {k: (round(v, 4) if isinstance(v, float) else v)
                               for k, v in drift.items()}
            parts.append(
                f"A bowl sinking {observed_per_day} times a day is off by "
                f"{drift['error_minutes_per_sinking']:+.3f} minutes a sinking and reads "
                f"{drift['reading_error_minutes_per_day']:+.1f} minutes a day.")
        result["summary"] = (
            "A copper vessel with a hole in the bottom, set in water, sinks sixty "
            "times in a day and night (SS xiii.23), so each sinking is one ghati "
            "of 24 minutes. " + " ".join(parts) +
            " The vessel's dimensions come from the commentary, not the verse."
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def compute_instrument_time(
    instrument: str,
    value: float,
    year: int,
    month: int = 1,
    day: float = 1.0,
    latitude: float = 23.18,
    gnomon: float = 12.0,
    forenoon: bool = True,
    staff_length: float = 3438.0,
) -> str:
    """
    Time of day from an instrument reading (Ch.13 v.20-24): the gnomon
    shadow (nara), the altitude on a wheel (cakra) or arc (dhanus), or the
    chord measured with the staff (yashti).
    """
    try:
        from suryasiddhanta import ch13_instruments as ch13
        from suryasiddhanta.ch01_mean_motions import julian_day

        jd = julian_day(int(year), int(month), float(day))
        found = ch13.instrument_time(
            instrument, float(value), jd, float(latitude), forenoon=bool(forenoon),
            gnomon=float(gnomon), staff_length=float(staff_length),
        )
        data = found.to_dict()
        entry = ch13.get_instrument(found.instrument)
        data["instrument_name"] = f"{entry['name']} ({entry['iast']})"
        data["latitude"] = float(latitude)
        data["date"] = f"{year}-{int(month):02d}-{int(day):02d}"
        if found.forenoon:
            when = f"{found.ghatis_since_sunrise:.3f} ghatis since sunrise"
        else:
            when = (f"{found.ghatis_to_sunset:.3f} ghatis until sunset "
                    f"({found.ghatis_since_sunrise:.3f} after sunrise)")
        data["summary"] = (
            f"{entry['name']} reading {found.reading} ({found.reading_unit}): the Sun "
            f"stands {found.sun_altitude_deg:.2f}° high, {when}; the half-day is "
            f"{found.half_day_ghatis:.3f} ghatis. Method from the "
            f"{'text' if found.source == 'verse' else 'commentary'} ({found.verse})."
        )
        return json.dumps(data, indent=2)
    except KeyError as e:
        return json.dumps({"error": str(e).strip("'\""), "instrument": instrument})
    except Exception as e:
        return json.dumps({"error": str(e), "instrument": instrument})


def get_instruments(section: Optional[str] = None) -> str:
    """Report the descriptive catalog of Ch.13 -- the sphere and the instruments."""
    try:
        from suryasiddhanta import ch13_instruments as ch13

        catalog = ch13.load_catalog()
        sections = ("instruments", "sphere_components", "sphere_points",
                    "fixed_stars", "seven_sages", "clepsydra_vessel")
        if section:
            key = str(section).lower()
            if key not in sections:
                return json.dumps({
                    "error": f"Unknown section {section!r}", "known": list(sections),
                })
            return json.dumps({"section": key, "source": catalog["source"],
                               key: catalog[key]}, indent=2)
        return json.dumps({
            "chapter": catalog["chapter"],
            "chapter_name_en": catalog["chapter_name_en"],
            "chapter_name_iast": catalog["chapter_name_iast"],
            "source": catalog["source"],
            "note": catalog["note"],
            "missing_verses_note": catalog["missing_verses_note"],
            **{key: catalog[key] for key in sections},
            "summary": (
                "Chapter 13 builds an illustrative armillary sphere about a wooden "
                "earth (SS xiii.1-16), sets it turning with water or quicksilver "
                "(xiii.16-20), and names the instruments of time: gnomon, staff, "
                "arc, wheel, the sinking copper bowl, the man-instrument, peacock, "
                "monkey and sand-vessels (xiii.20-24). Only the sphere, the bowl "
                "and the gnomon are the text's own; the staff, wheel and arc are "
                "explained in the commentary."
            ),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "section": section})


def get_constant(constant_name: str) -> str:
    """Look up a Surya Siddhanta constant."""
    try:
        from suryasiddhanta.ch01_mean_motions import (
            MAHAYUGA, KALI_EPOCH_JD, CIVIL_DAYS_PER_MAHAYUGA,
            BHAGANA, ALL_PLANETS, MEAN_DAILY_MOTION,
        )
        from suryasiddhanta.ch02_true_places import (
            R_SINE, OBLIQUITY_DEGREES, MANDA_EPICYCLE, SIGHRA_EPICYCLE,
            AYANAMSHA_AMPLITUDE, AYANAMSHA_PERIOD,
        )
        name = constant_name.lower()

        if "mahayuga" in name:
            return f"Mahayuga = {MAHAYUGA:,} years. One complete astronomical cycle."
        if "kalpa" in name:
            return f"Kalpa = {MAHAYUGA * 1000:,} years = 1000 Mahayugas (one Day of Brahma)."
        if "civil" in name or "days_mahayuga" in name:
            return f"Civil days per Mahayuga = {CIVIL_DAYS_PER_MAHAYUGA:,}."
        if "r_sine" in name or "radius" in name:
            return f"R (sine radius) = {R_SINE} arcminutes. Circumference ≈ 21,600' = 360°."
        if "obliquity" in name:
            return f"SS obliquity = {OBLIQUITY_DEGREES}° (modern ~23.44°)."
        if "kali" in name and "epoch" in name:
            return f"Kali epoch = JD {KALI_EPOCH_JD} = Feb 17/18, 3102 BCE (midnight, Lanka)."
        if "ayanamsha" in name:
            return (
                f"SS ayanamsha: oscillatory ±{AYANAMSHA_AMPLITUDE}° "
                f"over {AYANAMSHA_PERIOD} years. Zero at 499 CE."
            )
        if "daily" in name and "motion" in name:
            lines = ["Mean daily motion (°/day):"]
            for p, v in MEAN_DAILY_MOTION.items():
                lines.append(f"  {p}: {v:.6f}")
            return "\n".join(lines)

        for planet in ALL_PLANETS:
            if planet.lower() in name and "bhagana" in name:
                key = planet if planet in BHAGANA else f"{planet}_sighrocca"
                if key in BHAGANA:
                    return f"{planet} bhagana = {BHAGANA[key]:,} revolutions/Mahayuga."

        if "bhagana" in name:
            lines = ["Bhagana (revolutions per Mahayuga):"]
            for k, v in BHAGANA.items():
                lines.append(f"  {k}: {v:,}")
            return "\n".join(lines)

        if "manda" in name and "epicycle" in name:
            lines = ["Manda epicycle sizes (odd°/even°):"]
            for p, ep in MANDA_EPICYCLE.items():
                lines.append(f"  {p}: {ep.odd}/{ep.even}")
            return "\n".join(lines)

        if "sighra" in name and "epicycle" in name:
            lines = ["Sighra epicycle sizes (odd°/even°):"]
            for p, ep in SIGHRA_EPICYCLE.items():
                lines.append(f"  {p}: {ep.odd}/{ep.even}")
            return "\n".join(lines)

        return (
            f"Constant '{constant_name}' not found. "
            "Try: mahayuga, kalpa, r_sine, obliquity, kali_epoch, "
            "ayanamsha, bhagana, daily_motion, manda_epicycle, sighra_epicycle"
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


def explain_algorithm(algorithm_name: str) -> str:
    """Return step-by-step explanation of a Surya Siddhanta algorithm."""
    explanations = {
        "mean_motion": """## Mean Motion (SS Ch.1 v.29-56)
**Step 1: Ahargana** — days since Kali epoch (JD 588465.5, Feb 17/18 3102 BCE).
**Step 2: Bhagana** — sidereal revolutions per Mahayuga (4,320,000 years).
**Step 3:** mean_lon = (bhagana × ahargana / 1,577,917,828) × 360° mod 360°.""",

        "manda": """## Manda Correction (SS Ch.2 v.28-43)
Accounts for orbital eccentricity (like Kepler's equation).
**Step 1:** kendra = mean_lon − mandocca (apogee longitude).
**Step 2:** Reduce to bhuja (0-90°), note quadrant sign.
**Step 3:** Interpolate pulsating epicycle between odd/even quadrant sizes.
**Step 4:** bhuja_phala = sin(bhuja) × epicycle / 360.
**Step 5:** manda_phala = arcsin(bhuja_phala). Apply sign.
**Step 6:** manda_sphuta = mean_lon + manda_phala.""",

        "sighra": """## Sighra Correction (SS Ch.2 v.43-60)
Accounts for synodic motion (produces retrograde).
Four-step pipeline:
1. Half manda → manda_sphuta1
2. sighra_kendra = sighrocca − manda_sphuta1, half sighra
3. Full manda on (mean + half_sighra)
4. Full sighra → true longitude
H = √[(R + r·cos K)² + (r·sin K)²], correction = arcsin(r·sin K / H).""",

        "ayanamsha": """## Ayanamsha (SS Ch.3 v.9-12)
Oscillatory trepidation (NOT continuous precession):
ayanamsha = 27° × sin(years_from_zero × 360° / 7200)
Zero at 499 CE. Max ±27°. Average rate ~54"/year (modern ~50.3").""",

        "panchanga": """## Panchanga — Five Elements
1. **Tithi** = floor((Moon − Sun) / 12°) + 1 [1-30]
2. **Vara** = ahargana mod 7 [weekday from Kali=Friday]
3. **Nakshatra** = floor(Moon_lon / 13°20') + 1 [1-27]
4. **Yoga** = floor((Sun + Moon) / 13°20') + 1 [1-27]
5. **Karana** = floor((Moon − Sun) / 6°) + 1 [half-tithi]
Plus: Masa (Sun's rashi), Ritu (season), Samvatsara (60-year cycle).""",

        "sine_table": """## Sine Table / Jya (SS Ch.2 v.17-22)
24 entries of R·sin(θ), R=3438 arcminutes, step=3°45'.
R=3438 chosen so circumference ≈ 21,600' = 360°.
Difference method: Δ[n+1] = Δ[n] − jya[n]/225
sin(30°) = 1719/3438 = 0.5000 exactly. Max error < 1.5'.""",

        "ahargana": """## Ahargana (SS Ch.1 v.48-51)
"Heap of days" from the Kali epoch: midnight Feb 17/18 3102 BCE = JD 588465.5.
Foundation of all mean longitude computations.

**The text's route**, whose input is a luni-solar date:
1. Elapsed years × 12 + elapsed months of the current year = solar months.
2. Add the intercalary months: solar months × 1,593,336 / 51,840,000 (v.48-49).
3. × 30, + elapsed tithis = lunar days.
4. Subtract the omitted lunar days: × 25,082,252 / 1,603,000,080 (v.50-51).

**This implementation's route**: ahargana = JD − 588465.5. The two agree
exactly — for Jan 1, 1860 both give 1,811,945 — because the intercalary
months are already implicit in a date expressed as a Julian Day. Use
compute_ahargana_verse_route to see the first route's working.

Note the era year (1989 CE is Kali 5090) is one more than the elapsed
count (5089.87): the elapsed count is of *completed* years.""",

        "eclipse_lunar": """## Lunar Eclipse (SS Ch.4)
1. Find full moon (Sun-Moon opposition).
2. Check Moon near Rahu/Ketu node (within ~12°).
3. Compute apparent diameters: Moon, Earth's shadow.
4. Moon latitude from node distance.
5. Magnitude = (shadow_radius + moon_radius − |latitude|) / moon_diameter.
6. Half-duration from relative motion.""",

        "eclipse_solar": """## Solar Eclipse (SS Ch.5)
1. Find new moon (Sun-Moon conjunction).
2. Check Moon near node.
3. Apply lambana (parallax in longitude) — observer-dependent.
4. Apply nati (parallax in latitude).
5. Topocentric correction shifts eclipse visibility by location.
6. Magnitude computed as for lunar but with Sun as eclipsed body.""",

        "eclipse_projection": """## Eclipse Projection (SS Ch.6)
1. **Ayana valana** — deflection from ecliptic obliquity (zero at solstices).
2. **Aksha valana** — deflection from observer latitude (SS Ch.4 v.24).
3. Total valana = ayana + aksha.
4. Contact position angles on eclipsed disc.
5. Project Moon's path as (x,y) chord through eclipsed body.""",

        "conjunction": """## Conjunctions (SS Ch.7)
1. Scan planet longitudes over time for same-longitude crossings.
2. Bisection refinement to find exact JD.
3. Classification: yuddha (<1°), samagama (<5°), samāgama (>5°).
4. YOGATARA catalog — 27 junction stars for planet-star conjunctions.""",

        "heliacal": """## Heliacal Risings & Settings (SS Ch.9)
Visibility thresholds (sun elongation):
Mars 17°, Mercury 14/12°, Jupiter 11°, Venus 10/8°, Saturn 15°.
Heliacal rising = first visibility after conjunction with Sun.
Heliacal setting = last visibility before conjunction.
Scan daily, bisect to find exact transition day.""",

        "lunar_horns": """## Lunar Horns (SS Ch.10)
1. Moon elongation from Sun → illuminated fraction.
2. Crescent width proportional to elongation.
3. Bright limb angle = direction of Sun relative to Moon.
4. Horn angle includes observer latitude correction (parallactic angle).
5. Moonrise/moonset from hour angle computation.""",
    }

    name = algorithm_name.lower().replace(" ", "_").replace("-", "_")
    for key in explanations:
        if key in name or name in key:
            return explanations[key]

    return (
        f"Algorithm '{algorithm_name}' not found. Available: "
        + ", ".join(explanations.keys())
    )


def list_nakshatras() -> str:
    """List all 27 nakshatras with basic info (Ch.8)."""
    try:
        from suryasiddhanta.ch08_stars import NAKSHATRA_DATA
        result = []
        for nak in NAKSHATRA_DATA:
            result.append({
                "number": nak.number,
                "name": nak.name,
                "devanagari": nak.devanagari,
                "star": nak.star,
                "deity": nak.deity,
            })
        return json.dumps({"nakshatras": result, "count": len(result)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_yogataras() -> str:
    """List all 27 yogatara (junction stars) with coordinates from Ch.7 catalog."""
    try:
        from suryasiddhanta.ch07_conjunctions import YOGATARA
        result = []
        for name, (lon, lat) in YOGATARA.items():
            result.append({
                "name": name,
                "longitude": lon,
                "latitude": lat,
            })
        return json.dumps({"yogataras": result, "count": len(result)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Corpus (book text) tools ─────────────────────────────────────
# Wired to suryasiddhanta.corpus.retrieve -- the model must call these
# before quoting or citing verse text; it must never recall verse text
# from memory (see retrieve.py's module docstring for why).

def get_verse(chapter: int, verse: int) -> str:
    """Return one verse (translation + commentary) by chapter and number."""
    try:
        from suryasiddhanta.corpus.retrieve import get_verse as _get_verse
        result = _get_verse(chapter, verse)
        if result is None:
            return json.dumps({"error": f"No verse found at {chapter}.{verse}"})
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_verses(chapter: int, start: Optional[int] = None, end: Optional[int] = None) -> str:
    """Return a chapter, or a verse range within it."""
    try:
        from suryasiddhanta.corpus.retrieve import get_verses as _get_verses
        result = _get_verses(chapter, start, end)
        return json.dumps({"verses": result, "count": len(result)}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def search_corpus(query: str, limit: int = 8, include_commentary: bool = True) -> str:
    """Full-text search across verse text, commentary and topic labels.

    Call this before quoting book text or answering "what does the text say" --
    never recall verse text from memory."""
    try:
        from suryasiddhanta.corpus.retrieve import search as _search
        result = _search(query, limit, include_commentary)
        return json.dumps({"results": result, "count": len(result)}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def chapter_index() -> str:
    """List all chapters with verse counts and topic labels."""
    try:
        from suryasiddhanta.corpus.retrieve import chapter_index as _chapter_index
        return json.dumps({"chapters": _chapter_index()}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def tools_for_query(query: str, limit: int = 5, top_n: int = 4) -> str:
    """Which calculation tools the relevant verses point to for a question.

    Call this before answering a computational question, so the answer can
    cite the verse that authorises the method instead of inventing one."""
    try:
        from suryasiddhanta.corpus.retrieve import tools_for_query as _tools_for_query
        return json.dumps({"tools": _tools_for_query(query, limit, top_n)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Tool schema definitions for the LLM API ──────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "compute_planet_position",
        "description": (
            "Compute a planet's sidereal longitude using Surya Siddhanta algorithms (Ch.1-2). "
            "Returns nakshatra, rashi, mean longitude, and all correction values. "
            "Use for: 'Where was Mars on 628 CE?', 'What nakshatra was Jupiter in?'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "planet": {"type": "string", "description": "Planet: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn"},
                "year": {"type": "integer", "description": "CE year (negative = BCE, e.g. -500 for 500 BCE)"},
                "month": {"type": "integer", "description": "Month 1-12", "default": 1},
                "day": {"type": "number", "description": "Day 1-31 (fractional for sub-day)", "default": 1},
            },
            "required": ["planet", "year"],
        },
    },
    {
        "name": "compute_all_planets",
        "description": "Get all 7 classical planet positions at once for a date (Ch.1-2).",
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
            },
            "required": ["year"],
        },
    },
    {
        "name": "compute_panchanga",
        "description": (
            "Compute the Panchanga (tithi, vara, nakshatra, yoga, karana, masa, ritu, samvatsara) "
            "for a given date. Use for any Hindu calendar / almanac questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
            },
            "required": ["year"],
        },
    },
    {
        "name": "compute_ahargana",
        "description": (
            "Compute ahargana (day count from Kali Yuga epoch), Julian Day, the Kali "
            "era year, the elapsed Kali years and the weekday for a date (Ch.1). The "
            "era year is the one an almanac prints (1989 CE is Kali 5090); kali_years "
            "is the elapsed count, one less. Always call this rather than converting "
            "an era by hand."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
            },
            "required": ["year"],
        },
    },
    {
        "name": "compute_ahargana_verse_route",
        "description": (
            "Compute the ahargana the way the text itself does (SS i.48-51): elapsed "
            "years to solar months, add the intercalary months (adhimasa), reduce to "
            "lunar days, subtract the omitted ones (tithikshaya). Returns every "
            "intermediate, so the working can be shown. Input is elapsed years, "
            "luni-solar months of the current year and tithis of the current month, "
            "reckoned from the Kali epoch unless from_creation is set."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "years": {"type": "integer"},
                "months": {"type": "integer", "default": 0},
                "tithis": {"type": "integer", "default": 0},
                "from_creation": {"type": "boolean", "default": False},
            },
            "required": ["years"],
        },
    },
    {
        "name": "compute_ayanamsha",
        "description": (
            "Compute SS ayanamsha (sidereal-tropical offset) for a date (Ch.2). "
            "Oscillatory model: ±27° over 7200 years, zero at 499 CE."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
            },
            "required": ["year"],
        },
    },
    {
        "name": "compute_sine_table",
        "description": (
            "Return the SS 24-entry jya (sine) table with R=3438 and accuracy report (Ch.2). "
            "No parameters needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "compute_day_length",
        "description": (
            "Compute day/night length in ghatis and hours, plus declination "
            "and sunrise hour angle for a date and latitude (Ch.3)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number"},
                "latitude": {"type": "number", "description": "Observer latitude in degrees"},
            },
            "required": ["year", "month", "day", "latitude"],
        },
    },
    {
        "name": "compute_lagna",
        "description": (
            "Compute the ascendant (lagna/rising sign) for a date/time and location (Ch.3). "
            "Use for birth chart / kundali questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number", "description": "Day with fractional time (e.g. 15.75 = 15th at 18:00)"},
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
            "required": ["year", "month", "day", "latitude", "longitude"],
        },
    },
    {
        "name": "compute_gnomon_shadow",
        "description": (
            "Compute gnomon shadow length, sun altitude and azimuth for a date/time "
            "and location (Ch.3). Classical Indian timekeeping instrument."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number"},
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "gnomon_length": {"type": "number", "description": "Gnomon height (default 12 angulas)", "default": 12},
            },
            "required": ["year", "month", "day", "latitude", "longitude"],
        },
    },
    {
        "name": "compute_lunar_eclipse",
        "description": (
            "Predict a lunar eclipse using SS method (Ch.4). "
            "Returns type (partial/total/none), magnitude, half-duration. "
            "Use day ~15 (full moon) for best results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number", "default": 15},
            },
            "required": ["year", "month"],
        },
    },
    {
        "name": "compute_solar_eclipse",
        "description": (
            "Predict a solar eclipse using SS method (Ch.5). "
            "Provide latitude/longitude for topocentric (observer-specific) prediction. "
            "Use day ~1 (new moon) for best results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number", "default": 1},
                "latitude": {"type": "number", "description": "Observer latitude; omit with longitude for geocentric"},
                "longitude": {"type": "number", "description": "Observer longitude; omit with latitude for geocentric"},
            },
            "required": ["year", "month"],
        },
    },
    {
        "name": "compute_eclipse_diagram",
        "description": (
            "Generate eclipse projection diagram data (Ch.6): contact points, "
            "valana angles, Moon's path across eclipsed disc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "eclipse_type": {"type": "string", "enum": ["lunar", "solar"]},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number", "default": 15},
                "latitude": {"type": "number", "default": 23},
                "longitude": {"type": "number", "default": 82},
            },
            "required": ["eclipse_type", "year", "month"],
        },
    },
    {
        "name": "find_conjunctions",
        "description": (
            "Find conjunctions between two planets over a time period (Ch.7). "
            "Returns dates, longitudes, separations, and SS classification "
            "(yuddha <1°, samagama <5°)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "planet1": {"type": "string"},
                "planet2": {"type": "string"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "months": {"type": "integer", "description": "Search period in months", "default": 12},
            },
            "required": ["planet1", "planet2", "year"],
        },
    },
    {
        "name": "find_star_conjunction",
        "description": (
            "Find conjunctions of a planet with a yogatara (junction star) (Ch.7). "
            "Use for: 'When was Saturn near Rohini?'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "planet": {"type": "string"},
                "star_name": {"type": "string", "description": "Yogatara name (e.g. Rohini, Krittika, Revati)"},
                "year": {"type": "integer"},
                "months": {"type": "integer", "default": 12},
            },
            "required": ["planet", "star_name", "year"],
        },
    },
    {
        "name": "get_nakshatra_info",
        "description": (
            "Look up nakshatra details: yogatara coordinates, deity, gana, "
            "star name, span (Ch.8). Use for any nakshatra question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nakshatra_name": {"type": "string", "description": "Name or number (1-27)"},
            },
            "required": ["nakshatra_name"],
        },
    },
    {
        "name": "compute_star_position",
        "description": (
            "Compute a yogatara's sidereal/tropical/equatorial coordinates "
            "at a given epoch (Ch.8). Accounts for precession."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "star_name": {"type": "string"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
            },
            "required": ["star_name", "year"],
        },
    },
    {
        "name": "compute_star_rise_set",
        "description": "Compute rise/set times of a yogatara, detect circumpolar status (Ch.8).",
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "star_name": {"type": "string"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number"},
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
            "required": ["star_name", "year", "month", "day", "latitude", "longitude"],
        },
    },
    {
        "name": "compute_heliacal_rising",
        "description": (
            "Find next heliacal rising of a planet — first visibility after "
            "conjunction with Sun (Ch.9). SS visibility thresholds applied."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "planet": {"type": "string", "description": "Mars, Mercury, Jupiter, Venus, or Saturn"},
                "year": {"type": "integer"},
                "latitude": {"type": "number", "default": 23},
                "start_month": {"type": "integer", "default": 1},
            },
            "required": ["planet", "year"],
        },
    },
    {
        "name": "compute_heliacal_setting",
        "description": (
            "Find next heliacal setting — last visibility before conjunction "
            "with Sun (Ch.9)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "planet": {"type": "string"},
                "year": {"type": "integer"},
                "latitude": {"type": "number", "default": 23},
                "start_month": {"type": "integer", "default": 1},
            },
            "required": ["planet", "year"],
        },
    },
    {
        "name": "compute_visibility_events",
        "description": (
            "List all heliacal risings and settings of a planet over a period (Ch.9). "
            "Shows full visibility cycle."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "planet": {"type": "string"},
                "year": {"type": "integer"},
                "months": {"type": "integer", "default": 12},
            },
            "required": ["planet", "year"],
        },
    },
    {
        "name": "compute_moon_phase",
        "description": (
            "Compute lunar phase name, illumination %, crescent width, "
            "and bright limb angle for a date (Ch.10)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number", "default": 1},
            },
            "required": ["year", "month"],
        },
    },
    {
        "name": "compute_horn_angle",
        "description": (
            "Compute lunar horn (crescent tilt) angle from a specific location (Ch.10). "
            "Includes parallactic correction for observer latitude."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number"},
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
            "required": ["year", "month", "day", "latitude", "longitude"],
        },
    },
    {
        "name": "compute_moonrise_moonset",
        "description": "Compute moonrise and moonset times for a location (Ch.10).",
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number"},
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
            "required": ["year", "month", "day", "latitude", "longitude"],
        },
    },
    {
        "name": "find_patas",
        "description": (
            "List the patas — Vyatipata (tropical longitude sum 180°) and "
            "Vaidhrita (sum 360°) — falling in a date range (Ch.11). A pata is "
            "the moment the Sun's and Moon's declinations become equal in "
            "amount: same direction for Vyatipata, opposite for Vaidhrita. "
            "This is NOT the nitya-yoga also called Vyatipata that "
            "compute_panchanga reports; that one is a fixed 13°20′ span of the "
            "longitude sum with no declination condition."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
                "days": {"type": "integer", "default": 60},
            },
            "required": ["year"],
        },
    },
    {
        "name": "compute_pata_details",
        "description": (
            "Report whether a pata is in progress at a given moment and when "
            "the next one falls, with the Sun's and Moon's declinations (Ch.11)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
                "day": {"type": "number"},
                "hour": {"type": "number", "default": 0},
            },
            "required": ["year", "month", "day"],
        },
    },
    {
        "name": "get_earth_dimensions",
        "description": (
            "The size of the earth and how the sky behaves at a place (Ch.12). "
            "Gives the diameter of 1600 yojanas and the circumference of "
            "1600·√10 = 5059.644 (SS i.59), the corrected circumference on the "
            "place's own parallel (i.60), the desantara — difference of "
            "longitude in yojanas and the arcminutes it adds to or subtracts "
            "from a mean place (i.61) — whether the sphere there is right, "
            "oblique or parallel, and the parallels of SS xii.60-68 where the "
            "day first reaches sixty nadis, where the Sun is lost for whole "
            "signs, and where he passes overhead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "default": 0},
                "longitude": {"type": "number", "default": 0},
            },
            "required": [],
        },
    },
    {
        "name": "get_planetary_orbits",
        "description": (
            "The orbits (kakshya) of the planets in yojanas, their diameters, "
            "their distances from the earth, and their daily motion (Ch.12 "
            "v.80-90). The Surya Siddhanta assumes every planet covers the "
            "same 11,858.717 yojanas a day, so orbit size is proportional to "
            "period; only the Moon's 324,000 yojanas is a real measurement. "
            "Each entry carries both the derived orbit and the figure the text "
            "states in v.85-89. Omit `body` for the whole table."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "body": {
                    "type": "string",
                    "description": (
                        "Moon, Mercury, Venus, Sun, Mars, Jupiter, Saturn, "
                        "Mercury_sighrocca, Venus_sighrocca, Moon_apogee, "
                        "Moon_node or Asterisms."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_cosmic_time",
        "description": (
            "The days of the different orders of beings and the planetary "
            "regents of the divisions of time (Ch.12 v.74, 78-79). Gods and "
            "demons at the poles have a day of six months, the Fathers in the "
            "moon a day of a lunar month, Brahma a day of an Aeon. Also gives "
            "the planet ruling the given day, its solar month and its solar "
            "year, the twenty-four hora lords, and how far Brahma's present "
            "day has run."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
            },
            "required": ["year"],
        },
    },
    {
        "name": "get_cosmology",
        "description": (
            "The descriptive cosmology of Ch.12: Maya's nine inquiries "
            "(v.1-9), the creation sequence from the waters to the animate "
            "world (v.13-28), the five elements and the planets said to arise "
            "from them (v.23-24), the seven patalas (v.33), Meru, Vadavamukha "
            "and the four equatorial cities (v.34-44), and the order of the "
            "spheres outward from the earth (v.29-31). Note the Surya "
            "Siddhanta leaves the patalas unnamed and has no table of upper "
            "lokas — do not supply Puranic names for either. Optionally narrow "
            "to one section."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": (
                        "inquiries, creation_sequence, elements, "
                        "planet_origins, patalas, reference_places, "
                        "orbital_order, regents or day_and_night."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_armillary_sphere",
        "description": (
            "The armillary sphere (gola-yantra) of Ch.13 v.3-16 set up for a "
            "place and moment: its hoops (equator, colures, ecliptic, horizon, "
            "the Sun's six diurnal hoops at the sign boundaries, and hoops for "
            "the 28 junction stars and 7 other fixed stars) with declination "
            "and day-radius; the sign divisions, equinoxes and solstices; the "
            "orient, occident and meridian ecliptic-points (lagna, asta-lagna, "
            "madhya-lagna); the Sun; and the sines carajya, kujya and antya. "
            "`hour` is clock time in `utc_offset` (default IST)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "utc_offset": {"type": "number", "default": 5.5, "description": "Zone of the clock time in hours from UTC (5.5 = IST, 0 = UT); event times come back in the same zone"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
                "hour": {"type": "number", "default": 12,
                         "description": "Clock hour 0-24 in utc_offset."},
                "latitude": {"type": "number", "default": 23.18},
                "longitude": {"type": "number", "default": 75.78},
                "include_stars": {"type": "boolean", "default": True},
                "include_geometry": {
                    "type": "boolean", "default": False,
                    "description": "Add 3D normals and vectors (large; for drawing).",
                },
            },
            "required": ["year"],
        },
    },
    {
        "name": "compute_clepsydra",
        "description": (
            "The water-clock of Ch.13 v.23 — a copper bowl sinking sixty times a "
            "day, one ghati (24 minutes) a sinking. Converts sinkings (plus a "
            "partial fill) to ghatis/palas/vipalas and clock time, converts "
            "ghatis to sinkings, gives the sinkings between sunrise and sunset "
            "for a date and latitude, and the drift of a bowl that sinks some "
            "other number of times a day. Supply any of sinkings, ghatis, year "
            "or observed_per_day."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sinkings": {"type": "integer"},
                "ghatis": {"type": "number"},
                "partial": {"type": "number", "default": 0,
                            "description": "Fill toward the next sinking, 0 to <1."},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
                "latitude": {"type": "number", "default": 23.18},
                "observed_per_day": {"type": "number"},
            },
            "required": [],
        },
    },
    {
        "name": "compute_instrument_time",
        "description": (
            "Time of day from a Ch.13 instrument reading (v.20-24). nara: the "
            "gnomon's shadow (value = shadow, gnomon default 12 digits; the "
            "text's own method). cakra / dhanus: the Sun's altitude read on a "
            "wheel or arc (value = degrees; commentary). yashti: the chord from "
            "the tip of a sun-pointed staff to the sunrise point, or sunset "
            "point after noon (value = chord, staff default R = 3438; "
            "commentary). Returns ghatis since sunrise and until sunset."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "instrument": {"type": "string",
                               "enum": ["nara", "cakra", "dhanus", "yashti"]},
                "value": {"type": "number"},
                "year": {"type": "integer"},
                "month": {"type": "integer", "default": 1},
                "day": {"type": "number", "default": 1},
                "latitude": {"type": "number", "default": 23.18},
                "gnomon": {"type": "number", "default": 12},
                "forenoon": {"type": "boolean", "default": True},
                "staff_length": {"type": "number", "default": 3438},
            },
            "required": ["instrument", "value", "year"],
        },
    },
    {
        "name": "get_instruments",
        "description": (
            "The descriptive catalog of Ch.13: the eleven instruments (sphere, "
            "self-revolving mercury sphere, gnomon, staff, arc, wheel, clepsydra, "
            "man-instrument, peacock, monkey, sand-vessels) with verse and "
            "whether the method is text or commentary; the parts of the sphere; "
            "the definitions of lagna, asta-lagna, madhya-lagna, antya and "
            "carajya with Burgess's corrections; the seven fixed stars of "
            "viii.10-12, 20-21; the Seven Sages; and the clepsydra vessel. "
            "Optionally narrow to one section."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": (
                        "instruments, sphere_components, sphere_points, "
                        "fixed_stars, seven_sages or clepsydra_vessel."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_constant",
        "description": (
            "Look up SS constants: mahayuga, kalpa, bhagana, r_sine, obliquity, "
            "kali_epoch, ayanamsha, daily_motion, manda_epicycle, sighra_epicycle."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "constant_name": {"type": "string"},
            },
            "required": ["constant_name"],
        },
    },
    {
        "name": "explain_algorithm",
        "description": (
            "Get step-by-step explanation of an SS algorithm. Available: "
            "mean_motion, manda, sighra, ayanamsha, panchanga, sine_table, "
            "ahargana, eclipse_lunar, eclipse_solar, eclipse_projection, "
            "conjunction, heliacal, lunar_horns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "algorithm_name": {"type": "string"},
            },
            "required": ["algorithm_name"],
        },
    },
    {
        "name": "list_nakshatras",
        "description": "List all 27 nakshatras with name, star, and deity (Ch.8).",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_yogataras",
        "description": "List all 27 yogatara (junction stars) with ecliptic coordinates (Ch.7).",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_verse",
        "description": (
            "Return one verse (translation + commentary) of the Surya Siddhanta "
            "by chapter and verse number. Use this whenever the user names a "
            "specific verse -- never recall verse text from memory."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "chapter": {"type": "integer"},
                "verse": {"type": "integer"},
            },
            "required": ["chapter", "verse"],
        },
    },
    {
        "name": "get_verses",
        "description": "Return a whole chapter, or a verse range within it, of the Surya Siddhanta text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chapter": {"type": "integer"},
                "start": {"type": "integer", "description": "First verse number (optional)"},
                "end": {"type": "integer", "description": "Last verse number (optional)"},
            },
            "required": ["chapter"],
        },
    },
    {
        "name": "search_corpus",
        "description": (
            "Full-text search across the Surya Siddhanta translation, commentary and "
            "topic labels. Call this before quoting book text or answering 'what "
            "does the text say' -- never recall verse text from memory."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 8},
                "include_commentary": {
                    "type": "boolean", "default": True,
                    "description": "Set false to restrict to scripture only, not editorial commentary.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "chapter_index",
        "description": "List all 14 chapters with verse counts and topic labels -- use to ground 'what does the Surya Siddhanta cover?' without dumping the whole corpus.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "tools_for_query",
        "description": (
            "Given a question, return which calculation tools the relevant verses "
            "point to. Call this before answering a computational question, so the "
            "answer cites the verse that authorises the method."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
                "top_n": {"type": "integer", "default": 4},
            },
            "required": ["query"],
        },
    },
]


# ── Tool dispatcher ─────────────────────────────────────────────

TOOL_FUNCTIONS: Dict[str, Any] = {
    "compute_planet_position": compute_planet_position,
    "compute_all_planets": compute_all_planets,
    "compute_panchanga": compute_panchanga,
    "compute_ahargana": compute_ahargana,
    "compute_ahargana_verse_route": compute_ahargana_verse_route,
    "compute_ayanamsha": compute_ayanamsha,
    "compute_sine_table": compute_sine_table,
    "compute_day_length": compute_day_length,
    "compute_lagna": compute_lagna,
    "compute_gnomon_shadow": compute_gnomon_shadow,
    "compute_lunar_eclipse": compute_lunar_eclipse,
    "compute_solar_eclipse": compute_solar_eclipse,
    "compute_eclipse_diagram": compute_eclipse_diagram,
    "find_conjunctions": find_conjunctions,
    "find_star_conjunction": find_star_conjunction,
    "get_nakshatra_info": get_nakshatra_info,
    "compute_star_position": compute_star_position,
    "compute_star_rise_set": compute_star_rise_set,
    "compute_heliacal_rising": compute_heliacal_rising,
    "compute_heliacal_setting": compute_heliacal_setting,
    "compute_visibility_events": compute_visibility_events,
    "compute_moon_phase": compute_moon_phase,
    "compute_horn_angle": compute_horn_angle,
    "compute_moonrise_moonset": compute_moonrise_moonset,
    "find_patas": find_patas,
    "compute_pata_details": compute_pata_details,
    "get_earth_dimensions": get_earth_dimensions,
    "get_planetary_orbits": get_planetary_orbits,
    "get_cosmic_time": get_cosmic_time,
    "get_cosmology": get_cosmology,
    "get_armillary_sphere": get_armillary_sphere,
    "compute_clepsydra": compute_clepsydra,
    "compute_instrument_time": compute_instrument_time,
    "get_instruments": get_instruments,
    "get_constant": get_constant,
    "explain_algorithm": explain_algorithm,
    "list_nakshatras": list_nakshatras,
    "list_yogataras": list_yogataras,
    "get_verse": get_verse,
    "get_verses": get_verses,
    "search_corpus": search_corpus,
    "chapter_index": chapter_index,
    "tools_for_query": tools_for_query,
}


def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return result as string."""
    if tool_name not in TOOL_FUNCTIONS:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return TOOL_FUNCTIONS[tool_name](**tool_input)
    except Exception as e:
        return json.dumps({"error": str(e), "tool": tool_name, "input": tool_input})
