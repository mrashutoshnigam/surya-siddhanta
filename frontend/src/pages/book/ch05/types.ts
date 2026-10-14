// Shapes of the /api/book/chapter/5 payload, one interface per card.

import type { CardBase } from "../ch01/types";
export type { CardBase } from "../ch01/types";

export interface NoParallaxCard extends CardBase {
  latitude: number; sun: number; madhyalagna: number; interval: number;
  madhya_declination: number; latitude_gap: number;
  lambana_vanishes: boolean; nati_vanishes: boolean;
}

export interface LagnaCard extends CardBase {
  local_sidereal_time: number; lagna: number; greatest_declination: number;
  colatitude_sine: number; udaya: number; madhyalagna: number;
  madhya_declination: number; latitude: number; natamsa: number;
  direction: "north" | "south";
}

export interface DrkksepaCard extends CardBase {
  natamsa: number; madhyajya: number; udaya: number; drkksepa_verse: number;
  drkksepa_library: number; drkksepa_gap: number; drggati: number;
  approx_drkksepa: number; approx_drggati: number; vitribha: number;
}

export interface LambanaCard extends CardBase {
  drkksepa: number; drggati: number; interval: number; moon_from_vitribha: number;
  verse_ghatis: number; verse_arcmin: number; library_arcmin: number;
  library_ghatis: number; arcmin_per_ghati: number; rule: "add" | "subtract";
}

export interface NatiCard extends CardBase {
  drkksepa: number; verse_arcmin: number; shortcut_arcmin: number;
  library_arcmin: number; meridian_direction: "north" | "south";
  moon_latitude: number; corrected_latitude: number; same_direction: boolean;
}

export interface ResultCard extends CardBase {
  day: number; is_eclipse: boolean; eclipse_type: string; magnitude: number;
  locally_visible: boolean | null; sun_altitude_deg: number | null;
  half_duration_min: number | null; sun_diameter: number; moon_diameter: number;
  lambana: number | null; nati: number | null; geocentric_type: string;
  geocentric_magnitude: number; geocentric_latitude: number;
}

export type ContactsCard = CardBase & (
  | { is_eclipse: false }
  | {
      is_eclipse: true; half_duration_min: number; hemisphere: "eastern" | "western";
      hour_angle: number; lambana_contact: number; lambana_middle: number;
      lambana_separation: number; contact_adjust_min: number;
      separation_adjust_min: number; contact_half_min: number;
      separation_half_min: number; speed_arcmin_per_min: number;
    }
);

export interface LambanaProbe { drggati: number; verse_ghatis: number; verse_arcmin: number }
export interface NatiProbe { verse_arcmin: number; shortcut_arcmin: number; library_arcmin: number }

export interface Chapter5Payload {
  chapter: 5; title: string; jd: number;
  date: { year: number; month: number; day: number };
  place: { latitude: number; longitude: number };
  order: string[];
  cards: {
    "v.1": NoParallaxCard; "v.3-4": LagnaCard; "v.5-7": DrkksepaCard;
    "v.8-9": LambanaCard; "v.10-12": NatiCard; "v.13": ResultCard;
    "v.15-17": ContactsCard;
  };
}
