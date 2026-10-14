// Shapes of the /api/book/chapter/9 payload, one interface per card.

import type { CardBase } from "../ch01/types";
import type { DayDate } from "../dates";
export type { CardBase } from "../ch01/types";

export const PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"] as const;

export interface DirectionCard extends CardBase {
  planet: string; elongation: number; greater_than_sun: boolean; retrograde: boolean;
  visible: boolean; rule: "slow" | "swift"; event: "setting" | "rising";
  horizon: "west" | "east";
}

export interface ThresholdRow {
  planet: string; retrograde: number; direct: number; selected: boolean;
}

export interface ThresholdsCard extends CardBase {
  rows: ThresholdRow[]; planet: string; elongation: number; threshold: number;
  retrograde: boolean; margin: number; visible: boolean;
}

export interface HeliacalEvent {
  type: "rising" | "setting"; jd: number; date: DayDate; elongation: number;
  direction: "morning" | "evening";
}

export interface NextEventCard extends CardBase {
  event: "rising" | "setting"; elongation: number; threshold: number;
  shortfall_arcmin: number; planet_motion: number; sun_motion: number;
  closing_rate: number; hand_days: number | null; hand_date: DayDate | null;
  library: HeliacalEvent | null; days_apart: number | null;
}

export interface EventsCard extends CardBase {
  planet: string; months: number; events: HeliacalEvent[];
}

export interface StarsCard extends CardBase {
  groups: { degrees: number; verse: string; stars: string[] }[];
  circumpolar: string[];
}

export interface Chapter9Payload {
  chapter: 9; title: string; jd: number; planet: string;
  date: { year: number; month: number; day: number };
  order: string[];
  cards: {
    "ix.2-3": DirectionCard; "ix.6-9": ThresholdsCard; "ix.10-11": NextEventCard;
    "ix.6-11": EventsCard; "ix.12-18": StarsCard;
  };
}
