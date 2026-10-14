// Shapes of the /api/book/chapter/8 payload, one interface per card.

import type { CardBase as Base } from "../ch01/types";
import type { DayDate } from "../dates";

/** Chrome every Ch.8 card carries: which corpus records hold its text, if any. */
export interface CardBase extends Base {
  text_verses: string | null;
}

export interface LongitudeRow {
  number: number; name: string; star: string; share: number | null;
  preceding_minutes: number | null; rule: string; minutes: number; degrees: number;
  library_degrees: number; matches: boolean; selected: boolean;
}

export interface LongitudesCard extends CardBase {
  rows: LongitudeRow[]; bhoga_minutes: number;
  abhijit_degrees: number; abhijit_library_degrees: number;
}

export interface LatitudeRow {
  number: number; name: string; star: string; latitude: number;
  direction: string; selected: boolean;
}

export interface LatitudesCard extends CardBase {
  rows: LatitudeRow[];
}

export interface PositionCard extends CardBase {
  star: string; name: string; deity: string; sidereal_lon: number; sidereal_lat: number;
  ayanamsha: number; tropical_lon: number; right_ascension: number; declination: number;
  bhoga_of: string; circumpolar: boolean; never_visible: boolean;
  rise: DayDate | null; set: DayDate | null; hour_angle: number;
}

export interface ConjunctionsCard extends CardBase {
  planet: string; star: string; star_longitude: number; star_latitude: number;
  year: number; months: number;
  conjunctions: { jd: number; date: DayDate; separation_deg: number }[];
}

export interface Chapter8Payload {
  chapter: 8; title: string; jd: number; star: string;
  date: { year: number; month: number; day: number };
  order: string[];
  cards: {
    "viii.1-4": LongitudesCard; "viii.5-9": LatitudesCard;
    "viii.1-9": PositionCard; "viii.14-15": ConjunctionsCard;
  };
}
