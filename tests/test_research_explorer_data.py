"""Validate every explorer group against the existing paper tables and samples."""
import csv
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_all_research_groups_preserve_saved_evidence():
    data = json.loads((ROOT / "frontend/src/pages/research/research-data.json").read_text(encoding="utf-8"))
    assert len(data["series"]) == 16
    for variant in ("naive", "deltat"):
        source = ROOT / f"docs/evaluation/residuals_{variant}.csv"
        assert data["sources"][variant]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        with (ROOT / f"docs/evaluation/century_{variant}.csv").open(newline="") as f:
            table = {(r["body"], int(r["century_start_year"])): r for r in csv.DictReader(f)}
        for series in [s for s in data["series"] if s["variant"] == variant]:
            assert sum(w["n"] for w in series["windows"]) == 40176
            assert len(series["windows"]) == 11
            for window in series["windows"]:
                row = table[series["body"], window["start"]]
                assert window["n"] == int(row["n"])
                for name, column in [("mean", "mean_deg"), ("rms", "rms_deg"), ("max_abs", "max_abs_deg")]:
                    assert window[name] == pytest.approx(float(row[column]), abs=2e-8)
                assert len(window["bins"]) == 20
                assert sum(b["n"] for b in window["bins"]) == window["n"]
                assert max(max(abs(b["min"]), abs(b["max"])) for b in window["bins"]) == window["max_abs"]
