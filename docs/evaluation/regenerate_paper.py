"""Regenerate the data, tables and figures of the DE440 evaluation paper.

Run from the repository root:

    python docs/evaluation/regenerate_paper.py           # compute and print only
    python docs/evaluation/regenerate_paper.py --write   # also save outputs

Outputs go to docs/evaluation/regenerated/. See docs/evaluation/REPRODUCE.md.
"""
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
sys.dont_write_bytecode = True
import numpy as np
from jplephem.spk import SPK

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "docs/evaluation/validation"))
from kernel_audit import references, delta_t, wrap
from numerics_audit import BODIES, calendar, january_jd, rms
from suryasiddhanta.ch01_mean_motions import (
    julian_day, from_julian_day, mean_longitude,
    KALI_EPOCH_JD, SIDEREAL_YEAR_DAYS,
)
from suryasiddhanta.ch02_true_places import ayanamsha, true_longitude_full

kernel_path = ROOT / "paper/data/kernels/de440.bsp"
expected = "a4ce9bf9b3282becc9f4b2ac3cebe03a2ae7599981aabd7265fd8482fff7c4b5"
digest = hashlib.sha256(kernel_path.read_bytes()).hexdigest()
if digest != expected:
    raise RuntimeError("DE440 checksum mismatch")
jd = np.arange(julian_day(1550, 1, 1), julian_day(2649, 12, 31) + 1e-9, 10.)
assert len(jd) == 40176 and jd[-1] == 2688945.5
cy, cm, cd = calendar(jd)
start = january_jd(cy, jd >= 2299160.5)
end = january_jd(cy + 1, jd >= 2299160.5)
start = np.where(cy == 1582, january_jd(1582, False), start)
end = np.where(cy == 1582, january_jd(1583, True), end)
year = cy + (jd - start) / (end - start)
bucket = 1550 + 100 * ((cy - 1550) // 100)
centuries = list(range(1550, 2650, 100))
# Slopes use a uniform Julian year; labels and Delta-T use civil fractional years.
x = (jd - julian_day(2100, 1, 1)) / 365.25
aya = np.array([ayanamsha(float(j)) for j in jd])
def pa(j):
    t = (np.asarray(j) - 2451545.) / 36525.
    return np.polynomial.polynomial.polyval(
        t, [0, 5028.796195, 1.1054348, .00007964, -.000023857, -.0000000383]
    ) / 3600
zero = KALI_EPOCH_JD + 3600 * SIDEREAL_YEAR_DAYS
prec = pa(jd) - pa(zero)
frame = aya - prec
ss = {}
for body in BODIES:
    sidereal = np.array([
        mean_longitude("Moon_node", float(j)) if body == "Rahu"
        else true_longitude_full(body, float(j))["true_longitude"] for j in jd
    ])
    ss[body] = (sidereal + aya) % 360
kernel = SPK.open(str(kernel_path))
residual = {}
try:
    for variant in ("naive", "deltat"):
        tt = jd if variant == "naive" else jd - 75.7873 / 360 + delta_t(year) / 86400
        ref = references(kernel, tt)
        residual[variant] = {b: wrap(ss[b] - ref[b]) for b in BODIES}
finally:
    kernel.close()
def stats(a):
    i = int(np.argmax(np.abs(a)))
    return [len(a), float(np.mean(a)), rms(a), float(abs(a[i])), float(a[i])]
summary = {
    v: {(c, b): stats(residual[v][b][bucket == c]) for c in centuries for b in BODIES}
    for v in residual
}
fit = {}
remainder = {}
for b in BODIES:
    slope, offset = np.polyfit(x, residual["deltat"][b] - frame, 1)
    remainder[b] = residual["deltat"][b] - frame - offset - slope * x
    fit[b] = [float(slope * 3600), float(offset), rms(remainder[b])]
joint = {}
w = 2 * np.pi * x / 883
design = np.column_stack([np.ones(len(jd)), x, np.sin(w), np.cos(w)])
for b in ("Jupiter", "Saturn"):
    beta = np.linalg.lstsq(design, residual["deltat"][b] - frame, rcond=None)[0]
    joint[b] = {"drift": float(beta[1] * 3600),
                "amplitude_arcmin": float(np.hypot(beta[2], beta[3]) * 60),
                "rms": rms(residual["deltat"][b] - frame - design @ beta)}
elong = wrap(residual["deltat"]["Moon"] - residual["deltat"]["Sun"])
ss_tithi = np.floor(((ss["Moon"] - ss["Sun"]) % 360) / 12).astype(int)
ref_tithi = np.floor(((ref["Moon"] - ref["Sun"]) % 360) / 12).astype(int)
diagnostics = {
    "elongation_mae": float(np.mean(np.abs(elong))),
    "elongation_max": float(np.max(np.abs(elong))),
    "mean_rate_proxy_hours": float(np.mean(np.abs(elong)) / 12.19 * 24),
    "tithi_index_differences": int(np.sum(ss_tithi != ref_tithi)),
    "tithi_max_circular_difference": int(np.max(np.abs((ss_tithi-ref_tithi+15) % 30-15))),
    "venus_fraction_over_10": float(np.mean(np.abs(remainder["Venus"]) > 10)),
    "rahu_smoothed_rms": rms(np.convolve(residual["deltat"]["Rahu"], np.ones(17)/17, mode="valid")),
    "joint_883_year": joint,
    "detrended_century_rms": {b: [rms(remainder[b][bucket == c]) for c in centuries] for b in BODIES},
    "century_means": {b: [summary["deltat"][c, b][1] for c in centuries] for b in BODIES},
}
tables = {}
def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |",
                       "| " + " | ".join(["---"] * len(headers)) + " |"] +
                      ["| " + " | ".join(map(str, row)) + " |" for row in rows])
