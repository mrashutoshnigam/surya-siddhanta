# Running the Text: A Verse-Traceable Computational Edition Across All Fourteen Chapters of the *Sūrya Siddhānta*, and What Implementing It Reveals

Ashutosh Nigam and Dr. Dinesh Mohan Joshi

Indian Institute of Technology Jodhpur, India

## Abstract

Most computational studies of the *Sūrya Siddhānta* have examined its planetary theory. We present an open Python edition of the computable material across all fourteen chapters, based chiefly on Burgess's 1860 translation and checked against worked examples in Mahavir Prasad Srivastava's Hindi *Vigyan Bhashya*. Its 224 public functions cover planetary positions as well as eclipses, conjunctions, junction stars, heliacal phenomena, the lunar crescent, *pātas*, cosmography, instruments and time reckoning. The historical calculations use no modern ephemeris. Each function cites its relevant verses; where the verses do not specify a procedure, the implementation identifies a choice drawn from commentary or an explicit convention. A suite of 1,256 automated tests records the resulting behaviour.

Implementing the procedures revealed nine readings that produced plausible code but the wrong quantity. For example, treating the inner planets' *śīghrocca* revolutions as their mean motions placed Mercury 153° from the Sun. Interpreting the epoch's Julian Day as Universal Time instead of Ujjain mean time shifted sidereal time by about 76°; in a 1926 eclipse example, correcting the time base changed the computed longitude parallax from 3.83 to 1.16 ghatikas, compared with Srivastava's 1.06. The edition also makes implicit results calculable, including the duration of the 86-degree solar intervals (84.8–89.5 days) and the irregular advance of Jovian year names. We distinguish such findings from deliberate departures from printed examples and from errors in the sources. A separate comparison with JPL DE440 measures the longitude error of this implementation under stated time and frame conventions. The source code, tests and data are public.

**Keywords:** Sūrya Siddhānta; Indian astronomy; computational history of science; executable edition; textual criticism; software verification

## Introduction

The *Sūrya Siddhānta* is among the best-known astronomical works of the Indian *siddhānta* tradition. A traditional account places it first among eighteen revealed *siddhāntas* [12]. The two lists reproduced by Burgess, however, place it second, after the *Brahma-siddhānta* [1, Appendix, note to p. ii]. Burgess chose the text for translation because of its standing and continued use in nineteenth-century Indian astronomy. Its fourteen chapters treat planetary positions, direction and place, eclipses, conjunctions, stars, visibility, the lunar crescent, *pātas*, cosmography, instruments and measures of time [1, 7, 8]. His 1860 translation and notes remain the principal English reference for the work.

The rules of a procedural text can be paraphrased without settling every detail needed to carry them out. A calculation cannot. It must specify which quantity a rule uses, where a date begins, and how one chapter passes a result to another. Those decisions become visible when the procedure is run for a dated example. We use implementation in this sense: as a way to test a reading of the text.

Earlier computational work has concentrated on planetary positions (see Related work). This paper describes an implementation of the computable material across all fourteen chapters. It contributes an open library with one module per chapter; verse citations and explicit labels for rules supplied by commentary; tests against the text and Srivastava's worked examples; and nine cases in which running a plausible reading exposed an error. For the longitude calculations, we also report the results of a companion comparison with JPL DE440. Chapters 11–14 are included in the library, though some verses in every chapter remain outside its scope.

The edition is a stated reading of the procedures, not a reconstruction of any particular historical *pañcāṅg*-maker's practice. Its functions and tests are intended to let another reader locate a disputed choice and examine the effect of changing it.

## Related work

Pingree [7] and Plofker [8] survey the broader mathematical and astronomical tradition. Duke [2] analyses the epicyclic planetary models of the *Sūrya Siddhānta*. These studies explain the rules but do not provide executable editions of the text.

