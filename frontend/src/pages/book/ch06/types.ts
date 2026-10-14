// Shapes of the /api/book/chapter/6 payload, one interface per card.
//
// Every length is arcminutes ("digits") from the centre of the eclipsed
// body, x along the ecliptic and y across it; the diagram rotates by the
// valana. See api/book_ch06.py for the sign conventions.

import type { CardBase } from "../ch01/types";
export type { CardBase } from "../ch01/types";

export type Pt = [number, number];
export type Kind = "lunar" | "solar";

/** The disks, the verdict and the chord of the path. */
export interface Geometry {
  kind: Kind;
  eclipsed_radius: number; eclipser_radius: number; half_sum: number;
  half_difference: number; latitude: number; is_eclipse: boolean;
  eclipse_type: "total" | "annular" | "partial" | "none";
  obscured: number; magnitude: number; chord_half: number | null;
  contact: Pt | null; middle: Pt; separation: Pt | null;
}

export interface CirclesCard extends CardBase {
  valana_circle: number; aggregate_radius: number; eclipsed_radius: number;
  eclipser_radius: number; half_difference: number;
  eclipsed_body: string; eclipser_body: string;
}

export interface DirectionsCard extends CardBase {
  contact_limb: "east" | "west"; separation_limb: "east" | "west";
  valana: number; ayana_valana: number; aksha_valana: number;
  valana_direction: "north" | "south"; contact_valana: number; separation_valana: number;
  latitude: number; latitude_direction: "north" | "south"; same_direction: boolean;
  deflection_laid: "east" | "west"; latitude_drawn: string;
}

export type ObscurationCard = CardBase & Geometry & {
  valana: number; middle_latitude: number; circle_radius: number;
};

export interface VisibilityCard extends CardBase {
  kind: Kind; threshold: number; obscured: number; visible: boolean; is_eclipse: boolean;
}

export type PathCard = CardBase & Geometry & {
  valana: number; chord_length: number | null; library_chord_half: number | null;
};

export type StickCard = CardBase & Geometry & {
  valana: number; stick: number | null; reaches_path: boolean;
  contact_point: Pt | null; separation_point: Pt | null;
  default_obscured?: number; has_immersion?: boolean;
};

export interface ColoursCard extends CardBase {
  kind: Kind; magnitude: number; eclipse_type: string; at_maximum: string | null;
  scheme: { phase: string; colour: string }[];
}

export interface StickProbe {
  half_sum: number; half_difference: number; stick: number; max_obscured: number;
  reaches_path: boolean; point: Pt | null;
}

export interface Chapter6Payload {
  chapter: 6; title: string; kind: Kind; jd: number;
  date: { year: number; month: number; day: number };
  place: { latitude: number; longitude: number };
  order: string[];
  cards: {
    "vi.2": CirclesCard; "vi.4-9": DirectionsCard; "vi.10-11": ObscurationCard;
    "vi.13": VisibilityCard; "vi.14-16": PathCard; "vi.17-19": StickCard;
    "vi.20-22": StickCard; "vi.23": ColoursCard;
  };
}
