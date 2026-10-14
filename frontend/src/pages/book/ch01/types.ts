// Shapes of the /api/book/chapter/1 payload, one interface per card.
//
// The chapter page hands each card component its own slice, so these are
// the contract between api/book.py's card builders and the twelve
// components below them.

/** Chrome every card carries, whatever it computes. */
export interface CardBase {
  id: string;
  verses: string;
  title: string;
  does: string;
  date_dependent: boolean;
  note?: string;
}

export interface TimeUnit {
  unit: string;
  alias: string | null;
  seconds: number;
  days: number;
  next: string | null;
  per_next: number | null;
  in_ss_text: boolean;
}

export interface TimeChain {
  key: string;
  label: string;
  verses: string;
  source: "verse" | "commentary";
  units: TimeUnit[];
}

export interface TimeUnitsCard extends CardBase {
  chains: TimeChain[];
  units_seconds: Record<string, number>;
  ghatis_per_day: number;
  palas_per_ghati: number;
  vipalas_per_pala: number;
  ghati_minutes: number;
}

export interface YugasCard extends CardBase {
  ages: { name: string; years: number }[];
  mahayuga_years: number;
  kalpa_years: number;
  mahayugas_per_kalpa: number;
  civil_days_per_mahayuga: number;
  sidereal_days_per_mahayuga: number;
  lunar_months_per_mahayuga: number;
  civil_days_per_kalpa: number;
  sidereal_year_days: number;
}

export interface EpochCard extends CardBase {
  kali_epoch_jd: number;
  kali_epoch_date: string;
  jd: number;
  ahargana: number;
  kali_years_elapsed: number;
  kali_era_year: number;
  yuga_elapsed_fraction: number;
  kali_fraction_elapsed: number;
}

export interface BhaganaRow {
  body: string;
  revolutions: number;
  daily_motion_deg: number;
  daily_motion_arcmin: number;
  period_days: number;
}

export interface BhaganaCard extends CardBase {
  rows: BhaganaRow[];
  civil_days_per_mahayuga: number;
}

export interface WorkedRow {
  body: string;
  revolutions: number;
  turns_elapsed: number;
  fraction_of_turn: number;
  longitude: number;
  longitude_dms: string;
}

export interface MeanRuleCard extends CardBase {
  formula: string;
  bhagana: Record<string, number>;
  ahargana: number;
  civil_days_per_mahayuga: number;
  sidereal_year_days: number;
  worked: WorkedRow[];
}

export interface OrbitPointRow {
  planet: string;
  revolutions: number;
  per: "Age" | "Aeon";
  epoch_longitude: number;
  daily_motion: number;
  longitude: number;
  longitude_dms: string;
  rashi: string;
}

export interface ApsidesCard extends CardBase {
  rows: OrbitPointRow[];
  ahargana: number;
  direction?: string;
}

export interface AharganaRouteCard extends CardBase {
  input: { years: number; months: number; tithis: number };
  route: AharganaRoute;
  direct_ahargana: number;
  difference_days: number | null;
  solar_months_per_mahayuga: number;
  adhimasa_per_mahayuga: number;
  lunar_days_per_mahayuga: number;
  tithikshaya_per_mahayuga: number;
}

/** The shape /calc/ahargana-verse returns, reused when sliders move. */
export interface AharganaRoute {
  elapsed: { years: number; months: number; tithis: number };
  reckoned_from: string;
  solar_months: number;
  adhimasa: number;
  lunar_months: number;
  lunar_days: number;
  tithikshaya: number;
  civil_days: number;
  creation_to_kali_civil_days: number;
  summary: string;
}

export interface VaraCard extends CardBase {
  number: number;
  name: string;
  name_en: string;
  order: { number: number; name: string; name_en: string }[];
}

export interface MeanPlaceRow {
  planet: string;
  longitude: number;
  longitude_dms: string;
  rashi: string;
  sighrocca: number | null;
  sighrocca_dms: string | null;
}

export interface MeanPlacesCard extends CardBase {
  rows: MeanPlaceRow[];
  ahargana: number;
  civil_days_per_mahayuga: number;
  bodies: { planet: string; bhagana: number; epoch: number; retrograde: boolean }[];
  sighrocca: { planet: string; bhagana: number }[];
}

export interface SamvatsaraCard extends CardBase {
  number: number;
  name: string;
  jupiter_revolutions: number;
  jovian_years_elapsed: number;
  counted_from: string;
  names: string[];
  vijaya_index: number;
  jupiter_bhagana: number;
  civil_days_per_mahayuga: number;
  ahargana: number;
}

export interface EpochPositionsCard extends CardBase {
  rows: {
    planet: string;
    mandocca: number;
    mandocca_dms: string;
    node: number | null;
    node_dms: string | null;
  }[];
  years_creation_to_kali: number;
  civil_days_creation_to_kali: number;
  quarter_ages: number;
}

export interface Chapter1Payload {
  chapter: number;
  title: string;
  jd: number;
  date: { year: number; month: number; day: number };
  order: string[];
  rashis: string[];
  cards: {
    "i.11-13": TimeUnitsCard;
    "i.15-22": YugasCard;
    "i.23-24": EpochCard;
    "i.29-34": BhaganaCard;
    "i.35-37": MeanRuleCard;
    "i.41-42": ApsidesCard;
    "i.43-44": ApsidesCard;
    "i.48-51": AharganaRouteCard;
    "i.52-vara": VaraCard;
    "i.52-54": MeanPlacesCard;
    "i.55": SamvatsaraCard;
    "i.56-58": EpochPositionsCard;
  };
}

/** One verse as /api/corpus/verses/1 returns it. */
export interface VerseRecord {
  id: string;
  chapter: number;
  verse: number;
  translation_en: string;
  commentary_en?: string;
}