Santhoju and colleagues [10] compute location-specific true (*nirāyaṇa*) planetary longitudes and compare them with Stellarium; their treatment uses the fractional part of the *ahargaṇa*, a departure from the procedure adopted here. Their subsequent study [11] extends the calculation to geocentric latitudes and declinations. Roy [9] argues that the junction-star catalogue uses sidereal ecliptic coordinates, while Narayanan [3] uses computational simulation to investigate the text's date. A companion, unpublished study by Ashutosh Nigam [4] compares this edition's Chapter 1–2 longitudes with JPL DE440 [6] at 40,176 epochs. We discuss its results below.

We found no published implementation of the chapters on eclipse projection, conjunctions, heliacal visibility, the crescent, *pātas*, cosmography, instruments or time reckoning that also links its tests to verses and printed examples. This assessment is limited to English-language journals and public code repositories.

## Sources and editorial principles

**Sources.** The rules and constants come primarily from Burgess's translation and notes [1]. Srivastava's *Sūrya Siddhānta: Vigyan Bhashya* [14] provides a second kind of evidence: dated worked examples for Kashi, Prayag and other places in the 1920s, often with intermediate figures. We use those examples to check calculations, while keeping the verse and Burgess's commentary distinct. The Hindi text was consulted through OCR; doubtful digits were checked against the page images (see Errors in the printed sources).

**Editorial principles.** Five decisions govern the implementation:

- **P1 — Follow the verse where it specifies a rule.** If Burgess supplies a different procedure or fills a gap, the code records that procedure separately with `source = "commentary"`. The instruments of Chapter 13 and the methods of naming a Jovian year in Chapter 14 provide examples.
- **P2 — Keep modern ephemerides out of the historical calculation.** NumPy is the library's only runtime dependency. Given constants, including the 24° obliquity and the sine table of radius 3438, retain their textual values. Commentary or a documented convention supplies steps the verses leave unspecified.
- **P3 — Use one time base.** The Julian Day used within the calculations is reckoned in Ujjain mean time, as implied by the epoch of i.50. Civil-time conversion occurs at the boundaries of the system.
- **P4 — Record departures from worked examples.** The audit gives the size and reason for each known difference. Where a numerical assertion is present, it also detects a change in that difference; no parameter is adjusted merely to match a printed answer.
- **P5 — Document omissions.** The chapter documentation identifies verses that are not implemented and gives the reason.

## The edition

### Structure

The Python library `suryasiddhanta` (Python ≥ 3.9, MIT licence) has a module for each chapter, beginning with `ch01_mean_motions` and `ch02_true_places`. Later modules use earlier results where the text does: Chapter 5's parallax calculation calls the sidereal-time routine of Chapter 3, and Chapter 11's *pāta* calculation uses true places from Chapter 2 and declination from Chapter 3. Typed records carry results such as planetary positions, *pañcāṅgas*, eclipses, *pātas* and armillary spheres between modules. Four JSON catalogues hold material stated rather than calculated: the junction stars, cosmographic descriptions, fixed stars of the armillary sphere and nine measures of time. Table 1 gives the coverage by chapter.

**Table 1. Coverage of the edition by chapter. “Fns” counts public functions; “Tests” counts the chapter's automated tests.**

| Ch. | Subject | Fns | Tests | Principal content implemented |
| --- | --- | --- | --- | --- |
| 1 | Mean motions | 33 | 102 | revolutions per age, *ahargaṇa*, mean places, epoch positions, *tithi*, *yoga*, *karaṇa*, sixty-year cycle |
| 2 | True places | 35 | 169 | sine table, *manda* and *śīghra* equations, four-step true place, latitude, daily motion, trepidation |
| 3 | Direction, place, time | 17 | 81 | gnomon, latitude, ascensional difference, rising times, sidereal time, *lagna* |
| 4 | Lunar eclipses | 8 | 52 | disc and shadow diameters, magnitude, half-duration |
| 5 | Solar eclipses | 7 | 55 | nonagesimal, *lambana* and *nati*, topocentric eclipse |
| 6 | Eclipse projection | 7 | 46 | *valana*, contact points, diagram geometry |
| 7 | Conjunctions | 7 | 58 | planet–planet and planet–star conjunction, *yuddha* classification |
| 8 | Junction stars | 8 | 57 | catalogued *dhruvakas* and *vikṣepas* of the 27 *yogatārās* and Abhijit, positions, rising and setting |
| 9 | Heliacal phenomena | 6 | 44 | visibility limits, risings and settings |
| 10 | Lunar crescent | 9 | 46 | illuminated part, crescent width, horn angles, moonrise |
| 11 | *Pātas* | 9 | 24 | declination equality, true instant, duration |
| 12 | Cosmography | 32 | 58 | orbits per kalpa, earth's circumference, *deśāntara*, zones, regents |
| 13 | Instruments | 29 | 56 | parametric armillary sphere, time from altitude, four time instruments, clepsydra |
| 14 | Measures of time | 17 | 29 | nine *mānas*, *saṁkrāntis*, *ṣaḍaśītimukhas*, Jovian years |
|  | Total | 224 | 877 | plus 379 tests of the per-planet interface |

