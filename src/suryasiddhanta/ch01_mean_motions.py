"""
ch01_mean_motions.py
====================
Chapter 1: Of the Mean Motions of the Planets.

Implements cosmological time cycles, the Kali epoch, ahargana computation,
Julian Day conversions, Vedic time units, and mean longitude formulas
for all seven classical planets plus Moon's apogee and node.

Reference: SS Ch.1 v.11-56; Burgess (1860) pp.1-38
"""

from __future__ import annotations
import math
from typing import Dict, Tuple

from ._types import VedicTime, MeanPositions


# =====================================================================
#  COSMOLOGICAL CYCLES  (SS Ch.1 v.15-22)
# =====================================================================

MAHAYUGA = 4_320_000
KALPA = 4_320_000_000
KALI_YUGA = 432_000
DVAPARA_YUGA = 864_000
TRETA_YUGA = 1_296_000
KRITA_YUGA = 1_728_000

CIVIL_DAYS_PER_MAHAYUGA = 1_577_917_828
SIDEREAL_DAYS_PER_MAHAYUGA = 1_582_237_828
LUNAR_MONTHS_PER_MAHAYUGA = 53_433_336

# A kalpa (Aeon) = 1000 mahayugas (SS Ch.1 v.40)
CIVIL_DAYS_PER_KALPA = CIVIL_DAYS_PER_MAHAYUGA * 1000

SIDEREAL_YEAR_DAYS = CIVIL_DAYS_PER_MAHAYUGA / MAHAYUGA  # 365.25868...

#  Quantities the ahargana process of v.48-51 works with. None of them is
#  an independent datum: the text gives the revolutions and the civil days,
#  and these follow. A solar month is a twelfth of a solar year, so the
#  excess of lunar months over solar months in an Age is the number of
#  intercalary months (adhimasa), and the excess of lunar days over civil
#  days is the number of omitted lunar days (tithikshaya).
#  Burgess, comm. under i.51, prints 1,593,336 and 25,082,252 for these
#  two; his third figure, "1,003,000,080" lunar days, is a misprint for
#  1,603,000,080.
SOLAR_MONTHS_PER_MAHAYUGA = MAHAYUGA * 12                                      # 51,840,000
ADHIMASA_PER_MAHAYUGA = LUNAR_MONTHS_PER_MAHAYUGA - SOLAR_MONTHS_PER_MAHAYUGA  # 1,593,336
LUNAR_DAYS_PER_MAHAYUGA = LUNAR_MONTHS_PER_MAHAYUGA * 30                       # 1,603,000,080
TITHIKSHAYA_PER_MAHAYUGA = LUNAR_DAYS_PER_MAHAYUGA - CIVIL_DAYS_PER_MAHAYUGA   # 25,082,252


# =====================================================================
#  EPOCH — Kali Yuga start (SS Ch.1 v.23, v.57)
#  Midnight (LMT Lanka) between Feb 17-18, 3102 BCE = JD 588465.5
# =====================================================================

KALI_EPOCH_JD = 588465.5
KALI_EPOCH_YEAR = -3101
KALI_EPOCH_MONTH = 2
KALI_EPOCH_DAY = 18

#  Prime meridian (SS i.62): the line through Lanka and Avanti (Ujjain).
#  Burgess, under i.62, takes Ujjain at 75 deg 47' E (Thornton); 75.78 is the
#  value every UI and API route uses as its default longitude, so the
#  default place sits exactly on the meridian. Longitudes elsewhere in the
#  library stay east-positive from Greenwich.
LANKA_MERIDIAN_LONGITUDE = 75.78

#  The library's time base. Every JD the library takes or returns is
#  reckoned in Ujjain mean time, as the text reckons its sum of days "at
#  midnight, on the meridian of Lanka" (i.50): KALI_EPOCH_JD above is that
#  midnight. Ujjain mean time runs ahead of Universal Time by the
#  meridian's longitude, 75.78 / 360 of a day (5h 03m). Convert at the
#  boundary with jd_to_ut / jd_from_ut, or from a civil clock in any zone
#  with jd_from_clock / clock_from_jd.
UJJAIN_UT_OFFSET_DAYS = LANKA_MERIDIAN_LONGITUDE / 360.0
#: UTC offset, in hours, of Ujjain mean time itself (+5.052 h).
UJJAIN_UTC_OFFSET_HOURS = LANKA_MERIDIAN_LONGITUDE / 15.0


# =====================================================================
#  PLANETARY REVOLUTION COUNTS per Mahayuga  (SS Ch.1 v.29-34)
#  Bhagana = sidereal revolutions in 4,320,000 years
# =====================================================================

BHAGANA: Dict[str, int] = {
    "Sun": 4_320_000,
    "Moon": 57_753_336,
    "Mars": 2_296_832,
    "Mercury_sighrocca": 17_937_060,
    "Jupiter": 364_220,
    "Venus_sighrocca": 7_022_376,
    "Saturn": 146_568,
    "Moon_apogee": 488_203,
    "Moon_node": 232_238,
}

