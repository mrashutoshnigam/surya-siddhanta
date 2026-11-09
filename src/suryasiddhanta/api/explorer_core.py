"""Independent historical directions and modern geometric ephemeris adapters.

Nothing in this module changes the chapter implementations. Scene interpolation
is bounded and explicitly separate from the exact numerical snapshot.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import math
import os
from pathlib import Path
import threading

import numpy as np

from suryasiddhanta.ch01_mean_motions import jd_from_ut, mean_longitude, moon_node_longitude
from suryasiddhanta.ch02_true_places import planet_latitude, true_longitude_full
from suryasiddhanta.ch12_cosmography import orbit_diameter

from .explorer_catalog import HISTORICAL, MODERN
from .explorer_schemas import MIN_TIME, MAX_TIME

KERNEL_SHA256 = "a4ce9bf9b3282becc9f4b2ac3cebe03a2ae7599981aabd7265fd8482fff7c4b5"
DEFAULT_KERNEL = Path(__file__).resolve().parents[3] / "paper/data/kernels/de440.bsp"
KERNEL_HELP = "Modern astronomy needs verified DE440 data. Run python docker/fetch_ephemeris.py, or set SS_EPHEMERIS_PATH to that file."
_TRAJECTORY_LOCK = threading.Lock()
_UTC_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class EphemerisUnavailable(ValueError):
    pass


def kernel_path():
    return Path(os.environ.get("SS_EPHEMERIS_PATH", DEFAULT_KERNEL)).resolve()


@lru_cache(maxsize=2)
def _load_kernel(path: str, size: int, modified: int):
    try:
        from skyfield.api import load_file
    except ImportError as error:
        raise EphemerisUnavailable("Install the astronomy extra: pip install -e \".[astronomy]\". " + KERNEL_HELP) from error
    with open(path, "rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != KERNEL_SHA256:
        raise EphemerisUnavailable("DE440 checksum verification failed. " + KERNEL_HELP)
    return load_file(path)


def kernel():
    path = kernel_path()
    try:
        stat = path.stat()
        return _load_kernel(str(path), stat.st_size, stat.st_mtime_ns)
    except OSError as error:
        raise EphemerisUnavailable(KERNEL_HELP) from error


@lru_cache(maxsize=1)
def timescale():
    from skyfield.api import load
    # No network fetches: the package supplies leap-second and Delta-T tables.
    return load.timescale(builtin=True)


def modern_status():
    try:
        kernel()
        return True, None
    except EphemerisUnavailable as error:
        return False, str(error)


def utc_iso(timestamp):
    return utc_datetime(timestamp).isoformat().replace("+00:00", "Z")


def utc_datetime(timestamp):
    # Windows' C runtime rejects negative POSIX timestamps in fromtimestamp().
    # Calendar arithmetic supports the entire advertised interval everywhere.
    return _UTC_EPOCH + timedelta(seconds=timestamp)


def metadata(model):
    if model == "historical":
        return dict(model=model, origin="Earth", frame="SS sidereal ecliptic", units="yojanas (fixed model radii)",
            velocity_units="yojanas/day", time_scale="Ujjain mean time (converted from UTC)",
            provenance="SS Chapters 1–2 directions; Chapter 12 mean geocentric radii. Paths are directions at illustrative distances, not physical trajectories. Velocities and longitude motion are 30-minute finite-difference estimates of the rounded chapter results.")
    return dict(model=model, origin="Sun", frame="J2000 ecliptic", units="km", velocity_units="km/day",
        time_scale="TDB (converted from UTC)",
        provenance="JPL DE440; SHA-256 " + KERNEL_SHA256 + ". Geometric simultaneous positions, not apparent sky directions. Skyfield bundled time tables; historical/future UTC and Earth rotation carry time-model uncertainty.")


@lru_cache(maxsize=16)
def _radius(body):
    return orbit_diameter("Moon" if body in ("Rahu", "Ketu") else body) / 2


def _historical_positions(timestamp):
    jd = jd_from_ut(timestamp / 86400 + 2440587.5)
    positions, details = {}, {}
    for body in HISTORICAL:
        if body == "Earth":
            lon, lat, radius, mean = 0., 0., 0., 0.
        elif body in ("Rahu", "Ketu"):
            lon = (moon_node_longitude(jd) + (180 if body == "Ketu" else 0)) % 360
            lat, radius, mean = 0., _radius(body), lon
        else:
            lon = true_longitude_full(body, jd)["true_longitude"]
            lat, radius, mean = planet_latitude(body, jd) / 60, _radius(body), mean_longitude(body, jd)
        a, b = math.radians(lon), math.radians(lat)
        positions[body] = [radius * math.cos(b) * math.cos(a), radius * math.cos(b) * math.sin(a), radius * math.sin(b)]
        details[body] = dict(longitude_deg=lon, latitude_deg=lat, mean_longitude_deg=mean, distance=radius,
            target_kind="direction_marker" if body in ("Rahu", "Ketu") else "body_centre")
    return positions, details


def _modern_states(timestamps):
    # kernel() translates missing optional dependencies into the public 503
    # error before any other Skyfield import can bypass that availability gate.
    ephemeris = kernel()
    from skyfield.framelib import ecliptic_J2000_frame
    instants = [utc_datetime(t) for t in timestamps]
    t = timescale().from_datetimes(instants)
    sun = ephemeris["sun"]
    targets = {"Sun": "sun", "Earth": "earth", "Moon": "moon", "Mercury": "mercury", "Venus": "venus",
        "Mars": "mars barycenter", "Jupiter": "jupiter barycenter", "Saturn": "saturn barycenter",
        "Uranus": "uranus barycenter", "Neptune": "neptune barycenter"}
    rows = [dict() for _ in timestamps]
    for body in MODERN:
        p, v = (ephemeris[targets[body]] - sun).at(t).frame_xyz_and_velocity(ecliptic_J2000_frame)
        xyz, velocity = p.km.T, v.km_per_s.T * 86400
        for i in range(len(timestamps)):
            x, y, z = xyz[i]
            r = float(np.linalg.norm(xyz[i]))
            rows[i][body] = dict(position=xyz[i].tolist(), velocity=velocity[i].tolist(), distance=r,
                longitude_deg=math.degrees(math.atan2(y, x)) % 360,
                latitude_deg=math.degrees(math.atan2(z, math.hypot(x, y))),
                target_kind="system_barycentre" if "barycenter" in targets[body] else "body_centre")
    return rows


def state_at(model, timestamp):
    if model == "modern":
        return _modern_states([timestamp])[0]
    positions, details = _historical_positions(timestamp)
    # Small symmetric difference preserves the chapter's piecewise model rather
    # than pretending its mean motion is its instantaneous true motion.
    # The public chapter result is rounded to 0.0001 degrees. A 30-minute
    # baseline avoids amplifying that quantisation into noisy tangents.
    before, _ = _historical_positions(timestamp - 900)
    after, _ = _historical_positions(timestamp + 900)
    for body, p in positions.items():
        row = details[body]
        row["position"] = p
        row["velocity"] = ((np.array(after[body]) - before[body]) * 48).tolist()
        x, y, _ = p
        vx, vy, _ = row["velocity"]
        row["motion_deg_per_day"] = math.degrees((x * vy - y * vx) / (x*x + y*y)) if x*x+y*y else 0
    return details


def snapshot(model, timestamp):
    result = dict(**metadata(model), instant=utc_iso(timestamp), timestamp=timestamp, bodies=state_at(model, timestamp))
    if model == "modern":
        result["jd_tdb"] = float(timescale().from_datetime(utc_datetime(timestamp)).tdb)
    else:
        result["jd_ujjain"] = jd_from_ut(timestamp / 86400 + 2440587.5)
    return result


def _sample(timestamp, rows):
    return dict(timestamp=timestamp, positions={b: r["position"] for b, r in rows.items()},
        velocities={b: r["velocity"] for b, r in rows.items()})


def interpolate(a, b, timestamp):
    """Cubic Hermite, matching the frontend's independent implementation."""
    duration = (b["timestamp"] - a["timestamp"]) / 86400
    u = (timestamp - a["timestamp"]) / (b["timestamp"] - a["timestamp"])
    h00, h10, h01, h11 = 2*u**3-3*u*u+1, u**3-2*u*u+u, -2*u**3+3*u*u, u**3-u*u
    return {body: (h00*np.array(p) + h10*duration*np.array(a["velocities"][body])
        + h01*np.array(b["positions"][body]) + h11*duration*np.array(b["velocities"][body])).tolist()
        for body, p in a["positions"].items()}


