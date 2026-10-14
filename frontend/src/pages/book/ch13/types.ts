// Shapes of the /api/book/chapter/13 payload, one interface per card.

import type { CardBase } from "../ch01/types";
export type { CardBase } from "../ch01/types";

export interface HoopsCard extends CardBase {
  great: { key: string; name: string; verse: string; note: string }[];
  solar: { key: string; name: string; declination: number; day_radius: number }[];
  stars: Record<string, number>;
}

export interface SpherePointRow {
  key: string;
  name: string;
  tropical_longitude: number;
  sidereal_longitude: number;
  right_ascension: number;
  declination: number;
  note: string;
}

export interface PointsCard extends CardBase {
  cardinal: SpherePointRow[];
  signs: SpherePointRow[];
  chord_of_thirty: number;
}

export interface LagnasCard extends CardBase {
  lst_deg: number;
  ayanamsha: number;
  points: SpherePointRow[];
}

export interface SinesCard extends CardBase {
  sun_declination: number;
  sines: {
    krantijya: number;
    dyujya: number;
    kujya: number;
    carajya: number;
    antya_great_circle: number;
    antya_small_circle: number;
  };
  pole_altitude: number;
}

export interface InstrumentRow {
  instrument: "nara" | "cakra" | "dhanus" | "yashti";
  reading: number;
  reading_unit: string;
  ghatis_since_sunrise: number;
  ghatis_to_sunset: number;
  sun_altitude_deg: number;
  source: "verse" | "commentary";
  verse: string;
}

export interface Clepsydra {
  day_ghatis: number;
  night_ghatis: number;
  day_sinkings: { sinkings: number; partial: number };
  night_sinkings: { sinkings: number; partial: number };
}

export interface TimeCard extends CardBase {
  found: boolean;
  reason?: string;
  shadow?: number;
  forenoon?: boolean;
  instruments?: InstrumentRow[];
  clepsydra: Clepsydra;
}

export interface Chapter13Payload {
  chapter: 13;
  title: string;
  jd: number;
  date: { year: number; month: number; day: number };
  latitude: number;
  longitude: number;
  shadow: number;
  forenoon: boolean;
  order: string[];
  cards: {
    "xiii.4-9": HoopsCard;
    "xiii.10-11": PointsCard;
    "xiii.13-14": LagnasCard;
    "xiii.14-15": SinesCard;
    "xiii.20-24": TimeCard;
  };
}