# =====================================================================
#  APSIS AND NODE REVOLUTIONS per KALPA  (SS Ch.1 v.41-44)
#  "The revolutions of the sun's apsis, moving eastward, in an Aeon
#   [kalpa = 4,320,000,000 years], are 387; ..."
#  Note: these are per kalpa, NOT per mahayuga — 1000x slower than
#  the counts in BHAGANA. Only the Moon's apsis and node (above)
#  are reckoned per mahayuga (v.33).
# =====================================================================

MANDOCCA_REVOLUTIONS_KALPA: Dict[str, int] = {
    "Sun": 387,
    "Mars": 204,
    "Mercury": 368,
    "Jupiter": 900,
    "Venus": 535,
    "Saturn": 39,
}

# Node revolutions per kalpa, retrograde (SS Ch.1 v.43-44)
NODE_REVOLUTIONS_KALPA: Dict[str, int] = {
    "Mars": 214,
    "Mercury": 488,
    "Jupiter": 174,
    "Venus": 903,
    "Saturn": 662,
}


# =====================================================================
#  TIME UNIT CONVERSIONS
#
#  The SS's own table of sidereal time is short (v.11-12):
#      10 long syllables (gurvakshara) = 1 respiration (prana)  =    4 s
#       6 respirations                 = 1 vinadi               =   24 s
#      60 vinadis                      = 1 nadi (= ghatika)     = 1440 s
#      60 nadis                        = 1 sidereal day
#  Burgess notes under v.11 that the SS "refrains from giving the
#  imaginary subdivisions of the respiration" — truti, tatpara,
#  nimesha and kashtha below are Bhaskara's (Siddhanta-Shiromani
#  i.19-20) and the Puranas', not this text's, and are kept only
#  because the UIs display them. They are listed separately so the
#  two sources are not presented as one table.
# =====================================================================

#: Units defined by the Surya Siddhanta itself (v.11-13).
TIME_UNITS_SS_SEC = {
    "prana": 4.0,
    "vinadi": 24.0,
    "nadi": 24 * 60,
    "ghati": 24 * 60,           # ghatika, the text's alternate name for nadi
    "ahoratra": 86400,
    "paksha": 15 * 86400,
    "masa": 30 * 86400,
    "ritu": 2 * 30 * 86400,
    "ayana": 6 * 30 * 86400,
    # The SS's own sidereal year, derived from v.37: 1,577,917,828 civil
    # days / 4,320,000 years = 365.2587565 d.
    "samvatsara": SIDEREAL_YEAR_DAYS * 86400,
}

#: Units from Bhaskara's Siddhanta-Shiromani and the Puranas, NOT the SS.
#
#  These are derived downward from the nadi rather than upward from a
#  rounded truti, so that the chain closes on the text's own units:
#
#      100 truti   = 1 tatpara        30 kashtha = 1 kala
#       30 tatpara = 1 nimesha        30 kala    = 1 ghatika (= 1 nadi)
#       18 nimesha = 1 kashtha         2 ghatika = 1 muhurta
#
#  Taken the other way, from the once-used truti = 29.6e-6 s, thirty kalas
#  came to 1438.56 s against the nadi's 1440 -- a converter reading the two
#  tables together showed the chain failing to close by a second and a half.
#  The truti that follows from the nadi is 1/33750 s, which is the value the
#  Puranic reckoning intends.
_NADI_SEC = 24 * 60
_KALA_SEC = _NADI_SEC / 30          # 48 s
_KASHTHA_SEC = _KALA_SEC / 30       # 1.6 s
_NIMESHA_SEC = _KASHTHA_SEC / 18    # 0.0888... s

TIME_UNITS_NON_SS_SEC = {
    "truti": _NIMESHA_SEC / 3000,   # 1/33750 s
    "tatpara": _NIMESHA_SEC / 30,
    "nimesha": _NIMESHA_SEC,
    "kashtha": _KASHTHA_SEC,
    "kala": _KALA_SEC,
    "muhurta": 2 * _NADI_SEC,
    "prahara": 3 * 3600,
}

#: Combined lookup kept for backwards compatibility with the UIs.
TIME_UNITS_SEC = {**TIME_UNITS_NON_SS_SEC, **TIME_UNITS_SS_SEC}

GHATIS_PER_DAY = 60
# Burgess, note to v.11: the modern name for the vinadi is *pala*, but that
# term "nowhere occurs in our text". The field names below follow modern
# usage; the SS's own terms are vinadi (= pala) and prana.
PALAS_PER_GHATI = 60
VIPALAS_PER_PALA = 60


# =====================================================================
#  JULIAN DAY CONVERSIONS
# =====================================================================

def julian_day(year: int, month: int, day: float, gregorian: bool = None) -> float:
    """
    Convert calendar date to Julian Day Number.

    Auto-selects Julian calendar before Oct 15, 1582; Gregorian after.
    Override with gregorian=True/False.

    Args:
        year:      Year (negative = BCE, e.g. -3101 = 3102 BCE)
        month:     Month (1-12)
        day:       Day with optional fraction for time
        gregorian: Override calendar selection (None = auto)

    Returns:
        Julian Day Number as float
    """
    if gregorian is None:
        if year < 1582 or (year == 1582 and (month < 10 or (month == 10 and day < 15))):
            gregorian = False
        else:
            gregorian = True

    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12

    if gregorian:
        A = int(y / 100)
        B = 2 - A + int(A / 4)
    else:
        B = 0

    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + day + B - 1524.5


