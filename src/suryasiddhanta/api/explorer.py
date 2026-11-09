"""Read-only explorer routes; no external requests or AI credentials needed."""
from fastapi import APIRouter, HTTPException
from functools import lru_cache

from .explorer_catalog import BODIES
from .explorer_core import EphemerisUnavailable, KERNEL_SHA256, modern_status, snapshot, trajectory
from .explorer_schemas import CatalogOut, MarsLessonOut, SnapshotIn, SnapshotOut, TrajectoryIn, TrajectoryOut, parse_instant

router = APIRouter(prefix="/explorer", tags=["explorer"])


@lru_cache(maxsize=1)
def mars_lesson():
    """Fixed daily exact evaluations; independent of optional modern data/AI."""
    start = parse_instant('2024-10-01T00:00:00Z').timestamp()
    end = parse_instant('2025-04-01T00:00:00Z').timestamp()
    samples = []
    for day in range(round((end - start) / 86400) + 1):
        value = snapshot('historical', start + day * 86400)
        body = value['bodies']['Mars']
        samples.append(dict(instant=value['instant'], timestamp=value['timestamp'],
            longitude_deg=body['longitude_deg'], motion_deg_per_day=body['motion_deg_per_day']))
    return {key: value[key] for key in ('model', 'origin', 'frame', 'units', 'velocity_units', 'time_scale', 'provenance')} | dict(body='Mars', samples=samples)


@router.get('/lessons/mars-retrograde', response_model=MarsLessonOut)
def get_mars_lesson():
    return mars_lesson()


@router.get("/catalog", response_model=CatalogOut)
def catalog():
    available, reason = modern_status()
    return dict(bodies=BODIES, modern_available=available, modern_unavailable_reason=reason,
        min_instant="1550-01-01T00:00:00Z", max_instant="2649-12-31T23:59:59.999Z", kernel_sha256=KERNEL_SHA256)


@router.post("/snapshot", response_model=SnapshotOut)
def get_snapshot(body: SnapshotIn):
    try:
        return snapshot(body.model, parse_instant(body.instant).timestamp())
    except EphemerisUnavailable as error:
        raise HTTPException(503, str(error)) from error


@router.post("/trajectory", response_model=TrajectoryOut)
def get_trajectory(body: TrajectoryIn):
    try:
        return trajectory(body.model, parse_instant(body.start).timestamp(), body.days)
    except EphemerisUnavailable as error:
        raise HTTPException(503, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
