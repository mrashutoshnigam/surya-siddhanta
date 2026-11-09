"""Explorer contracts: UTC/frame fidelity, bounded work, and offline ephemeris."""
from datetime import datetime, timezone
import builtins
from pathlib import Path
import json
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from suryasiddhanta.api.main import app
from suryasiddhanta.ch01_mean_motions import jd_from_ut, julian_day
from suryasiddhanta.ch02_true_places import true_longitude_full, planet_latitude

client = TestClient(app)
INSTANT = "2024-04-09T00:00:00Z"


def snapshot(model="historical", instant=INSTANT):
    response = client.post("/explorer/snapshot", json={"model": model, "instant": instant})
    assert response.status_code == 200, response.text
    return response.json()


def test_historical_uses_ujjain_jd_and_arcminute_latitude():
    result = snapshot()
    jd = jd_from_ut(julian_day(2024, 4, 9, gregorian=True))
    assert result["frame"] == "SS sidereal ecliptic"
    assert result["origin"] == "Earth"
    assert result["bodies"]["Earth"]["position"] == [0, 0, 0]
    for body in ("Sun", "Moon", "Mars", "Mercury", "Venus", "Jupiter", "Saturn"):
        row = result["bodies"][body]
        assert row["longitude_deg"] == pytest.approx(true_longitude_full(body, jd)["true_longitude"], abs=1e-8)
        assert row["latitude_deg"] == pytest.approx(planet_latitude(body, jd) / 60, abs=1e-8)
    assert "Uranus" not in result["bodies"]
    assert (result["bodies"]["Ketu"]["longitude_deg"] - result["bodies"]["Rahu"]["longitude_deg"]) % 360 == pytest.approx(180)


def test_equivalent_offsets_represent_the_same_instant():
    a, b = snapshot(), snapshot(instant="2024-04-09T05:30:00+05:30")
    assert a["bodies"] == b["bodies"]
    assert a["instant"] == b["instant"]


@pytest.mark.parametrize("instant", ["1549-12-31T23:59:59Z", "2650-01-01T00:00:00Z", "2024-04-09", "nonsense"])
def test_dates_outside_contract_rejected(instant):
    assert client.post("/explorer/snapshot", json={"model": "historical", "instant": instant}).status_code == 422


def test_model_and_window_validation():
    assert client.post("/explorer/snapshot", json={"model": "invented", "instant": INSTANT}).status_code == 422
    for days in (0, -1, 65, 1e-20):
        assert client.post("/explorer/trajectory", json={"model": "historical", "start": INSTANT, "days": days}).status_code == 422
    assert client.post("/explorer/trajectory", json={"model": "historical", "start": "2649-12-31T00:00:00Z", "days": 2}).status_code == 422


def test_historical_retrograde_and_wrap():
    first = snapshot(instant="2025-01-01T00:00:00Z")["bodies"]["Mars"]["longitude_deg"]
    second = snapshot(instant="2025-01-02T00:00:00Z")["bodies"]["Mars"]["longitude_deg"]
    assert (second - first + 180) % 360 - 180 < 0
    assert all(0 <= b["longitude_deg"] < 360 for b in snapshot()["bodies"].values())


def test_historical_window_handles_sharp_mercury_correction():
    # The chapter's inverse sine changes very sharply near this quadrant.
    # A shallow recursion limit used to reject a whole month of valid dates.
    response = client.post("/explorer/trajectory", json={"model":"historical","start":"2024-12-13T00:00:00Z","days":32})
    assert response.status_code == 200, response.text
    from suryasiddhanta.api.explorer_core import interpolate, state_at
    frames = response.json()["samples"]
    assert len(frames) <= 8193
    critical = datetime(2025,1,1,5,10,55,tzinfo=timezone.utc).timestamp()
    for offset in np.linspace(-2,2,21):
        t = critical + float(offset)
        a,b = next((a,b) for a,b in zip(frames,frames[1:]) if a["timestamp"] <= t <= b["timestamp"])
        p=np.array(interpolate(a,b,t)["Mercury"])
        q=np.array(state_at("historical",t)["Mercury"]["position"])
        error=math.atan2(np.linalg.norm(np.cross(p,q)),np.dot(p,q))*206264.806
        assert error < 1