### Conventions

*Time.* Calculations use Julian Days in Ujjain mean time (P3). Calendar input is Julian before 15 October 1582 and Gregorian from that date onward. The relation between this time base and the epoch is discussed below.

*Longitude.* Positions are sidereal. To obtain a tropical longitude, the code applies the text's oscillating *ayaṇāṁśa* (±27° over 7,200 years, with a zero near 499 CE), rather than continuous precession.

*Sines.* Planetary equations interpolate in the 24-entry sine table of radius 3438. For geometric rules without a supplied table, the code uses modern trigonometric functions. The procedures therefore follow the adopted reading of the text, but their final digits need not match a historical hand calculation.

### Two chapters that are not ephemerides

Much of Chapter 12 gives fixed dimensions. The module derives them from three starting quantities—the Earth's diameter of 1,600 *yojanas*, its circumference of 1600√(10), and the Moon's orbit of 324,000 *yojanas*—together with the revolution numbers from Chapter 1. The orbits in xii.80–90 must be reckoned per kalpa: using a mahayuga makes them a thousand times too small. Multiplying the Moon's revolutions in a kalpa by her orbit yields 18,712,080,864,000,000 *yojanas*, the ether orbit stated in xii.90. Although i.59–61 give the Earth's circumference, its latitude correction and the *deśāntara*, these rules are implemented in Chapter 12 because its calculations need them.

Chapter 13 describes instruments. Its armillary sphere is represented in an equatorial frame, with the north pole on *z* and the vernal equinox on *x*. Each hoop is specified by a unit normal and an offset, allowing a renderer to draw the model without repeating the astronomical calculation. At Ujjain the model has 46 hoops. It calculates the ecliptic point on the eastern horizon without sign-by-sign interpolation and places the stellar hoops according to a polar reading of ii.58. The gnomon, wheel, arc and staff each return time from the solar-altitude rule of iii.34–39. Methods reconstructed from Burgess's commentary, rather than specified by the verse, carry a `source` label.

### Per-planet interface and distribution

A separate interface groups the chapter functions by body (`sun`, `moon`, `mars`, …, `rahu`, `ketu`) and supplies the body argument to each wrapper. It adds no planetary calculation except the convention that Ketu is 180° from Rahu; the chapters do not compute Ketu independently. Its 379 tests compare wrapper signatures with those of the underlying functions. The calculation package itself depends only on NumPy.

## Verification method

We checked the edition at three levels. First, 877 chapter tests and 379 interface tests—1,256 in all—check the implemented rules and their connections. All pass in the reported run. Many use constraints drawn from a particular verse or example: Mercury and Venus remain within 28° and 48° of the Sun, respectively; epoch positions of apsides and nodes agree with Burgess's table under i.44 to one arc-second; the months and seasons have the spans given in xiv.9–10; and the year 1859–60 CE bears Burgess's sixty-year name *Prajāpati* (i.55).