def from_julian_day(jd: float) -> Tuple[int, int, int, float]:
    """
    Convert Julian Day Number to calendar date.

    Returns:
        (year, month, day, fraction_of_day)
    """
    jd = jd + 0.5
    Z = int(jd)
    F = jd - Z

    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)

    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E)
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715

    return year, month, day, F


def jd_to_ut(jd: float) -> float:
    """A library JD (Ujjain mean time) as a JD in Universal Time."""
    return jd - UJJAIN_UT_OFFSET_DAYS


def jd_from_ut(jd_ut: float) -> float:
    """A JD in Universal Time as a library JD (Ujjain mean time)."""
    return jd_ut + UJJAIN_UT_OFFSET_DAYS


def jd_from_clock(year: int, month: int, day: float, hour: float = 0.0,
                  utc_offset_hours: float = UJJAIN_UTC_OFFSET_HOURS,
                  gregorian: bool = None) -> float:
    """
    Library JD (Ujjain mean time) for a civil date and clock time.

    Args:
        year, month, day: Civil date; ``day`` may carry a fraction for the
            time of day, which adds to ``hour``.
        hour:             Clock hour in the given zone.
        utc_offset_hours: The zone's offset from UTC in hours (5.5 for
            IST). The default is Ujjain mean time itself, so a bare date
            is midnight on the Lanka meridian, as the text reckons it.
        gregorian:        As for :func:`julian_day`.
    """
    jd_civil = julian_day(year, month, day, gregorian) + hour / 24.0
    return jd_from_ut(jd_civil - utc_offset_hours / 24.0)


def clock_from_jd(jd: float, utc_offset_hours: float = UJJAIN_UTC_OFFSET_HOURS
                  ) -> Tuple[int, int, int, float]:
    """
    Civil date and clock hour, in the given zone, of a library JD.

    The inverse of :func:`jd_from_clock`. Returns ``(year, month, day,
    hour)`` with ``hour`` in [0, 24).
    """
    y, m, d, frac = from_julian_day(jd_to_ut(jd) + utc_offset_hours / 24.0)
    return y, m, d, frac * 24.0


# =====================================================================
#  AHARGANA (elapsed civil days from Kali epoch)
# =====================================================================

def ahargana(jd: float) -> float:
    """
    Compute ahargana: civil days elapsed since Kali epoch.

    Kali epoch = midnight (LMT, Lanka meridian)
    Feb 17-18, 3102 BCE = JD 588465.5

    ``jd`` is a library JD, in Ujjain mean time (see
    UJJAIN_UT_OFFSET_DAYS); a whole-and-a-half JD is a midnight at Ujjain.

    The text's own procedure (v.48-51) reaches the same count by a
    different route — reduce elapsed years to solar months, add the
    intercalary months (adhimasa), reduce to days, subtract the omitted
    lunar days (tithikshaya). That route exists because its input is a
    luni-solar calendar date; this function's input is already a Julian
    Day, for which plain subtraction from the epoch is equivalent. The
    equivalence is exact, not approximate, and
    ``ahargana_from_luni_solar`` below implements the other route;
    ``test_verse_route_matches_jd_subtraction`` pins the two together on
    Burgess's worked example for Jan 1, 1860.

    Reference: SS Ch.1 v.48-51
    """
    return jd - KALI_EPOCH_JD


def jd_from_ahargana(a: float) -> float:
    """Convert ahargana back to Julian Day Number."""
    return a + KALI_EPOCH_JD


def adhimasa_elapsed(solar_months: int) -> int:
    """
    Number of intercalary months (adhimasa) contained in a count of
    elapsed solar months.

    SS i.48-49 states it as a proportion: as the solar months of an Age
    are to its intercalary months, so are the solar months elapsed to
    the intercalary months elapsed. The fractional remainder is
    discarded — it is the part of an adhimasa not yet complete.

    Reference: SS Ch.1 v.48-49
    """
    return solar_months * ADHIMASA_PER_MAHAYUGA // SOLAR_MONTHS_PER_MAHAYUGA


def tithikshaya_elapsed(lunar_days: int) -> int:
    """
    Number of omitted lunar days (tithikshaya) contained in a count of
    elapsed lunar days.

    The companion proportion to :func:`adhimasa_elapsed`: as the lunar
    days of an Age are to its omitted lunar days, so are the lunar days
    elapsed to the omitted lunar days elapsed. A tithi is shorter than a
    civil day, so tithis are dropped to keep the two reckonings together.

    Reference: SS Ch.1 v.50-51
    """
    return lunar_days * TITHIKSHAYA_PER_MAHAYUGA // LUNAR_DAYS_PER_MAHAYUGA


