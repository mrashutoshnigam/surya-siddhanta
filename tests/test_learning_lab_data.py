"""Check the teaching artifact against its research source, not rounded UI labels."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mars_learning_data_preserves_research_evidence():
    result = json.loads((ROOT / "frontend/src/pages/learn/mars-evaluation.json").read_text(encoding="utf-8"))
    source = ROOT / "docs/evaluation/residuals_deltat.csv"
    with source.open(newline="", encoding="utf-8") as stream:
        rows = [r for r in csv.DictReader(stream) if r["body"] == "Mars"]
    assert result["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert sum(w["n"] for w in result["windows"]) == len(rows) == 40176
    assert len(result["windows"]) == 11
    for window in result["windows"]:
        values = [float(r["residual_deg"]) for r in rows
                  if window["start"] <= float(r["year"]) < window["start"] + 100]
        assert window["n"] == len(values)
        assert math.isclose(window["rms"], math.sqrt(sum(v*v for v in values)/len(values)), abs_tol=1e-9)
        assert math.isclose(window["mean"], sum(values)/len(values), abs_tol=1e-9)
        assert window["max_abs"] == max(map(abs, values))
        assert min(b["min"] for b in window["bins"]) == min(values)
        assert max(b["max"] for b in window["bins"]) == max(values)
        assert sum(b["n"] for b in window["bins"]) == len(values)
