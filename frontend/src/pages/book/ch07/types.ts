// Shapes of the /api/book/chapter/7 payload, one interface per card.

import type { CardBase } from "../ch01/types";
import type { DayDate } from "../dates";
export type { CardBase } from "../ch01/types";

export const BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"] as const;
export type Body = (typeof BODIES)[number];

export interface WhoCard extends CardBase {
  planet1: string; planet2: string; planet1_taragraha: boolean;
  planet2_taragraha: boolean; both_taragraha: boolean; relation: string;
}

export interface DirectionCard extends CardBase {
  planet1: string; planet2: string; longitude1: number; longitude2: number;
  gap: number; motion1: number; motion2: number; retrograde1: boolean;
  retrograde2: boolean; relative_speed: number; swifter: string;
  status: "past" | "to come"; rule: "v.2" | "v.3";
}

export interface CorrectionStep {
  jd: number; gap_arcmin: number; relative_speed: number;
  move_days: number; move_ghatis: number; rule: "add" | "subtract";
}

export interface CorrectionCard extends CardBase {
  steps: CorrectionStep[]; settled: boolean; final_jd: number | null;
  final_date: DayDate | null; library_jd: number | null;
  library_date: DayDate | null; agrees: boolean;
}

export type LatitudesCard = CardBase & (
  | { found: false }
  | {
      found: true; jd: number; date: DayDate; latitude1: number; latitude2: number;
      same_direction: boolean; verse_gap: number; library_separation_arcmin: number;
    }
);

export type ClassificationCard = CardBase & (
  | { found: false }
  | {
      found: true; jd: number; date: DayDate; longitude: number;
      separation_deg: number; type: string; limit_deg: number;
      winner: string | null; north_planet: string; latitude1: number; latitude2: number;
    }
);

export interface Chapter7Payload {
  chapter: 7; title: string; jd: number; pair: [string, string];
  date: { year: number; month: number; day: number };
  order: string[];
  cards: {
    "vii.1": WhoCard; "vii.2-3": DirectionCard; "vii.4-6": CorrectionCard;
    "vii.12": LatitudesCard; "vii.19-22": ClassificationCard;
  };
}