def ahargana_from_luni_solar(
    years: int,
    months: int = 0,
    tithis: int = 0,
    *,
    from_creation: bool = False,
) -> int:
    """
    Ahargana by the text's own route, from a luni-solar date.

    The chain of v.48-51: elapsed years to solar months, add the
    intercalary months, multiply by 30 for lunar days, subtract the
    omitted lunar days.

    The three inputs are not quite what their names suggest, so to be
    explicit — they are the triple Burgess writes as "1,955,884,960 y.,
    9 m., 7 d." for Jan 1, 1860:

    * ``years``   — complete elapsed years.
    * ``months``  — complete *luni-solar* months of the current year
      elapsed (Chaitradi). They enter the solar-month total, which is
      the method's own built-in approximation; the adhimasa proportion
      is what corrects it.
    * ``tithis``  — complete tithis of the current lunar month elapsed.

    ``from_creation`` sets the era the count is kept in, for both the
    input and the result. By default both are reckoned from the Kali
    epoch, so ``ahargana_from_luni_solar(4960, 9, 7)`` is that same
    Jan 1, 1860 and returns a number directly comparable with
    :func:`ahargana`. Set it to reckon from the end of creation instead,
    as the text does and as Burgess's example is written; the
    proportions themselves always run on the count from creation, since
    intercalary months accumulate from there (v.56 allows reckoning from
    a later epoch, which is what the default does by subtracting
    :data:`CIVIL_DAYS_CREATION_TO_KALI`).

    Reference: SS Ch.1 v.48-51, v.56
    """
    if not from_creation:
        years += YEARS_CREATION_TO_KALI
    solar_months = years * 12 + months
    lunar_months = solar_months + adhimasa_elapsed(solar_months)
    lunar_days = lunar_months * 30 + tithis
    civil_days = lunar_days - tithikshaya_elapsed(lunar_days)
    if from_creation:
        return civil_days
    return civil_days - CIVIL_DAYS_CREATION_TO_KALI


def kali_years_elapsed(jd: float) -> float:
    """Elapsed years (fractional) since Kali epoch using SS sidereal year."""
    return ahargana(jd) / SIDEREAL_YEAR_DAYS


def kali_era_year(jd: float) -> int:
    """
    The Kali year a date falls in, as an era number rather than an
    elapsed count: 5090 for a date in 1989 CE, where
    :func:`kali_years_elapsed` returns 5089.87.

    The year turns on the anniversary of the Kali epoch measured in SS
    sidereal years. That is not a fixed Gregorian date — the sidereal
    year is longer than the tropical one, so the anniversary walks
    forward through the civil calendar. It currently falls in April:
    this function places the 4961st year's start within about two days
    of Apr 12, 1859, the Mesha sankranti Burgess tabulates as the start
    of solar year 4961 (comm. under i.51).

    Reference: SS Ch.1 v.23, v.48-51
    """
    return int(kali_years_elapsed(jd)) + 1


# =====================================================================
#  YUGA POSITION
# =====================================================================

def yuga_elapsed_fraction(jd: float) -> float:
    """
    Fraction of a Mahayuga elapsed *since the Kali epoch*, not since the
    Mahayuga's own start: this returns 0.0 at the Kali epoch and 1.0 one
    full Mahayuga later.

    The Kali epoch itself stands at 0.9 of the current Mahayuga, since
    Krita + Treta + Dvapara = 1,728,000 + 1,296,000 + 864,000 = 3,888,000
    of its 4,320,000 years have run (SS Ch.1 v.15-17, v.23).
    """
    kali_years = kali_years_elapsed(jd)
    return (kali_years % MAHAYUGA) / MAHAYUGA


# =====================================================================
#  TIME FORMAT CONVERSIONS
# =====================================================================

def day_to_hms(day_fraction: float) -> Tuple[int, int, float]:
    """Convert fractional day to (hours, minutes, seconds)."""
    total_sec = day_fraction * 86400
    h = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = total_sec % 60
    return h, m, s


def ghati_to_minutes(gh: float) -> float:
    """1 ghati = 24 minutes."""
    return gh * 24.0


def minutes_to_ghati(minutes: float) -> float:
    """Convert minutes to ghatis."""
    return minutes / 24.0


# =====================================================================
#  MANDOCCA (APOGEE) LONGITUDES at Kali epoch
#
#  Derived from the SS system itself: the apsides had been moving at
#  their kalpa rates (v.41-42) for the astronomical time elapsed from
#  the end of creation to the Kali epoch, which is 1811 quarter-Ages
#  = 1,955,880,000 years (Burgess comm. under i.24 and i.29-34).
#  Position at Kali epoch = frac(revs * elapsed/kalpa) * 360.
#
#  These reproduce, to the arc-second, Burgess's table of positions at
#  the commencement of the Iron Age (comm. under i.44):
#  Sun 2s 17d 7' 48" = 77.13, Mercury 7s 10d 19' 12" = 220.32,
#  Venus 2s 19d 39' = 79.65, Mars 4s 9d 57' 36" = 129.96,
#  Jupiter 5s 21d = 171.0, Saturn 7s 26d 36' 36" = 236.61.
# =====================================================================