Second, an audit takes 257 selected computations from Srivastava, reconstructs their inputs (*ahargaṇa*, Vikrama year and place), and compares the library's results at the precision printed in the book. Disagreements are classified as a fixed library defect, a documented deviation, an inconsistency in the printed source or OCR, or a calculation for which the library has no function. The reported audit run has 197 passes, 48 documented deviations and 12 skips. Of the skips, three concern source errors, seven lack a function, one is a deviation that cannot be compared, and one concerns material outside the verses.

Third, the companion DE440 study tests the Chapter 1–2 longitude path against a modern ephemeris. This comparison measures the result of the implemented model under stated conventions; it serves a different purpose from checking a rule against the text.

## What implementing the text revealed

### Readings that produce a wrong computation

Nine readings initially led to a program that ran but calculated the wrong quantity. Table 2 records the verse, the resulting error and the check that revealed it. These cases matter because a calculation can be internally consistent while misreading the procedure it implements.

**Table 2. Nine readings that completed the calculation but produced the wrong quantity. The last column identifies the check that exposed each error.**

| Verse | Reading that failed | Symptom and size | Detected by |
| --- | --- | --- | --- |
| i.29, i.31–32 | Mercury's and Venus's 17,937,060 and 7,022,376 revolutions used as their mean motion | they belong to the *śīghrocca*; the *śīghra* anomaly of ii.44 became identically zero; Mercury 153° from the Sun on 2024-01-01 | elongation bound (28°/48°) |
| i.57 | inner *śīghroccas* given non-zero epoch places (220°, 90°) | both complete whole revolutions in the half-age to Kali, so both are 0° at the epoch | derivation from i.57 |
| ii.29, ii.45 | *manda* anomaly taken as planet - apsis | the text defines apsis - planet; the equation of centre changed sign, and the Sun's error swung by ±4° | worked example; comparison with the modern equation of centre |
| ii.67 | fixed *karaṇas* 59 and 60 in modern almanac order | the text's order is Śakuni, Nāga, Catuṣpada, Kiṁstughna | Burgess's table under ii.69 |
| iv.2 | lunar diameter scaled by 1/(1-0.055cosκ) | the disc came out largest at apogee; the verse scales by true over mean motion: 480 × 853.7/790.6 ÷ 15 ≈ 34.554' with the rounded inputs shown for the Kashi example | book example; displayed inputs rounded |
| xi.14 | *pāta* half-duration divided by the rate at which the declinations separate | the verse divides by the difference of the daily motions; durations fell from several hours to 1.7–2.4 hours | verse |
| xii.78–79 | regents of month and year taken from true solar months and years | uniform 30- and 360-day periods counted from creation (the days from creation to Kali leave 17 and 347) | Burgess i.51–52 |
| xiv.10 | seasons starting with Vasanta at Taurus | Śiśira begins at Capricorn, so Taurus–Gemini is Grīṣma; one season off | verse |
| xiv.17 | mean-longitude Jovian year labelled `verse` | the verse names the year from Jupiter's heliacal phases; the mean method is Burgess's reading | verse |

The inner-planet case illustrates the value of a constraint taken from the text. When Mercury's and Venus's *śīghrocca* revolutions were treated as their mean motions, the mean place and *śīghrocca* coincided. The four-step true-place routine still produced a number, but Mercury lay 153° from the Sun on 1 January 2024. The elongation bound exposed the mistake. The lunar-diameter case required a different check: Srivastava's arithmetic, followed to the printed precision, showed that the verse scales the diameter by true divided by mean motion, rather than by the modern-looking formula first used in the code.

### What a date means: the time base fixed by the epoch

The epoch of i.50 begins at midnight on the Laṅkā meridian, which passes through Ujjain. Julian Days derived from the text's day count are consequently reckoned in Ujjain mean time, about 5 h 03 m (75.79/360 of a day) ahead of Universal Time. A modern sidereal-time routine expects Universal Time. Passing it the textual Julian Day without conversion shifts the computed sky by about 76°. This error then affects the *lagna*, parallax, *valana*, risings and settings, and the armillary sphere.

