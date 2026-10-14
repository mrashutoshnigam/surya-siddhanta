// Shapes of the /api/book/chapter/4 payload, one interface per card.

import type { CardBase } from "../ch01/types";
export type { CardBase, VerseRecord } from "../ch01/types";

export interface DiametersCard extends CardBase {
  sun_yojana: number; moon_yojana: number; earth_yojana: number; yojana_per_arcmin: number;
  sun_mean_arcmin: number; moon_mean_arcmin: number; sun_arcmin: number;
  moon_arcmin: number; moon_ratio: number;
}

export interface ShadowCard extends CardBase {
  earth_yojana: number; sun_yojana: number; moon_yojana: number; difference: number;
  correction: number; shadow_yojana: number; shadow_arcmin: number; library_arcmin: number;
}

export interface OppositionCard extends CardBase {
  day: number; sun: number; moon: number; moon_rashi: string; elongation: number;
  node: number; moon_minus_node: number;
}

/** The v.10-13 geometry; every duration is `null` when there is no eclipse. */
export interface Geometry {
  moon_diameter: number; shadow_diameter: number; latitude: number;
  half_sum: number; half_difference: number; obscured: number;
  speed_arcmin_per_min: number; eclipse_type: "total" | "partial" | "none";
  magnitude: number; root_sum: number | null; root_difference: number | null;
  half_duration_min: number | null; half_duration_ghatis: number | null;
  totality_half_min: number | null; totality_half_ghatis: number | null;
}
export type ObscurationCard = CardBase & Geometry & { moon_longitude: number; node_longitude: number };
export type DurationCard = CardBase & Geometry;

export interface Chapter4Payload {
  chapter: 4; title: string; jd: number;
  date: { year: number; month: number; day: number };
  order: string[];
  cards: {
    "iv.1-2": DiametersCard; "iv.4-5": ShadowCard; "iv.7-8": OppositionCard;
    "iv.10-11": ObscurationCard; "iv.12-13": DurationCard;
  };
}