YEARS_CREATION_TO_KALI = 1811 * 1_080_000  # 1,955,880,000
_KALPA_FRAC_AT_KALI = YEARS_CREATION_TO_KALI / KALPA  # 0.45275

#  Civil days from the end of creation to the Kali epoch, by the v.48-51
#  route itself — 714,402,296,627. Whole years contain a whole number of
#  solar months and no part-tithi, so the route returns exactly
#  YEARS_CREATION_TO_KALI * SIDEREAL_YEAR_DAYS here. This is the offset
#  that puts ahargana_from_luni_solar on the same footing as ahargana().
CIVIL_DAYS_CREATION_TO_KALI = ahargana_from_luni_solar(
    YEARS_CREATION_TO_KALI, from_creation=True
)

MANDOCCA_AT_EPOCH: Dict[str, float] = {
    # Moon's apsis at Kali epoch = a quadrant in advance of the initial
    # point (SS Ch.1 v.57-58 with Burgess comm. under v.29-34)
    "Moon": 90.0,
    **{
        planet: (revs * _KALPA_FRAC_AT_KALI % 1.0) * 360.0
        for planet, revs in MANDOCCA_REVOLUTIONS_KALPA.items()
    },
}

# No SIGHROCCA_AT_EPOCH table is needed. SS Ch.1 v.57 puts every planet,
# the conjunctions (sighra) included, at the first of Aries at the end of
# the Golden Age, and both inner sighroccas complete a whole number of
# revolutions in the half-Mahayuga from there to the Kali epoch
# (17,937,060 / 2 = 8,968,530 and 7,022,376 / 2 = 3,511,188), so both
# stand at exactly 0 deg at the epoch. sighrocca_longitude() therefore
# applies no offset.

# Planet node longitudes at Kali epoch, derived like MANDOCCA_AT_EPOCH
# but retrograde (SS Ch.1 v.43-44). These match Burgess's Iron-Age table
# (comm. under i.44) to the arc-second: Mercury 20d 52' 48" = 20.88,
# Venus 2s 0d 1' 48" = 60.03, Mars 1s 10d 8' 24" = 40.14,
# Jupiter 2s 19d 44' 24" = 79.74, Saturn 3s 10d 37' 12" = 100.62.
NODE_AT_EPOCH: Dict[str, float] = {
    planet: (-revs * _KALPA_FRAC_AT_KALI) % 1.0 * 360.0
    for planet, revs in NODE_REVOLUTIONS_KALPA.items()
}


# =====================================================================
#  MEAN DAILY MOTIONS (derived from bhagana)
# =====================================================================

MEAN_DAILY_MOTION: Dict[str, float] = {
    body: bhagana * 360.0 / CIVIL_DAYS_PER_MAHAYUGA
    for body, bhagana in BHAGANA.items()
}

MEAN_DAILY_MOTION["Moon_node"] = -MEAN_DAILY_MOTION["Moon_node"]


# =====================================================================
#  MEAN LONGITUDE  (SS Ch.1 v.53-54)
# =====================================================================

ALL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def _normalize(degrees: float) -> float:
    """Normalize angle to [0, 360)."""
    return degrees % 360.0


def mean_longitude(planet: str, jd: float) -> float:
    """
    Compute mean sidereal longitude for a planet at given Julian Day.

    Formula (SS Ch.1 v.53-54):
        mean_lon = (bhagana * ahargana / civil_days_per_mahayuga) * 360 mod 360

    Mercury and Venus are the exception. The text assigns them no
    revolutions of their own — v.29 gives 4,320,000 for "the sun, Mercury
    and Venus" alike, and the 17,937,060 / 7,022,376 of v.31-32 belong to
    their *conjunctions* (sighra). Burgess, comm. under i.54: "to the
    Hindu apprehension, the mean place of those planets is the same with
    that of the sun." Their mean place is therefore the Sun's mean
    longitude; sighrocca_longitude() supplies the fast-moving element.

    Args:
        planet: "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                "Moon_apogee", or "Moon_node"
        jd:     Julian Day Number

    Returns:
        Mean sidereal longitude in degrees [0, 360)
    """
    VALID = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
             "Moon_apogee", "Moon_node"}
    if planet not in VALID:
        raise ValueError(f"Unknown planet '{planet}'. Valid: {sorted(VALID)}")

    if planet in ("Mercury", "Venus"):
        return mean_longitude("Sun", jd)

    a = ahargana(jd)
    bhagana_val = BHAGANA[planet]
    lon = (bhagana_val * a / CIVIL_DAYS_PER_MAHAYUGA) * 360.0

    # Epoch offsets and direction per SS Ch.1 v.57-58: at the Kali
    # epoch the moon's apsis stands at 90 deg and its node (retrograde)
    # at 180 deg; all other bodies start at 0 deg (first of Aries).
    if planet == "Moon_apogee":
        return _normalize(90.0 + lon)
    if planet == "Moon_node":
        return _normalize(180.0 - lon)
    return _normalize(lon)