The discrepancy became apparent in Srivastava's calculation of the solar eclipse at Kashi on Pauṣa amavasya, Vikrama 1982 (14 January 1926). With the two clocks mixed, the first longitude-parallax result was 3.83 ghatikas; using a single time base changed it to 1.16, near the book's 1.06 (Table 3). Both versions of the code were internally consistent, so the worked example was needed to identify the time-base error.

**Table 3. The Kashi solar eclipse of 14 January 1926 and the effect of the time base. The gap that remains after the fix arises mainly from the book's three-pass (*asakrt*) iteration and its larger solar disc, neither of which the edition adopts (Table 4).**

| Quantity | Two clocks mixed | One clock (this edition) | Srivastava |
| --- | --- | --- | --- |
| Longitude parallax, first pass (ghatikas) | 3.83 | 1.16 | 1.06 |
| Latitude parallax (*nati*) | -12.7' | -33.8' | -34.6' |
| Obscured part (*grāsa*) | magnitude 0.50 | 27.5' | 25.6' |

The epoch also sets the zero for *deśāntara* (i.60–61) at the Laṅkā–Ujjain meridian, not Greenwich. On that basis the edition obtains 7°16'58” for Kashi, or 1 ghaṭikā 12 pala 50 vipala, agreeing with Srivastava's table. Establishing the clock associated with an epoch is therefore necessary before comparing event times from this or another *siddhānta* with modern calculations.

### Polar against ecliptic star coordinates

Chapter 8 gives each junction star a *dhruvaka* and a *vikṣepa*, but their coordinate interpretation is disputed. Burgess treats them as polar coordinates associated with a circle of declination. Roy [9] argues for sidereal ecliptic coordinates. We implement both: Chapter 8 uses the ecliptic reading, whereas the Chapter 13 armillary sphere uses a polar construction based on our reading of ii.58. Keeping both procedures available records the interpretive choice; the implementation does not settle the historical question.

For 2024, the resulting declinations differ by less than 0.5° for 17 of the 28 stars. The largest differences are 2.4° for Uttara Bhādrapadā, 2.0° for Pūrva Bhādrapadā, 1.8° for Svātī and 1.5° for Dhaniṣṭhā. Against the modern positions quoted by Srivastava, the Chapter 8 ecliptic reading places Svātī's right ascension 16.6° away. That comparison gives reason to retain the polar alternative, although it cannot establish the meaning of every historical passage. Table 4 includes the gap between the implementations.

The *dhruvakas* provide a separate check on the catalogue. Verse viii.1 says to multiply a star's share by ten and add the minutes of the preceding asterisms, each of which spans 13°20' (800 minutes); viii.2–5 give the shares. Thus, for a star in the *n*th asterism with share *sₙ*,

$$
dhruvaka = 10s_n + 800(n - 1) minutes.
$$

Twenty-four stars receive shares. The positions of Uttarāṣāḍhā, Śravaṇa, Dhaniṣṭhā and Abhijit are specified separately in viii.4. The derived values agree with the catalogue for all 27 stars; Revatī differs by 0.2' only because the catalogue rounds 359°50' to two decimal places.

### Quantities the text implies but does not state

The calculations also expose results that the verses imply without giving explicitly.

**The *ṣaḍaśītimukhas* (xiv.4–6).** Four points lie 86° apart, counted from Libra 0°: 266°, 352°, 78° and 164°. The remaining 16° of Virgo closes the circle (4 × 86 + 16 = 360). The verse's “eighty-six days” therefore correspond to degrees of solar motion, not equal periods of elapsed time. Because the Sun's motion is non-uniform, the 1,604 intervals calculated over solar years 1800–2200 last from 84.8 to 89.5 days. Burgess notes that the text does not explain the division's purpose. The positions can be derived; their intended use remains uncertain.

