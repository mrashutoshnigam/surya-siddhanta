"""Export a small, offline teaching view of the saved Mars evaluation.

Run from any directory: python docs/evaluation/export_learning_lab.py
No ephemeris is recomputed. Statistics use all source samples; the chart uses
annual min/max envelopes and means, rather than silently dropping extrema.
"""
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/evaluation/residuals_deltat.csv"
OUTPUT = ROOT / "frontend/src/pages/learn/mars-evaluation.json"


def build():
    years = defaultdict(list)
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["body"] == "Mars":
                years[math.floor(float(row["year"]))].append(float(row["residual_deg"]))
    windows = []
    for start in range(1550, 2650, 100):
        bins = []
        values = []
        for year in range(start, start + 100):
            sample = years[year]
            if not sample:
                raise ValueError(f"Missing Mars samples for {year}")
            values.extend(sample)
            bins.append({"year": year, "n": len(sample), "min": min(sample),
                         "max": max(sample), "mean": sum(sample) / len(sample)})
        windows.append({"start": start, "n": len(values),
                        "mean": sum(values) / len(values),
                        "rms": math.sqrt(sum(v*v for v in values) / len(values)),
                        "max_abs": max(map(abs, values)), "bins": bins})
    return {
        "body": "Mars", "source": "docs/evaluation/residuals_deltat.csv",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "variant": "deltat", "sampling_days": 10,
        "residual": "wrap(SS tropical longitude - DE440 longitude, -180, 180) degrees",
        "frame": "Geocentric geometric longitude; DE440 rotated to mean ecliptic of date. SS tropical = sidereal + SS ayanamsha.",
        "time": "DE440 TT = library JD - 75.7873/360 + Delta-T/86400; Espenak-Meeus Delta-T approximation.",
        "chart": "Annual minimum, maximum and mean of saved ten-day samples. Window statistics use all samples.",
        "windows": windows,
    }


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
