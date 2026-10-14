// Shapes of the /api/book/chapter/11 payload, one interface per card.

import type { CardBase } from "../ch01/types";
import type { DayDate } from "../dates";
export type { CardBase } from "../ch01/types";

export interface SumRuleCard extends CardBase {
  longitude_sum: number;
  vyatipata_sum: number;
  vaidhrita_sum: number;
  degrees_to_vyatipata: number;
  degrees_to_vaidhrita: number;
  next_by_sum_rule: "Vyatipata" | "Vaidhrita";
}

export interface DeclinationCard extends CardBase {
  sun_declination: number;
  moon_declination: number;
  moon_declination_plain: number;
  moon_latitude_arcmin: number;
  ayana_valana: number;
  nearest_kind: "Vyatipata" | "Vaidhrita" | null;
  is_past: boolean | null;
}

export interface PataEvent {
  kind: "Vyatipata" | "Vaidhrita";
  begin: DayDate;
  middle: DayDate;
  end: DayDate;
  duration_ghatis: number;
  duration_hours: number;
  sun_declination: number;
  moon_declination: number;
  refined: boolean;
}

export interface TimingCard extends CardBase, Partial<PataEvent> {
  found: boolean;
}

export interface EventsCard extends CardBase {
  days: number;
  events: PataEvent[];
  unrefined_count: number;
}

export interface Chapter11Payload {
  chapter: 11;
  title: string;
  jd: number;
  date: { year: number; month: number; day: number };
  days: number;
  order: string[];
  cards: {
    "xi.2-3": SumRuleCard;
    "xi.4-11": DeclinationCard;
    "xi.12-14": TimingCard;
    "xi.19": EventsCard;
  };
}