**Jovian years (xiv.15–17).** The twelve year names are the names of the months. Verses xiv.15–16 distribute the 27 asterisms among them: nine months receive two asterisms and three receive three (9 × 2 + 3 × 3 = 27). A month name consequently spans roughly 27–40° of longitude, while a mean Jovian year spans exactly 30°. The name need not advance by one place each year. The underlying analysis reports 1,978 sampled transitions associated with calculations dated 1700–2300: the name advances by one in 83.4 per cent, by none in 8.3 per cent and by two in 8.4 per cent. Every twelve-year run nevertheless returns to its starting name. Sewell and Dikshit [13] describe the irregularity; here it follows directly from the text's month–asterism assignments. The library also offers the verse's heliacal method and reports years for which the two methods disagree.

**The scale of the universe (xii.80–90).** Reckoning the orbits per kalpa gives the ether orbit stated in xii.90 from the Moon's revolutions. The derived solar orbit is 4,331,500 *yojanas*, the value reported by Burgess.

**Instruments (xiii).** The four time-finding instruments return the same time for a given solar altitude because each calculation reduces to iii.34–39. Computing them separately makes that shared geometry explicit.

### Errors in the printed sources

Srivastava's OCR transcript often reads the Devanagari digit nine as six. We checked disagreements involving those digits against the page images before treating them as errors in the library. The images support the library's values for Puṣya's share of 76 (106°), Rohiṇī's 49°30' (read as 46°30' by OCR), a lunar declination of 18°54'11.5” in Chapter 11 (OCR: 15°), the divisor 900 in x.9 (OCR: 600), and the Vikrama years 1991–95 in Chapter 14 (OCR: 1961–65).

Some inconsistencies are present in the print itself. A Chapter 3 zenith distance is given as 9°51', though the sine on the preceding line corresponds to 10°01', the value returned by the library. Chapter 2 prints two positions for Jupiter on the same date. An external almanac may account for another difference: Srivastava's *Visva Pañcāṅg* puts Jupiter 2.18° from the edition's result while its Mars, Mercury and Saturn differ by only 1–3'. Since the edition's Jupiter agrees with Burgess's worked example, we suspect the almanac's Jupiter constant, but cannot establish the cause from this comparison alone.

### Deviations kept on purpose

The edition retains several differences from Srivastava where his examples use a modern value or a refinement that the library does not implement. Table 4 gives the main cases. The audit records the size and reason for a difference; only cases with a numerical assertion automatically detect a change in its magnitude.

**Table 4. Deliberate differences between the edition and Srivastava’s worked examples.**

| Area | Edition | Srivastava | Typical gap |
| --- | --- | --- | --- |
| Obliquity | 24° (text) | 23°27' (modern) | declination 22–28' |
| *Ayaṇāṁśa*, 1920s | text's trepidation, 21°24' | almanac, 22°41' | 1°17' |
| Eclipse discs (iv) | solar disc fixed | scaled by anomaly | 1–5' |
| Eclipse timing | one pass | three-pass *asakrt* iteration | 5–20 min |
| Eclipse projection (vi) | straight chords | changing latitude | *valana* 0.6–1.2° |
| Star coordinates (viii) | ecliptic reading in Ch. 8 | polar (ii.58) | up to 2.4° in declination |
| Heliacal limits (ix) | ecliptic elongation | *kālāṁśa* | 2.6–3.5° for Venus |
| *Pāta* (xi) | text’s Moon and node | Nautical Almanac | declination 1.8° |
| Jovian year (xiv) | twelfth of a revolution (Burgess) | Sun–Jupiter conjunction interval | method |

## How accurate is the edition? A bound from DE440

An unpublished companion study [4] compares the implementation's tropical longitudes for the Sun, Moon, five planets and lunar node with JPL DE440 [6]. It samples 40,176 epochs at ten-day intervals over 1,100 years, from 1550 to 2649 CE, converting the Ujjain-mean-time base to Terrestrial Time using ΔT. For centuries through 2249 CE, the reported RMS error is 1.14–1.93° for the Sun, 1.69–2.29° for the Moon and 1.88–9.45° for the five planets. The companion study relates much of the longer-term trend to drift in the adopted mean motions and to the text's trepidation model of precession, which reverses in 2299 CE.

