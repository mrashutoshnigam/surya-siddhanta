// Shapes of the /api/book/chapter/14 payload, one interface per card.

import type { CardBase } from "../ch01/types";
import type { DayDate } from "../dates";
export type { CardBase } from "../ch01/types";

export interface ManaRow {
  key: string;
  iast: string;
  devanagari: string;
  english: string;
  unit: string;
  unit_days: number;
  practical: boolean;
  uses: string[];
  verses: string;
  source: string;
  count: number;
  reading_unit: string;
  description: string;
}

export interface ManasCard extends CardBase {
  manas: ManaRow[];
  details: Record<string, unknown>;
}

export interface Mark {
  name: string;
  longitude: number;
  arc_degrees: number;
  measured_days: number;
  jd: number;
  date: DayDate;
  use?: string;
}

export interface MukhasCard extends CardBase {
  marks: Mark[];
  note: string;
}

export interface Sankranti {
  sign: string;
  masa: string;
  longitude: number;
  kind: "visuvat" | "ayana" | "plain";
  jd: number;
  date: DayDate;
  tropical_longitude: number;
  ayanamsha: number;
  punyakala_total_nadis: number;
  punyakala_each_side_nadis: number;
}

export interface Ritu {
  name: string;
  english: string;
  start_sign: string;
  days: number;
  start: DayDate;
  end: DayDate;
}

export interface SankrantisCard extends CardBase {
  year_days: number;
  sankrantis: Sankranti[];
  ayanas: { dakshinayana: Sankranti; uttarayana: Sankranti };
  visuvats: { vernal: Sankranti; autumnal: Sankranti };
  ritus: Ritu[];
}

export interface FathersCard extends CardBase {
  elongation: number;
  hour: number;
  ghati: number;
  day_fraction: number;
  tithi: number;
  tithi_name: string;
  paksha: string;
  phase: string;
  next_noon: DayDate;
  next_midnight: DayDate;
  month_days: number;
}

export interface AsterismsCard extends CardBase {
  months: { month: string; namesake: string; asterisms: string[] }[];
  moon_longitude: number;
  moon_asterism: string;
  moon_month: string;
}

export interface JovianYear {
  method: "mean" | "heliacal";
  source: "verse" | "commentary";
  jovian_years_elapsed: number;
  name: string;
  name_index: number;
  asterism: string;
  longitude: number;
  sixty_year_name: string;
  note: string;
}

export interface JupiterCard extends CardBase {
  mean: JovianYear;
  heliacal: JovianYear | null;
  cycle: (JovianYear & { date: DayDate; advance: number })[];
}

export interface ConverterCard extends CardBase {
  value: number;
  from_mana: string;
  to_mana: string;
  result: number;
  units: { key: string; iast: string; unit: string; unit_days: number }[];
  structure: {
    manvantaras: number;
    manvantara_years: number;
    sandhis: number;
    sandhi_years: number;
    total_years: number;
    kalpa_years: number;
  };
}

export interface Chapter14Payload {
  chapter: 14;
  title: string;
  jd: number;
  date: { year: number; month: number; day: number };
  value: number;
  from_mana: string;
  to_mana: string;
  heliacal: boolean;
  order: string[];
  cards: {
    "xiv.1-2": ManasCard;
    "xiv.4-6": MukhasCard;
    "xiv.7-11": SankrantisCard;
    "xiv.12-14": FathersCard;
    "xiv.15-16": AsterismsCard;
    "xiv.17": JupiterCard;
    "xiv.18-21": ConverterCard;
  };
}