for number, col in [(2, 2), (3, 3)]:
    tables[str(number)] = table(["Century"] + BODIES, [
        [f"{c}-{c+99}"] + [f'{summary["deltat"][c,b][col]:.2f}' for b in BODIES]
        for c in centuries])
tables["4"] = table(
    ["Body", "naive RMS", "deltat RMS", "naive minus deltat", "deltat precession-corrected RMS"],
    [[b, f'{rms(residual["naive"][b]):.2f}', f'{rms(residual["deltat"][b]):.2f}',
      f'{rms(residual["naive"][b])-rms(residual["deltat"][b]):+.2f}',
      f'{rms(residual["deltat"][b]-frame):.2f}'] for b in BODIES])
predicted = [-8.5, -8.0, -27.3, 20.9, -17.7, 6.8, -26.8, 9.5]
tables["5"] = table(
    ["Body", "Drift (arcsec/Julian year)", "Offset at 2100-01-01 (deg)",
     "Detrended RMS (deg)", "Predicted drift, Table 1", "Measured minus predicted"],
    [[b, f"{fit[b][0]:.2f}", f"{fit[b][1]:.3f}", f"{fit[b][2]:.3f}",
      f"{p:+.1f}", f"{fit[b][0]-p:+.1f}"] for b,p in zip(BODIES,predicted)])
selected = [0, int(np.argmin(abs(jd-julian_day(2100,1,1)))),
            int(np.argmax(aya)), int(np.argmin(abs(jd-julian_day(2400,1,1)))), len(jd)-1]
def date_label(i):
    y,m,d,f = from_julian_day(float(jd[i]))
    return f"{y:04d}-{m:02d}-{d:02d}" + (" (Julian)" if y < 1582 else "")
tables["6"] = table(["Civil date", "SS ayanamsha", "IAU 2006 precession", "SS minus reference"],
    [[date_label(i), f"{aya[i]:.3f}", f"{prec[i]:.3f}", f"{frame[i]:+.3f}"] for i in selected])
provenance = {
    "kernel_sha256": digest, "epochs": len(jd),
    "grid_sha256": hashlib.sha256(jd.astype("<f8").tobytes()).hexdigest(),
    "python": platform.python_version(),
    "packages": {p: importlib.metadata.version(p) for p in ["numpy", "jplephem"]},
    "source_sha256": {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [
        "src/suryasiddhanta/ch01_mean_motions.py", "src/suryasiddhanta/ch02_true_places.py",
        "docs/evaluation/validation/kernel_audit.py", "docs/evaluation/validation/numerics_audit.py",
        "docs/evaluation/regenerate_paper.py",
        "docs/evaluation/paper/surya-siddhanta-vs-de440.md"]},
}
commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
provenance["git_commit"] = commit.stdout.strip() if commit.returncode == 0 else None
print(json.dumps({"provenance": provenance, "tables": tables, "diagnostics": diagnostics}, indent=2))
if "--write" in sys.argv:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = ROOT / "docs/evaluation/regenerated"
    out.mkdir(parents=True, exist_ok=True)
    def save_csv(name, headers, rows):
        with (out/name).open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
    for v in residual:
        save_csv(f"residuals_{v}.csv", ["jd","year","body","residual_deg"],
                 ((f"{jd[i]:.6f}", f"{year[i]:.8f}", b, f"{residual[v][b][i]:.9f}")
                  for b in BODIES for i in range(len(jd))))
        save_csv(f"century_{v}.csv",
                 ["century_start_year","body","n","mean_deg","rms_deg","max_abs_deg","max_signed_deg"],
                 ([c,b]+summary[v][c,b] for c in centuries for b in BODIES))
    save_csv("ayanamsha_vs_precession.csv",
             ["jd","year","ss_ayanamsha_deg","true_precession_deg","difference_deg"],
             zip(jd,year,aya,prec,frame))
    for b in BODIES:
        fig,ax = plt.subplots(figsize=(10,4))
        for v in residual:
            ax.plot(year, residual[v][b], lw=.45, alpha=.75, label=v)
        ax.set(xlabel="Civil year", ylabel="SS minus DE440 (degrees)", title=b)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out/f"error_{b.lower()}.png", dpi=180)
        plt.close(fig)
    fig,ax = plt.subplots(figsize=(10,4))
    for values,label in [(aya,"SS ayanamsha"),(prec,"IAU 2006 precession"),(frame,"Difference")]:
        ax.plot(year,values,label=label)
    ax.set(xlabel="Civil year", ylabel="Degrees")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out/"ayanamsha_vs_precession.png",dpi=180)
    plt.close(fig)
    for v in residual:
        fig,ax = plt.subplots(figsize=(10,5))
        grid = np.array([[summary[v][c,b][2] for b in BODIES] for c in centuries])
        im = ax.imshow(grid, aspect="auto", vmin=0, vmax=21)
        ax.set_xticks(range(8), BODIES)
        ax.set_yticks(range(11), [f"{c}-{c+99}" for c in centuries])
        ax.set(title=f"RMS by civil century: {v}")
        fig.colorbar(im, ax=ax, label="Degrees")
        fig.tight_layout()
        fig.savefig(out/f"century_heatmap_{v}.png",dpi=180)
        plt.close(fig)
    (out/"tables_regenerated.md").write_text(
        "\n\n".join(f"## Table {n}\n\n{t}" for n,t in tables.items())+"\n",encoding="utf-8")
    (out/"diagnostics.json").write_text(json.dumps(diagnostics,indent=2)+"\n",encoding="utf-8")
    provenance["output_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(out.iterdir()) if p.suffix in [".csv",".png"] or p.name in ["tables_regenerated.md","diagnostics.json"]}
    (out/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n",encoding="utf-8")
    print("Wrote",out)
