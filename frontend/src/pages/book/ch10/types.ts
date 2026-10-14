// Shapes of the /api/book/chapter/10 payload, one interface per card.

import type { CardBase } from "../ch01/types";
import type { DayDate } from "../dates";
export type { CardBase } from "../ch01/types";

export interface VisibilityCard extends CardBase {
  elongation: number; distance: number; limit: number; visible: boolean;
  waxing: boolean; horizon: string;
}

export interface RiseSetCard extends CardBase {
  latitude: number; longitude: number; rise: DayDate | null; set: DayDate | null;
}

export interface IlluminationCard extends CardBase {
  elongation: number; paksha: string; reflected_elongation: number; minutes: number;
  lit_digits: number; fraction: number; library_fraction: number; phase: string;
  width_arcmin: number; moon_radius_arcmin: number;
}

/** The inputs of one drawn Moon. */
export interface Crescent {
  jd: number; date: DayDate; elongation: number; waxing: boolean; phase: string;
  fraction: number; width_arcmin: number; bright_limb_angle: number;
  horn_angle: number; sun_angle: number;
}

export interface FigureCard extends CardBase {
  latitude: number; longitude: number; now: Crescent; strip: Crescent[];
}

export interface Chapter10Payload {
  chapter: 10; title: string; jd: number;
  date: { year: number; month: number; day: number };
  order: string[];
  cards: {
    "x.1": VisibilityCard; "x.2-5": RiseSetCard; "x.9": IlluminationCard;
    "x.10-14": FigureCard;
  };
}
