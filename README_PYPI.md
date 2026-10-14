# surya-siddhanta

A from-scratch Python implementation of the astronomy of the *Surya Siddhanta*,
following Ebenezer Burgess's 1860 translation, with all 14 chapters
implemented.

Every number comes from the text's own rules: mean motions, epicycles, the
sine table, eclipse rules, and so on. The library does not use Swiss
Ephemeris, pyephem or skyfield; its only dependency is `numpy`. Results
therefore differ slightly from modern ephemerides. That is the point: you
get what the Surya Siddhanta itself predicts.

## Install

```bash
pip install surya-siddhanta
pip install "surya-siddhanta[plot]"   # adds matplotlib, for eclipse diagrams
```

Requires Python 3.9 or later.

## Two ways to import

### By chapter (follows the book)

Each module implements one chapter. The file layout mirrors the book's own
structure:

```python
from suryasiddhanta.ch01_mean_motions import julian_day, compute_panchanga
from suryasiddhanta.ch02_true_places import compute
from suryasiddhanta.ch04_lunar_eclipses import compute_lunar_eclipse

print(compute("Jupiter", 628, 1, 1))        # true place of Jupiter, 1 Jan 628 CE
print(compute_panchanga(2024, 4, 9))        # tithi, vara, nakshatra, yoga, karana
eclipse = compute_lunar_eclipse(2025, 9, 7)
print(eclipse.is_eclipse, eclipse.eclipse_type, eclipse.magnitude)
```

| Module | Chapter |
|---|---|
| `ch01_mean_motions` | Mean motions, ahargana, calendar, panchanga |
| `ch02_true_places` | Epicyclic corrections, sine table, true places |
| `ch03_direction_place_time` | Direction, place and time: shadows, sunrise, lagna |
| `ch04_lunar_eclipses` | Lunar eclipses |
| `ch05_solar_eclipses` | Solar eclipses and parallax |
| `ch06_eclipse_projection` | Projection of eclipses |
| `ch07_conjunctions` | Planetary conjunctions |
| `ch08_stars` | Nakshatras and the star catalog |
| `ch09_heliacal` | Heliacal risings and settings |
| `ch10_lunar_horns` | Moon's phases and the elevation of her horns |
| `ch11_pata` | Vyatipata and Vaidhrita |
| `ch12_cosmography` | Cosmography: earth, orbits in yojanas, cosmic time |
| `ch13_instruments` | Armillary sphere, water clock, time from instruments |
| `ch14_reckoning_time` | The modes of reckoning time (manas), sankrantis, Jovian years |

### By planet (everything about one body)

`suryasiddhanta.planets` groups the same functions by graha: `sun`, `moon`,
`mars`, `mercury`, `jupiter`, `venus`, `saturn`, `rahu` and `ketu`. A chapter
function that takes a planet keeps its name, and the planet is already filled
in:

```python
from suryasiddhanta.ch01_mean_motions import julian_day
from suryasiddhanta.planets import sun, moon, mars, jupiter

jd = julian_day(2024, 4, 9)
sun.compute(2024, 4, 9).true_longitude   # Ch.2, planet="Sun" filled in
sun.sankrantis(2024)                     # Ch.14, the Sun's sign entries
moon.phase_name(jd)                      # Ch.10
mars.next_heliacal(jd)                   # Ch.9
jupiter.samvatsara(jd)                   # Ch.1, the sixty-year cycle
mars.REVOLUTIONS_PER_MAHAYUGA            # Ch.1 revolution table
```

Functions that need both the Sun and the Moon go where you would look for
them:

- the solar eclipse is in `sun`;
- the lunar eclipse and the phases are in `moon`;
- tithi, yoga, karana, panchanga and the patas are in both.

`ketu` is the point opposite Rahu. The text itself does not compute Ketu.

## Conventions

- **Time is a Julian Day in Ujjain mean time.** The text's epoch is midnight
  on the Lanka meridian, so `julian_day(y, m, d)` is midnight at Ujjain
  (UT + 5h 03m). Pre-Gregorian dates work. To convert to and from UT or
  local clock time, use `jd_to_ut`, `jd_from_ut`, `jd_from_clock` and
  `clock_from_jd` in `ch01_mean_motions`.
- **Longitudes are sidereal**, as in the text. `ch02_true_places.ayanamsha`
  gives the Surya Siddhanta's own oscillating ayanamsha (±27° over 7200
  years, zero in 499 CE) for converting to tropical.
- **Planet names** are given as in `"Sun"`, `"Moon"`, `"Mars"`, `"Mercury"`,
  `"Jupiter"`, `"Venus"`, `"Saturn"`.

## License

MIT.
