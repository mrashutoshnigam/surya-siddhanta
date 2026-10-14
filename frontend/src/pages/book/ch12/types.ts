// Shapes of the /api/book/chapter/12 payload, one interface per card.

import type { CardBase } from "../ch01/types";
export type { CardBase } from "../ch01/types";

export interface SphereCard extends CardBase {
  latitude: number;
  kind: "right" | "oblique" | "parallel";
  pole_altitude: number;
  colatitude: number;
  hemisphere: "gods" | "demons" | "neither";
  day_ghatis: number | null;
  description: string;
}

export interface EarthCard extends CardBase {
  latitude: number;
  longitude: number;
  circumference: number;
  obliquity: number;
  obliquity_yojanas: number;
  polar_day_limit: {
    latitude: number;
    yojanas_from_equator: number;
    yojanas_from_pole: number;
  };
  corrected_circumference: number;
  desantara_yojanas: number;
  moon_daily_arcmin: number;
  moon_correction_arcmin: number;
}

export interface InvisibilityLimit {
  sign_longitude: number;
  declination: number;
  latitude: number;
  yojanas_from_equator: number;
  signs_invisible: number;
}

export interface LimitsCard extends CardBase {
  limits: InvisibilityLimit[];
  overhead_band: { yojanas: number; degrees: number };
}

export interface ClockCard extends CardBase {
  anchor: string;
  anchor_hour: number;
  hours: { name: string; iast: string; longitude: number; hour: number }[];
}

export interface DaysCard extends CardBase {
  day_of_the_gods: number;
  day_of_the_manes: number;
  day_of_brahma: number;
  brahma: {
    years_elapsed: number;
    years_remaining: number;
    fraction: number;
    kalpa_years: number;
  };
}

export interface RegentsCard extends CardBase {
  day: string;
  month: string;
  year: string;
  horas: string[];
  order: string[];
}

export interface OrbitRow {
  body: string;
  orbit_yojanas: number;
  revolutions_per_kalpa: number;
  orbit_diameter_yojanas: number;
  distance_yojanas: number;
  daily_motion_arcmin: number;
  stated_yojanas: number | null;
  stated_difference: number | null;
}

export interface OrbitsCard extends CardBase {
  daily_linear_motion: number;
  ether_orbit: number;
  orbits: OrbitRow[];
}

export interface Chapter12Payload {
  chapter: 12;
  title: string;
  jd: number;
  date: { year: number; month: number; day: number };
  latitude: number;
  longitude: number;
  order: string[];
  cards: {
    "xii.42-44": SphereCard;
    "xii.59-61": EarthCard;
    "xii.63-68": LimitsCard;
    "xii.70-71": ClockCard;
    "xii.74": DaysCard;
    "xii.78-79": RegentsCard;
    "xii.80-90": OrbitsCard;
  };
}
