"""Explicit time and frame contracts for the beginner explorer."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

Model = Literal["historical", "modern"]
MIN_TIME = datetime(1550, 1, 1, tzinfo=timezone.utc).timestamp()
MAX_TIME = datetime(2650, 1, 1, tzinfo=timezone.utc).timestamp() - .001


def parse_instant(value: str) -> datetime:
    """Require a real ISO instant with a zone; never infer the server zone."""
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("Include a UTC offset or Z in the instant")
    moment = moment.astimezone(timezone.utc)
    if not MIN_TIME <= moment.timestamp() <= MAX_TIME:
        raise ValueError("Choose an instant in 1550–2649 CE")
    return moment


class SnapshotIn(BaseModel):
    model: Model = "historical"
    instant: str = Field(max_length=60)

    @field_validator("instant")
    @classmethod
    def valid_instant(cls, value: str) -> str:
        return parse_instant(value).isoformat()


class TrajectoryIn(BaseModel):
    model: Model = "historical"
    start: str = Field(max_length=60)
    days: float = Field(default=32, ge=1 / 86400, le=64, allow_inf_nan=False)

    @field_validator("start")
    @classmethod
    def valid_start(cls, value: str) -> str:
        return parse_instant(value).isoformat()

    @model_validator(mode="after")
    def valid_end(self):
        if parse_instant(self.start).timestamp() + self.days * 86400 > MAX_TIME:
            raise ValueError("The whole trajectory must lie within 1550–2649 CE")
        return self


class ExplorerContextIn(SnapshotIn):
    body: str = Field(default="Earth", max_length=20)
    beginner: bool = True


class Source(BaseModel):
    label: str
    url: str


class BodyInfo(BaseModel):
    id: str
    sanskrit: str
    kind: Literal["star", "planet", "moon", "node"]
    models: List[Model]
    introduction: str
    historical: Optional[str] = None
    rotation_hours: Optional[float] = None
    tilt_deg: Optional[float] = None
    diameter_km: Optional[float] = None
    orbital_days: Optional[float] = None
    color: str
    texture: Optional[str] = None
    sources: List[Source]


class CatalogOut(BaseModel):
    bodies: Dict[str, BodyInfo]
    modern_available: bool
    modern_unavailable_reason: Optional[str] = None
    min_instant: str
    max_instant: str
    kernel_sha256: str


class BodyState(BaseModel):
    position: List[float]
    velocity: List[float]
    longitude_deg: float
    latitude_deg: float
    distance: float
    target_kind: Literal["body_centre", "system_barycentre", "direction_marker"]
    mean_longitude_deg: Optional[float] = None
    motion_deg_per_day: Optional[float] = None


class FrameMetadata(BaseModel):
    model: Model
    origin: str
    frame: str
    units: str
    velocity_units: str
    time_scale: str
    provenance: str


class SnapshotOut(FrameMetadata):
    instant: str
    timestamp: float
    jd_tdb: Optional[float] = None
    jd_ujjain: Optional[float] = None
    bodies: Dict[str, BodyState]


class Sample(BaseModel):
    timestamp: float
    positions: Dict[str, List[float]]
    velocities: Dict[str, List[float]]


class TrajectoryOut(FrameMetadata):
    start: str
    end: str
    samples: List[Sample]
    interpolation: str = "cubic Hermite; velocities per day"
    angular_tolerance_arcsec: float = 1


class LessonSample(BaseModel):
    instant: str
    timestamp: float
    longitude_deg: float
    motion_deg_per_day: float


class MarsLessonOut(FrameMetadata):
    model: Literal['historical'] = 'historical'
    origin: Literal['Earth'] = 'Earth'
    body: Literal['Mars'] = 'Mars'
    longitude_units: Literal['degrees'] = 'degrees'
    motion_units: Literal['degrees/day'] = 'degrees/day'
    samples: List[LessonSample]