def test_missing_kernel_does_not_break_historical(monkeypatch, tmp_path):
    monkeypatch.setenv("SS_EPHEMERIS_PATH", str(tmp_path / "missing.bsp"))
    catalog = client.get("/explorer/catalog").json()
    assert not catalog["modern_available"]
    assert "fetch_ephemeris" in catalog["modern_unavailable_reason"]
    assert client.post("/explorer/snapshot", json={"model": "modern", "instant": INSTANT}).status_code == 503
    snapshot()


@pytest.mark.parametrize("endpoint", ["snapshot", "trajectory", "chat"])
def test_missing_astronomy_extra_returns_503_with_guidance(monkeypatch, tmp_path, endpoint):
    # Simulate an API-only installation even on a machine with Skyfield already
    # imported. A real path gets past stat() so dependency handling is exercised.
    from suryasiddhanta.api import explorer_core
    kernel_file = tmp_path / "de440.bsp"
    kernel_file.write_bytes(b"dependency check runs before kernel verification")
    monkeypatch.setenv("SS_EPHEMERIS_PATH", str(kernel_file))
    explorer_core._load_kernel.cache_clear()
    original_import = builtins.__import__

    def without_astronomy(name, *args, **kwargs):
        if name == "skyfield" or name.startswith("skyfield."):
            raise ModuleNotFoundError("No module named 'skyfield'", name="skyfield")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_astronomy)
    api_client = TestClient(app, raise_server_exceptions=False)
    if endpoint == "chat":
        response = api_client.post("/chat", json={"message": "Explain this scene", "explorer": {
            "model": "modern", "instant": INSTANT, "body": "Earth"}})
    elif endpoint == "trajectory":
        response = api_client.post("/explorer/trajectory", json={"model": "modern", "start": INSTANT, "days": 1})
    else:
        response = api_client.post("/explorer/snapshot", json={"model": "modern", "instant": INSTANT})
    assert response.status_code == 503, response.text
    assert "astronomy" in response.json()["detail"]
    catalog = api_client.get("/explorer/catalog").json()
    assert not catalog["modern_available"]
    assert "astronomy" in catalog["modern_unavailable_reason"]
    assert api_client.post("/explorer/snapshot", json={"model": "historical", "instant": INSTANT}).status_code == 200


def test_catalog_facts_and_model_membership():
    data = client.get("/explorer/catalog").json()
    assert data["bodies"]["Venus"]["rotation_hours"] < 0
    assert data["bodies"]["Uranus"]["models"] == ["modern"]
    assert data["bodies"]["Rahu"]["kind"] == "node"
    assert all(b["sources"] for b in data["bodies"].values())


@pytest.mark.parametrize("model", ["historical", "modern"])
@pytest.mark.parametrize("instant", ["1550-01-01T00:00:00Z", "1850-01-01T00:00:00Z", "2649-12-31T23:59:59Z"])
def test_supported_calendar_range_on_windows(model, instant):
    if model == "modern" and not Path("paper/data/kernels/de440.bsp").exists():
        pytest.skip("Optional kernel not installed")
    result = snapshot(model, instant)
    assert result["instant"].startswith(instant[:19])
    assert all(math.isfinite(value) for body in result["bodies"].values() for value in body["position"])


def test_pre_unix_epoch_trajectory():
    response=client.post("/explorer/trajectory",json={"model":"historical","start":"1550-01-01T00:00:00Z","days":1})
    assert response.status_code==200,response.text
    assert response.json()["start"]=="1550-01-01T00:00:00Z"


