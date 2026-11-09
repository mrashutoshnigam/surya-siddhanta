"""Create a compact explorer artifact from the two saved residual CSVs."""
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BODIES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu"]
OUTPUT = ROOT / "frontend/src/pages/research/research-data.json"


def build():
    series, sources = [], {}
    for variant in ("naive", "deltat"):
        source = ROOT / f"docs/evaluation/residuals_{variant}.csv"
        groups = defaultdict(list)
        with source.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                body = row["body"]
                year = math.floor(float(row["year"]))
                if body not in BODIES or not 1550 <= year < 2650:
                    raise ValueError("Unexpected body or date in research source")
                groups[body, year].append(float(row["residual_deg"]))
        sources[variant] = {"path": str(source.relative_to(ROOT)).replace("\\", "/"),
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        for body in BODIES:
            windows = []
            for start in range(1550, 2650, 100):
                values, bins = [], []
                for year in range(start, start + 100, 5):
                    sample = []
                    for y in range(year, year + 5):
                        if not groups[body, y]:
                            raise ValueError(f"Missing samples: {body}, {y}")
                        sample.extend(groups[body, y])
                    values.extend(sample)
                    bins.append({"year": year, "n": len(sample), "min": min(sample),
                                 "max": max(sample), "mean": math.fsum(sample) / len(sample)})
                windows.append({"start": start, "n": len(values),
                                "mean": math.fsum(values) / len(values),
                                "rms": math.sqrt(math.fsum(v*v for v in values)/len(values)),
                                "max_abs": max(map(abs, values)), "bins": bins})
            series.append({"body": body, "variant": variant, "windows": windows})
    return {"bodies": BODIES, "sources": sources, "sample_step_days": 10,
            "chart_bin_years": 5, "epochs_per_body": 40176,
            "residual": "SS tropical longitude minus DE440, wrapped to [-180,180) degrees",
            "frame": "Geocentric geometric longitude; reference rotated to mean ecliptic of date. SS tropical = sidereal + SS ayanamsha.",
            "time": {"naive": "Treat library JD directly as reference TT (diagnostic baseline).",
                     "deltat": "Reference TT = library JD - 75.7873/360 + Delta-T/86400; Espenak-Meeus approximation."},
            "series": series}


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(build(), separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
