// Shapes of the /api/book/chapter/2 payload, one interface per card.
// The chapter page hands each card component its own slice.

import type { CardBase } from "../ch01/types";
export type { CardBase, VerseRecord } from "../ch01/types";

export interface BhujaKoti {
  kendra: number; quadrant: number; odd: boolean;
  bhuja: number; koti: number; bhuja_jya: number; koti_jya: number;
}

export interface SineRow {
  index: number; arcmin: number; degrees: number; jya: number;
  difference: number; utkrama: number; modern: number; error: number;
}
export interface SineTableCard extends CardBase {
  radius: number; step_arcmin: number; sign_arcmin: number; first_sine: number;
  rows: SineRow[]; note: string;
}

export interface BhujaKotiCard extends CardBase {
  rows: { body: string; manda: BhujaKoti; sighra: BhujaKoti | null }[];
  sample: BhujaKoti;
}

export interface InterpForward {
  arc_deg: number; arcmin: number; quotient: number; remainder_arcmin: number;
  preceding: number; following: number; difference: number; part: number;
  interpolated: number; library: number; exact: number;
}
export interface InterpInverse {
  sine: number; count_below: number; less: number; difference: number;
  arcmin: number; arc_deg: number; library_deg: number;
}
export interface InterpolationCard extends CardBase {
  step_arcmin: number; forward: InterpForward; inverse: InterpInverse;
}

export interface EpicycleAt {
  body: string; kendra: number; bhuja: number; sin_bhuja: number;
  manda: number; sighra: number | null;
}
export interface EpicyclesCard extends CardBase {
  sample_kendra: number;
  rows: {
    body: string; manda_even: number; manda_odd: number;
    sighra_even: number | null; sighra_odd: number | null; sample: EpicycleAt;
  }[];
}

export interface MandaCard extends CardBase {
  rows: (BhujaKoti & {
    body: string; mean: number; mandocca: number; epicycle: number;
    phala: number; corrected: number; corrected_rashi: string;
  })[];
}

export interface SighraCard extends CardBase {
  no_sighra: string[];
  rows: (BhujaKoti & {
    body: string; manda_sphuta: number; sighrocca: number; epicycle: number;
    kotiphala: number; bhujaphala: number; hypotenuse: number; phala: number;
  })[];
}

export interface TruePlaceCard extends CardBase {
  rows: {
    body: string; true_longitude: number; rashi: string;
    stages: { label: string; correction: number | null; longitude: number }[];
  }[];
}

export interface DayLength {
  latitude: number; sun_tropical: number; declination: number;
  direction: "north" | "south"; sine_declination: number; versed_sine: number;
  day_radius: number; day_ghatis: number; night_ghatis: number;
}
export type DayLengthCard = CardBase & DayLength;

export interface YogaCard extends CardBase {
  sun: number; moon: number; sum: number; sum_arcmin: number; span_deg: number;
  number: number; name: string; fraction: number; names: string[];
}
export interface TithiCard extends CardBase {
  sun: number; moon: number; elongation: number; span_deg: number;
  number: number; fraction: number; paksha: "shukla" | "krishna"; name: string;
}
export interface KaranaCard extends CardBase {
  sun: number; moon: number; elongation: number; span_deg: number;
  number: number; name: string; kind: "fixed" | "recurring";
  half_of_tithi: 1 | 2; recurring: string[]; fixed: string[];
}

export interface Chapter2Payload {
  chapter: 2; title: string; jd: number;
  date: { year: number; month: number; day: number };
  latitude: number; order: string[]; rashis: string[];
  cards: {
    "ii.15-27": SineTableCard; "ii.29-30": BhujaKotiCard; "ii.31-33": InterpolationCard;
    "ii.34-38": EpicyclesCard; "ii.39": MandaCard; "ii.40-42": SighraCard;
    "ii.43-45": TruePlaceCard; "ii.60-63": DayLengthCard; "ii.65": YogaCard;
    "ii.66": TithiCard; "ii.67-69": KaranaCard;
  };
}
