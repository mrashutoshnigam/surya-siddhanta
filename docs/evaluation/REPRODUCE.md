# Reproducing the DE440 evaluation paper

How to rerun the calculations behind
[`paper/surya-siddhanta-vs-de440.md`](paper/surya-siddhanta-vs-de440.md) and update the
paper when the results change. Everything is driven by one script,
[`regenerate_paper.py`](regenerate_paper.py). It uses the Chapter 1/2 implementation, the
local DE440 kernel and the two audit helpers in [`validation/`](validation/). It does not
need the old `suryasiddhanta.evaluation` package, which no longer exists.

All commands run from the repository root.

## 1. Prepare the environment

Linux/macOS (bash):

```bash
python3 -m venv .venv-paper
.venv-paper/bin/python -m pip install -e ".[plot,dev]" jplephem
.venv-paper/bin/python -m pytest tests/test_ch01_mean_motions.py tests/test_ch02_true_places.py -q
```

Windows (PowerShell):

```powershell
python -m venv .venv-paper
.\.venv-paper\Scripts\python.exe -m pip install -e ".[plot,dev]" jplephem
.\.venv-paper\Scripts\python.exe -m pytest tests/test_ch01_mean_motions.py tests/test_ch02_true_places.py -q
```

Required files:

- `paper/data/kernels/de440.bsp` (about 114 MiB, not in git). Download it from
  [JPL NAIF](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp).
  The script refuses to run unless its SHA-256 is
  `a4ce9bf9b3282becc9f4b2ac3cebe03a2ae7599981aabd7265fd8482fff7c4b5`.
- `docs/evaluation/validation/kernel_audit.py`
- `docs/evaluation/validation/numerics_audit.py`

## 2. Run without writing anything

```bash
.venv-paper/bin/python docs/evaluation/regenerate_paper.py
```

(PowerShell: `.\.venv-paper\Scripts\python.exe docs/evaluation/regenerate_paper.py`)

This recomputes both time variants for all 40,176 epochs and eight bodies, a few seconds'
work, and prints Tables 2–6, the diagnostics and the provenance as JSON. For the current
paper, expect:

- 40,176 epochs; JD endpoints 2287195.5 and 2688945.5.
- Grid SHA-256 `8d2d5d7cbda66baf8b966aa38f0fb226381306cf842efc382953a973315d235b`.
- Elongation MAE about 1.178449 degrees, maximum 3.937849 degrees.
- 3,966 sampled tithi-index disagreements.
- Joint 883-year drifts about +7.144078 (Jupiter) and -27.861331 (Saturn) arcseconds/year.
- 271 passing tests in step 1 (a later code revision may change this count).

A change to the astronomical code can legitimately change these numbers. Find out why
and document it; don't force the old values.

## 3. Save data and figures

```bash
.venv-paper/bin/python docs/evaluation/regenerate_paper.py --write
```

This writes to `docs/evaluation/regenerated/` (replacing earlier runs):

| Output | Use |
|---|---|
| `residuals_naive.csv`, `residuals_deltat.csv` | Every residual, for the uncorrected-time and Delta-T-corrected variants |
| `century_naive.csv`, `century_deltat.csv` | Per-century counts, means, RMS and largest values |
| `ayanamsha_vs_precession.csv` | Frame diagnostic |
| `tables_regenerated.md` | Copy-ready Tables 2–6 |
| `diagnostics.json` | Joint fits, tithi comparison, smoothing and century diagnostics |
| `provenance.json` | Kernel, grid, source and output hashes, package versions and git commit |
| Eleven PNG files | Eight body plots, one precession plot and two heatmaps |

The script never edits the paper or the CSVs/PNGs the paper links to.

## 4. Adopt the outputs into the paper

1. Check `provenance.json` and `diagnostics.json`, and look at the eleven PNGs.
2. If anything changed, copy the tables from `tables_regenerated.md` into Tables 2–6 of the
   Markdown paper, and update the abstract, Sections 5–7 and anything else that quotes
   those values. Table 1's modern mean-element rates are not computed by the script;
   changing them needs a separate, documented calculation.
3. Replace the CSVs and PNGs the paper links to:

   ```bash
   cp docs/evaluation/regenerated/*.csv docs/evaluation/regenerated/*.png docs/evaluation/
   ```

   PowerShell:

   ```powershell
   Get-ChildItem -LiteralPath .\docs\evaluation\regenerated -File |
       Where-Object { $_.Extension -in '.csv', '.png' } |
       Copy-Item -Destination .\docs\evaluation -Force
   ```

4. Update the environment details in the paper's Section 4.6 if they changed.
5. Carry the same edits into `paper/surya-siddhanta-vs-de440.tex` (the Markdown is the
   source; the TeX is maintained by hand to match it) and rebuild the PDF as described in
   the repository [README](../../README.md#build-the-de440-evaluation-paper-pdf).

The older scripts in `validation/` can replay checks on earlier CSVs, but
`numerics_audit.py` uses the earlier decimal-year regression convention when comparing
Table 5, so it is not the updater for the current paper.

The script covers the longitude comparison and diagnostics in the paper. It does not
produce event-based eclipse or tithi timing errors.