Eight bodies, two time variants and 40,176 epochs give 642,816 residuals. Reconstructing them independently from the kernel reproduced the stored values to within 5.5 × 10⁻⁷ degrees. This is a check on the comparison and residual arithmetic under the chosen conventions. It does not validate every textual reading, nor does it exclude implementation error from the measured differences. The reported errors describe this implementation of the historical model.

## Availability and reproducibility

The code for version 2.0.0 is in the [public repository](https://github.com/mrashutoshnigam/surya-siddhanta) [5]. This paper refers to main-branch commit `36d8c53e714d`; reference [5] gives the full hash. The repository contains the calculation library, tests, four catalogues, the companion DE440 manuscript, stored results and instructions for regenerating them. Repeating the DE440 comparison also requires the JPL kernel identified in those instructions. The Srivastava audit counts come from an audit branch and remain reported results until the cases and exact revision are archived with the paper. The repository's web and conversational interfaces are outside the scope of this study.

## Discussion

The errors found during implementation were not evident from the procedures as paraphrased. They appeared when a result violated a textual constraint or disagreed with a worked example. In particular, the inner-planet and time-base errors left the program internally consistent. Their diagnosis required a check external to the mistaken routine but still grounded in the text or its printed calculation.

This is what the test suite adds to the edition. A printed note can state an editor's reading; here the reading is also a function whose consequences can be recalculated. A different interpretation of ii.58, for example, can be implemented in one function and traced through star positions, armillary hoops and rising times. The `source` label identifies where a procedure comes from a verse and where it comes from commentary.

The edition has limits. It relies mainly on Burgess's translation; we did not prepare a new Sanskrit edition. Srivastava's examples were read through OCR, with page images checked where digits were doubtful. The library omits some rules and verses, including the disc diameters in vii.13–14, stellar visibility limits in ix.12–18, the Moon's visibility limit in x.1, the equation of time, and descriptive or astrological passages. Its documentation records omissions by chapter. Modern trigonometric functions also replace geometric procedures where the text gives no table, so the code does not reproduce every rounding choice of historical hand calculation. Coverage across fourteen chapters should be understood as coverage of their computable core, not of every verse.

## Conclusion

Implementing the *Sūrya Siddhānta* across its fourteen chapters made several interpretive choices testable. Nine initially plausible readings yielded the wrong quantity. The epoch of i.50 fixed the time base needed for place-dependent calculations; the star coordinates admitted competing polar and ecliptic procedures; and computations supplied values implicit in the verses, including the *ṣaḍaśītimukha* intervals, Jovian year-name advances, the *dhruvakas* and the ether orbit of xii.90. Verse-linked functions and tests record the readings behind these results. The code permits other readers to test alternatives, although the worked-example audit will be fully reproducible only when its cases and exact revision are archived.

## Statements

**Author contributions.** Ashutosh Nigam conceived the work, wrote the software and tests, carried out the verification, and drafted the manuscript. Dr. Dinesh Mohan Joshi advised on the Sanskrit text and its astronomy, checked the adopted readings, and reviewed the software and manuscript. Both authors approved the final manuscript.

**Competing interests.** The authors declare no competing interests.

## References

1. Ebenezer Burgess (1860). “Translation of the Sūrya-Siddhānta, a Text-Book of Hindu Astronomy; with Notes and an Appendix.” *Journal of the American Oriental Society* 6, 141–498.
2. Dennis Duke (2005). “The Equant in India: The Mathematical Basis of Ancient Indian Planetary Models.” *Archive for History of Exact Sciences* 59(6), 563–576. https://doi.org/10.1007/s00407-005-0096-y
3. Anil Narayanan (2010). “Dating the Sūrya Siddhānta Using Computational Simulation of Proper Motions and Ecliptic Variations.” *Indian Journal of History of Science* 45(4), 455–476.
4. Ashutosh Nigam (2026). “Evaluating the Accuracy of Surya Siddhanta Planetary Algorithms against JPL DE440, 1550–2649 CE.” Unpublished manuscript. Source, data and figures: https://github.com/mrashutoshnigam/surya-siddhanta/tree/main/docs/evaluation
5. Ashutosh Nigam (2026). *suryasiddhanta: A Verse-Traceable Python Implementation of the Sūrya Siddhānta*. Version 2.0.0, MIT licence, public main-branch commit `36d8c53e714d699641289daf5b59dc8cef21ab65`. https://github.com/mrashutoshnigam/surya-siddhanta
6. Ryan S. Park, William M. Folkner, James G. Williams and Dale H. Boggs (2021). “The JPL Planetary and Lunar Ephemerides DE440 and DE441.” *The Astronomical Journal* 161(3), article 105. https://doi.org/10.3847/1538-3881/abd414
7. David Pingree (1978). “History of Mathematical Astronomy in India.” *Dictionary of Scientific Biography*, vol. 15, supplement 1, 533–633. New York: Charles Scribner’s Sons.
8. Kim Plofker (2009). *Mathematics in India*. Princeton: Princeton University Press.
9. Raja Ram Mohan Roy (2019). “Sidereal Ecliptic Coordinate System of Sūryasiddhānta.” *Indian Journal of History of Science* 54(3), 286–303. https://doi.org/10.16943/ijhs/2019/v54i3/49740
10. Pandu Santhoju, Punit Bhalla, Laxmidhar Behera and R. Venketeswara Pai (2025). “Mathematical Model as per the Algorithm of Sūryasiddhānta for Computation of Location Specific True Position of the Planets.” *Journal of Astrophysics and Astronomy* 46(1), article 9. https://doi.org/10.1007/s12036-024-10018-8
11. Pandu Santhoju, Venketeswara R. Pai and Laxmidhar Behera (2026). “Computation of Planetary Geocentric Latitudes and Declinations Based on the Sūryasiddhānta Algorithm.” *Indian Journal of History of Science* 61(1), 9–36. https://doi.org/10.1007/s43539-026-00198-3
12. Prabodhchandra Sengupta (1935). “Introduction.” In Phanindralal Gangooly (ed.), *Translation of the Sūrya-Siddhānta, a Text-Book of Hindu Astronomy, by Ebenezer Burgess, reprinted from the edition of 1860*, vii–lvi. Calcutta: University of Calcutta.
13. Robert Sewell and Śaṅkara Bālakṛṣṇa Dikshit (1896). *The Indian Calendar: With Tables for the Conversion of Hindu and Muhammadan into A.D. Dates, and Vice Versa*. London: Swan Sonnenschein.
14. Mahavir Prasad Srivastava (1982–1983). *Sūrya Siddhānta: Vigyan Bhashya*, 2 vols., 2nd ed. Allahabad: Dr. Ratnakumari Svadhyaya Sansthan. Consulted copy: vol. 1 dated March 1982; vol. 2 dated May 1983. First issued by Vijnana Parishad in 1940.

## Verses not implemented, by chapter

| Ch. | Not implemented (reason) |
| --- | --- |
| 1 | Civil-calendar-to-luni-solar input conversion for the text's *ahargaṇa* route; the route itself is implemented as `ahargana_from_luni_solar` |
| 3 | Equation of time, refraction, sundial-to-standard-time conversion (in the commentary, not the verses) |
| 4 | iv.8, 15, 17–26 (eclipse colour, effects and verses the library does not compute) |
| 4–5 | Three-pass (*asakrt*) iteration; anomaly scaling of the solar disc |
| 7 | vii.7–10, 13–18 (disc diameters and the dependent rules) |
| 9 | ix.4–5, 11, 16–17 (ascensional equivalents); ix.12–18 (visibility limits of the stars) |
| 10 | x.1 (the Moon's visibility limit), x.2–8 (setting interval, elevation of the horns) |
| 11 | xi.4–5, 16–18 (character and effects), 20–23 (the asterism-counted third *yoga*) |
| 12 | Descriptive verses (creation, the underworlds, Maya's questions) and xii.91 onwards |
| 13 | xiii.1–3, 16–19, 21–22 (narrative and construction detail) |
| 14 | xiv.3, 22–27 and Burgess's appendix |