def mandocca_longitude(planet: str, jd: float) -> float:
    """
    Current longitude of mandocca (apogee) for a planet.
    Apogee precesses slowly forward from its Kali epoch position.
    """
    if planet not in MANDOCCA_AT_EPOCH:
        raise ValueError(f"No mandocca data for '{planet}'")

    a = ahargana(jd)
    if planet == "Moon":
        # Moon's apsis: revolutions per mahayuga (SS Ch.1 v.33)
        daily_motion = BHAGANA["Moon_apogee"] * 360.0 / CIVIL_DAYS_PER_MAHAYUGA
    else:
        # Planet apsides: revolutions per kalpa (SS Ch.1 v.41-42)
        revs = MANDOCCA_REVOLUTIONS_KALPA.get(planet, 0)
        daily_motion = revs * 360.0 / CIVIL_DAYS_PER_KALPA

    epoch_pos = MANDOCCA_AT_EPOCH[planet]
    return _normalize(epoch_pos + daily_motion * a)


def sighrocca_longitude(planet: str, jd: float) -> float:
    """
    Compute sighrocca (sighra apogee) longitude.
    Outer planets (Mars, Jupiter, Saturn): sighrocca = Sun's mean longitude.
    Inner planets (Mercury, Venus): from their own sighra bhagana.
    """
    if planet in ("Mars", "Jupiter", "Saturn"):
        return mean_longitude("Sun", jd)
    elif planet in ("Mercury", "Venus"):
        a = ahargana(jd)
        key = f"{planet}_sighrocca"
        bhagana_val = BHAGANA[key]
        return _normalize(bhagana_val * a / CIVIL_DAYS_PER_MAHAYUGA * 360.0)
    else:
        raise ValueError(f"Sighrocca not defined for '{planet}'")


def planet_node_longitude(planet: str, jd: float) -> float:
    """
    Ascending node longitude for a star-planet (SS Ch.1 v.43-44).
    Nodes move retrograde, at revolutions-per-kalpa rates.
    """
    if planet not in NODE_REVOLUTIONS_KALPA:
        raise ValueError(f"No node data for '{planet}'")

    a = ahargana(jd)
    daily_motion = NODE_REVOLUTIONS_KALPA[planet] * 360.0 / CIVIL_DAYS_PER_KALPA
    return _normalize(NODE_AT_EPOCH[planet] - daily_motion * a)


def moon_node_longitude(jd: float) -> float:
    """
    Moon's ascending node (Rahu) longitude. Moves retrograde.
    At Kali epoch the node stands half a revolution in advance of
    the initial point, i.e. at 180 deg (SS Ch.1 v.57-58).
    """
    a = ahargana(jd)
    motion = BHAGANA["Moon_node"] * a / CIVIL_DAYS_PER_MAHAYUGA * 360.0
    return _normalize(180.0 - motion)


def compute_all_mean_positions(jd: float) -> MeanPositions:
    """Compute mean positions for all planets at once."""
    return MeanPositions(
        jd=jd,
        Sun=mean_longitude("Sun", jd),
        Moon=mean_longitude("Moon", jd),
        Mars=mean_longitude("Mars", jd),
        Mercury=mean_longitude("Mercury", jd),
        Jupiter=mean_longitude("Jupiter", jd),
        Venus=mean_longitude("Venus", jd),
        Saturn=mean_longitude("Saturn", jd),
        Moon_apogee=mandocca_longitude("Moon", jd),
        Moon_node=moon_node_longitude(jd),
    )


# =====================================================================
#  RASHI AND NAKSHATRA FROM LONGITUDE (basic lookup)
# =====================================================================

RASHIS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]


def rashi_from_longitude(lon: float) -> Tuple[int, str, float]:
    """Return (rashi_index, rashi_name, degrees_within_rashi)."""
    lon = _normalize(lon)
    idx = int(lon / 30.0)
    deg_in = lon - idx * 30.0
    return idx, RASHIS[idx], round(deg_in, 4)


def nakshatra_from_longitude(lon: float) -> Tuple[int, str, int, float]:
    """
    Return (nakshatra_index, nakshatra_name, pada, degrees_in_nakshatra).
    27 nakshatras of 13deg20' each.

    The index is 0-based, because callers use it to index the name and
    catalog lists. Panchanga.nakshatra["number"] is 1-based, like its
    tithi / yoga / karana siblings.
    """
    span = 360.0 / 27  # 13.333...
    lon = _normalize(lon)
    idx = int(lon / span)
    deg_in = lon - idx * span
    pada = int(deg_in / (span / 4)) + 1
    return idx, _NAKSHATRA_NAMES[idx], pada, round(deg_in, 4)


_NAKSHATRA_NAMES = [
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Svati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]


# =====================================================================
#  TITHI (LUNAR DAY)  (SS Ch.2 v.66; cf. Ch.14 v.12-13)
# =====================================================================

TITHI_NAMES = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]