@pytest.mark.skipif(not Path("paper/data/kernels/de440.bsp").exists(), reason="Optional DE440 kernel not installed")
def test_modern_vectors_against_direct_spk_reference():
    # Independent reader (jplephem), hand-written time and fixed obliquity matrix.
    from jplephem.spk import SPK
    result = snapshot("modern")
    jd_tdb = result["jd_tdb"]
    # SPICE ECLIPJ2000 uses IAU 1980 J2000 obliquity, not ecliptic-of-date.
    eps = math.radians(84381.448 / 3600)
    matrix = np.array([[1, 0, 0], [0, math.cos(eps), math.sin(eps)], [0, -math.sin(eps), math.cos(eps)]])
    with SPK.open("paper/data/kernels/de440.bsp") as kernel:
        sun = kernel[0, 10].compute(jd_tdb)
        for body, target in (("Mars", 4), ("Jupiter", 5), ("Saturn", 6), ("Uranus", 7), ("Neptune", 8)):
            expected = matrix @ (kernel[0, target].compute(jd_tdb) - sun)
            assert result["bodies"][body]["position"] == pytest.approx(expected, abs=.1, rel=0)
            assert result["bodies"][body]["target_kind"] == "system_barycentre"
        earth = kernel[0, 3].compute(jd_tdb) + kernel[3, 399].compute(jd_tdb)
        moon = kernel[0, 3].compute(jd_tdb) + kernel[3, 301].compute(jd_tdb)
        assert result["bodies"]["Earth"]["position"] == pytest.approx(matrix @ (earth - sun), abs=.1, rel=0)
        assert result["bodies"]["Moon"]["position"] == pytest.approx(matrix @ (moon - sun), abs=.1, rel=0)
    assert result["bodies"]["Sun"]["position"] == [0, 0, 0]


@pytest.mark.skipif(not Path("paper/data/kernels/de440.bsp").exists(), reason="Optional DE440 kernel not installed")
def test_modern_position_and_velocity_against_saved_offline_fixtures():
    fixture=json.loads((Path(__file__).parent/"fixtures/explorer_de440.json").read_text())
    for epoch in fixture["epochs"]:
        result=snapshot("modern",epoch["instant"])
        assert result["jd_tdb"]==pytest.approx(epoch["jd_tdb"],abs=1e-9,rel=0)
        for body,expected in epoch["bodies"].items():
            assert result["bodies"][body]["position"]==pytest.approx(expected["position"],abs=.1,rel=0)
            assert result["bodies"][body]["velocity"]==pytest.approx(expected["velocity"],abs=.01,rel=0)


@pytest.mark.parametrize("model", ["historical", "modern"])
def test_trajectory_hermite_stays_within_one_arcsecond(model):
    if model == "modern" and not Path("paper/data/kernels/de440.bsp").exists():
        pytest.skip("Optional kernel not installed")
    from suryasiddhanta.api.explorer_core import interpolate, state_at
    from suryasiddhanta.api.explorer_schemas import parse_instant
    # Crosses a Sun longitude wrap and historical piecewise sine-table knots.
    response = client.post("/explorer/trajectory", json={"model": model, "start": "2024-04-12T00:00:00Z", "days": 4})
    assert response.status_code == 200, response.text
    frames = response.json()["samples"]
    assert frames[0]["timestamp"] < frames[-1]["timestamp"]
    assert len(frames) <= 8193
    for a, b in zip(frames, frames[1:]):
        for fraction in (.13, .37, .71, .91):
            timestamp = a["timestamp"] + (b["timestamp"] - a["timestamp"]) * fraction
            exact = state_at(model, timestamp)
            for body, p in interpolate(a, b, timestamp).items():
                q = np.array(exact[body]["position"])
                p = np.array(p)
                # For the Moon, test its Earth-relative direction too.
                if model == "modern" and body == "Moon":
                    p -= np.array(interpolate(a, b, timestamp)["Earth"])
                    q -= np.array(exact["Earth"]["position"])
                if np.linalg.norm(q) == 0:
                    continue
                error = math.atan2(np.linalg.norm(np.cross(p, q)), np.dot(p, q)) * 206264.806
                assert error < 1, (model, body, error)
