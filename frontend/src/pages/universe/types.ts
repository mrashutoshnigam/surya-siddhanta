export type Model = "historical" | "modern";
export type Vector = [number, number, number];
export type Positions = Record<string, Vector>;
export interface CameraPose {position:Vector;target:Vector}
export interface Source { label: string; url: string }
export interface BodyInfo {
  id: string; sanskrit: string; kind: "star" | "planet" | "moon" | "node";
  models: Model[]; introduction: string; historical: string | null;
  rotation_hours: number | null; tilt_deg: number | null; diameter_km: number | null;
  orbital_days: number | null; color: string; texture: string | null; sources: Source[];
}
export interface Catalog {
  bodies: Record<string, BodyInfo>; modern_available: boolean;
  modern_unavailable_reason: string | null; min_instant: string; max_instant: string;
}
export interface BodyState {
  position: Vector; velocity: Vector; longitude_deg: number; latitude_deg: number;
  distance: number; target_kind: string; mean_longitude_deg: number | null;
  motion_deg_per_day: number | null;
}
export interface Metadata {
  model: Model; origin: string; frame: string; units: string; velocity_units: string;
  time_scale: string; provenance: string;
}
export interface Snapshot extends Metadata {
  instant: string; timestamp: number; bodies: Record<string, BodyState>;
  jd_tdb: number | null; jd_ujjain: number | null;
}
export interface Sample { timestamp: number; positions: Positions; velocities: Positions }
export interface Trajectory extends Metadata {
  start: string; end: string; samples: Sample[]; angular_tolerance_arcsec: number;
}
export interface SimulationState {
  model: Model; body: string; timestamp: number; playing: boolean; speed: number;
  direction: 1 | -1; nodes: boolean;
  spin: boolean; orbiting: boolean; guides: boolean;
}
export interface LessonSample {instant:string;timestamp:number;longitude_deg:number;motion_deg_per_day:number}
export interface MarsLesson extends Metadata {body:"Mars";longitude_units:'degrees';motion_units:'degrees/day';samples:LessonSample[]}
export type TourId = "spin" | "moon" | "retrograde" | "models";
export interface Demonstration { id: TourId; label: string }