def tithi_from_elongation(moon_lon: float, sun_lon: float) -> Tuple[int, float]:
    """
    Compute tithi from Moon and Sun longitudes.
    Each tithi = 12deg of elongation (Moon - Sun).

    Returns:
        (tithi_number 1-30, elapsed_fraction)
    """
    elongation = (moon_lon - sun_lon) % 360.0
    tithi_float = elongation / 12.0
    num = min(int(tithi_float), 29)
    frac = tithi_float - int(tithi_float)
    return num + 1, frac


# =====================================================================
#  VARA (WEEKDAY)
# =====================================================================

VARA_NAMES = ["Ravivara", "Somavara", "Mangalavara", "Budhavara",
              "Guruvara", "Shukravara", "Shanivara"]
VARA_NAMES_EN = ["Sunday", "Monday", "Tuesday", "Wednesday",
                 "Thursday", "Friday", "Saturday"]


def vara(jd: float) -> Tuple[int, str]:
    """
    Compute vara (weekday) from Julian Day Number.
    Returns: (vara_index_0based, vara_name_sanskrit). 0 = Sunday.
    """
    day_idx = int(jd + 1.5) % 7
    return day_idx, VARA_NAMES[day_idx]


# =====================================================================
#  MASA (LUNAR MONTH)
# =====================================================================

MASA_NAMES = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha",
    "Shravana", "Bhadrapada", "Ashvina", "Kartika",
    "Margashirsha", "Pausha", "Magha", "Phalguna",
]


def masa_from_sun_longitude(sun_lon: float) -> Tuple[int, str]:
    """
    Determine the *solar* month from the Sun's longitude.

    A solar month is the Sun's stay in one sign (SS Ch.1 v.13, Ch.14
    v.10). Burgess, comm. under xiv.16: "in practice Vaishakha is treated
    as the first of the solar months, and Caitra of the lunar" — so the
    Sun in Mesha is Vaishakha, and the list is offset by one sign.

    This is not the amanta lunar month a panchanga names, which depends
    on the new moon that opens it and is not computed here.

    Returns: (masa_index_0based, masa_name)
    """
    masa_idx = (int(sun_lon / 30) + 1) % 12
    return masa_idx, MASA_NAMES[masa_idx]


# =====================================================================
#  RITU (SEASON)
# =====================================================================

#  SS Ch.14 v.9-10: the seasons are reckoned from the Sun's entrance
#  into Capricorn, beginning with Shishira, "each prevailing through two
#  signs". Burgess's table under xiv.16 gives the correspondences:
#  Shishira = Magha + Phalguna (Sun in Makara + Kumbha, 270-330 deg),
#  Vasanta = Caitra + Vaishakha (Meena + Mesha, 330-30), and so on.
RITU_NAMES = ["Shishira", "Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta"]
RITU_NAMES_EN = ["Winter", "Spring", "Summer", "Monsoon", "Autumn", "Pre-Winter"]


def ritu_from_sun_longitude(sun_lon: float) -> Tuple[int, str]:
    """
    Return the season (ritu) from the Sun's longitude.

    Two signs each, counted from Capricorn with Shishira first
    (SS Ch.14 v.9-10), so index 0 = Shishira at Sun 270-330 deg.

    Returns: (ritu_index_0based, ritu_name)
    """
    ritu_idx = int(((sun_lon + 90.0) % 360.0) / 60.0)
    return ritu_idx, RITU_NAMES[ritu_idx]


# =====================================================================
#  SAMVATSARA (60-YEAR JUPITER CYCLE)
# =====================================================================

SAMVATSARA_NAMES = [
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati",
    "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatri",
    "Ishvara", "Bahudhanya", "Pramathi", "Vikrama", "Vrishapriya",
    "Chitrabhanu", "Svabhanu", "Tarana", "Parthiva", "Vyaya",
    "Sarvajit", "Sarvadhari", "Virodhi", "Vikruta", "Khara",
    "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi",
    "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava",
    "Shubhakrut", "Sobhakrut", "Krodhi", "Vishvavasu", "Parabhava",
    "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhikrut",
    "Paridhavi", "Pramadin", "Ananda", "Rakshasa", "Anala",
    "Pingala", "Kalayukta", "Siddharthi", "Raudra", "Durmati",
    "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya",
]


def samvatsara(jd: float) -> Tuple[int, str]:
    """
    Compute Jupiter samvatsara (60-year cycle name).

    SS Ch.1 v.55: "Multiply by twelve the past revolutions of
    Jupiter, add the signs of the current revolution, and divide
    by sixty; the remainder marks the year of Jupiter's cycle,
    counting from Vijaya." Vijaya is the 27th year of the cycle
    as popularly counted from Prabhava (Burgess comm.: the rule
    gives 1859-60 CE = Prajapati).

    Returns: (index_0based_from_Prabhava, name)
    """
    a = ahargana(jd)
    jupiter_revs = BHAGANA["Jupiter"] * a / CIVIL_DAYS_PER_MAHAYUGA
    jovian_years = int(jupiter_revs * 12.0)  # 12 x revs + signs of current
    idx = (jovian_years + SAMVATSARA_NAMES.index("Vijaya")) % 60
    return idx, SAMVATSARA_NAMES[idx]