def _acceptable(predicted, actual, model):
    for body, p in predicted.items():
        q = np.array(actual[body]["position"])
        p = np.array(p)
        if model == "modern" and body == "Moon":
            p -= np.array(predicted["Earth"])
            q -= np.array(actual["Earth"]["position"])
        if np.linalg.norm(q) == 0:
            continue
        angle = math.atan2(np.linalg.norm(np.cross(p, q)), np.dot(p, q)) * 206264.806
        # SS quantisation alone spans 0.36 arcsec; a smaller target cannot
        # converge at rounding boundaries. Keep margin below the 1" contract.
        if angle > (.65 if model == "historical" else .2) or (model == "modern" and np.linalg.norm(p-q) > 1):
            return False
    return True


@lru_cache(maxsize=12)
def _trajectory(model, start, days, kernel_identity):
    end = start + days * 86400
    timestamps = np.linspace(start, end, max(2, math.ceil(days * 4) + 1)).tolist()
    cache = {}

    def fill(points):
        missing = [t for t in points if t not in cache]
        states = _modern_states(missing) if model == "modern" and missing else [state_at(model, t) for t in missing]
        cache.update(zip(missing, states))

    fill(timestamps)
    samples = []

    def refine(left, right, depth=0):
        a, b = _sample(left, cache[left]), _sample(right, cache[right])
        checks = [left + (right-left)*u for u in (.25, .5, .75)]
        fill(checks)
        if all(_acceptable(interpolate(a, b, t), cache[t], model) for t in checks):
            samples.append(a)
            return
        # Historical inverse-sine quadrant cusps can need sub-second samples
        # inside an otherwise smooth month. Bound total samples independently.
        if depth >= 24 or len(samples) >= 8191:
            raise ValueError("This window needs too many samples; choose a shorter interval")
        middle = checks[1]
        refine(left, middle, depth+1)
        refine(middle, right, depth+1)

    for left, right in zip(timestamps, timestamps[1:]):
        refine(left, right)
    samples.append(_sample(end, cache[end]))
    return dict(**metadata(model), start=utc_iso(start), end=utc_iso(end), samples=samples,
        interpolation="cubic Hermite; velocities per day", angular_tolerance_arcsec=1.)


def trajectory(model, start, days):
    identity = "historical"
    if model == "modern":
        kernel()  # Check availability even if this trajectory is cached.
        stat = kernel_path().stat()
        identity = (str(kernel_path()), stat.st_mtime_ns, stat.st_size)
    # A single flight bounds memory/CPU under concurrent requests; the LRU holds
    # at most twelve bounded windows and never caches an unavailable kernel.
    with _TRAJECTORY_LOCK:
        return _trajectory(model, start, days, identity)
