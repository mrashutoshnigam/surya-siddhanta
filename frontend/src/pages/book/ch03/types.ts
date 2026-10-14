// Shapes of the /api/book/chapter/3 payload, one interface per card.
// The chapter page hands each card component its own slice.

import type { CardBase } from "../ch01/types";
export type { CardBase, VerseRecord } from "../ch01/types";

/** Shadow figures; both are `null` when the Sun is on the horizon. */
export interface ShadowResult {
  gnomon: number; shadow: number | null; hypotenuse: number | null; direction: string;
}

export interface DirectionResult {
  tip1: [number, number]; tip2: [number, number]; midpoint: [number, number];
  noon_shadow_direction: "north" | "south"; ns_angle: number; cardinal: string;
}
export type DirectionCard = CardBase & DirectionResult;

export type GnomonResult = ShadowResult & { altitude: number };
export type GnomonCard = CardBase & GnomonResult;

export interface AyanaCard extends CardBase {
  ayanamsha: number; kali_years: number; period_years: number;
  rows: { body: string; sidereal: number; tropical: number; rashi: string }[];
}

export interface LatitudeResult {
  shadow: number; sun_tropical: number; declination: number; altitude: number;
  shadow_direction: "north" | "south"; latitude: number;
}
export type LatitudeCard = CardBase & LatitudeResult & { latitude_true: number };

export interface Equatorial {
  tropical: number; right_ascension: number; declination: number; direction: "north" | "south";
}
export interface EquatorialCard extends CardBase {
  rows: (Equatorial & { body: string })[];
}

export type NoonShadow = ShadowResult & {
  latitude: number; declination: number; zenith_distance: number; altitude: number;
};
export type NoonShadowCard = CardBase & NoonShadow;

export type HourAngleResult = ShadowResult & {
  latitude: number; declination: number; hour_angle: number; azimuth: number; altitude: number;
};
export type HourAngleCard = CardBase & HourAngleResult;

export interface CaraResult {
  latitude: number; sun_tropical: number; declination: number; cara_ghatis: number;
  half_day_ghatis: number; sunrise_hour_angle: number; sunrise_offset_hours: number;
  day_ghatis: number; night_ghatis: number;
}
export type CaraCard = CardBase & CaraResult;

export interface RisingResult {
  latitude: number;
  rows: { index: number; rashi: string; degrees: number; asus: number; lanka_asus: number; text_asus: number }[];
}
export type RisingCard = CardBase & RisingResult;

export interface Chapter3Payload {
  chapter: 3; title: string; jd: number;
  date: { year: number; month: number; day: number };
  latitude: number; order: string[];
  cards: {
    "iii.1-4": DirectionCard; "iii.5-8": GnomonCard; "iii.9-12": AyanaCard;
    "iii.13-17": LatitudeCard; "iii.18-20": EquatorialCard; "iii.21-23": NoonShadowCard;
    "iii.38-41": HourAngleCard; "iii.42": CaraCard; "iii.43-44": RisingCard;
  };
}