# =====================================================================
#  YOGA (LUNI-SOLAR COMBINATION)  (SS Ch.2 v.65)
# =====================================================================

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]


def yoga_from_longitudes(sun_lon: float, moon_lon: float) -> Tuple[int, str]:
    """
    Compute yoga from Sun and Moon longitudes.
    yoga_index = floor((Sun + Moon) / 13°20') mod 27.
    Returns: (yoga_number 1-27, yoga_name)
    """
    combined = (sun_lon + moon_lon) % 360.0
    span = 800.0 / 60.0  # 13°20' = 13.3333...°
    idx = int(combined / span) % 27
    return idx + 1, YOGA_NAMES[idx]


# =====================================================================
#  KARANA (HALF-TITHI)  (SS Ch.2 v.67-69)
#
#  v.67: "The fixed (dhruva) karanas, namely Shakuni, Naga, Chatushpada
#  the third, and Kimstughna, are counted from the latter half of the
#  fourteenth day of the dark half-month" — i.e. 58, 59, 60, 1 in that
#  order, as Burgess's table under v.69 sets out. Note that modern
#  panchangas invert 59 and 60 (Chatushpada then Naga); this module
#  follows the text.
# =====================================================================

KARANA_NAMES_RECURRING = [
    "Bava", "Balava", "Kaulava", "Taitila",
    "Garaja", "Vanija", "Vishti",
]
KARANA_NAMES_FIXED = [
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
]


def karana_from_elongation(moon_lon: float, sun_lon: float) -> Tuple[int, str, str]:
    """
    Compute karana (half-tithi) from Moon-Sun elongation.
    60 karanas per synodic month. 4 fixed + 7 recurring × 8 = 56 + 4.
    Returns: (karana_number 1-60, karana_name, type 'fixed'|'recurring')
    """
    elongation = (moon_lon - sun_lon) % 360.0
    karana_num = int(elongation / 6.0) + 1
    karana_num = min(karana_num, 60)

    if karana_num == 1:
        return 1, KARANA_NAMES_FIXED[3], "fixed"  # Kimstughna
    elif karana_num == 58:
        return 58, KARANA_NAMES_FIXED[0], "fixed"  # Shakuni
    elif karana_num == 59:
        return 59, KARANA_NAMES_FIXED[2], "fixed"  # Naga
    elif karana_num == 60:
        return 60, KARANA_NAMES_FIXED[1], "fixed"  # Chatushpada
    else:
        idx = (karana_num - 2) % 7
        return karana_num, KARANA_NAMES_RECURRING[idx], "recurring"


# =====================================================================
#  COMPUTE PANCHANGA (convenience function)
# =====================================================================

def compute_panchanga(year: int, month: int, day: float,
                      gregorian: bool = None) -> 'Panchanga':
    """
    Compute complete panchanga for a given date.

    Returns a Panchanga dataclass with all five elements plus
    masa, ritu, samvatsara, and raw longitudes.
    """
    from ._types import Panchanga
    from .ch02_true_places import compute, ayanamsha

    jd = julian_day(year, month, float(day), gregorian)
    sun = compute("Sun", year, month, float(day), gregorian)
    moon = compute("Moon", year, month, float(day), gregorian)

    sun_lon = sun.true_longitude
    moon_lon = moon.true_longitude
    aya = ayanamsha(jd)

    t_num, t_frac = tithi_from_elongation(moon_lon, sun_lon)
    paksha = "Shukla" if t_num <= 15 else "Krishna"

    v_idx, v_name = vara(jd)

    n_idx, n_name, n_pada, n_frac = nakshatra_from_longitude(moon_lon)

    y_num, y_name = yoga_from_longitudes(sun_lon, moon_lon)

    k_num, k_name, k_type = karana_from_elongation(moon_lon, sun_lon)

    m_idx, m_name = masa_from_sun_longitude(sun_lon)
    r_idx, r_name = ritu_from_sun_longitude(sun_lon)
    s_idx, s_name = samvatsara(jd)

    return Panchanga(
        year=year, month=month, day=int(day), jd=jd,
        tithi_={
            "number": t_num, "name": TITHI_NAMES[t_num - 1],
            "paksha": paksha, "elapsed": round(t_frac, 4),
        },
        vara_={
            "number": v_idx, "name": v_name,
            "name_en": VARA_NAMES_EN[v_idx],
        },
        nakshatra={
            "number": n_idx + 1, "name": n_name,
            "pada": n_pada, "elapsed": round(n_frac, 4),
        },
        yoga_={
            "number": y_num, "name": y_name,
        },
        karana_={
            "number": k_num, "name": k_name, "type": k_type,
        },
        masa={"number": m_idx, "name": m_name},
        ritu={"number": r_idx, "name": r_name,
              "name_en": RITU_NAMES_EN[r_idx]},
        samvatsara_={"number": s_idx, "name": s_name},
        sun_lon=sun_lon, moon_lon=moon_lon, ayanamsha=aya,
    )
