// Shapes of the glossary document served by GET /api/glossary
// (src/suryasiddhanta/data/glossary.json).

/** How a term is grouped in the panel. */
export type Category =
  | "concept"
  | "unit"
  | "place"
  | "planet"
  | "rashi"
  | "nakshatra"
  | "tithi"
  | "yoga"
  | "karana"
  | "weekday"
  | "month"
  | "season"
  | "samvatsara"
  | "instrument"
  | "star";

/** One equation in a term's full entry: LaTeX source plus an optional caption. */
export interface Equation {
  latex: string;
  caption?: string;
}

/** A diagram for the popup; `src` is a file name under /api/glossary/img/. */
export interface TermImage {
  src: string;
  alt: string;
}

/** Limits on where and how the page scan may find a term. */
export interface TermMatch {
  /** Match the name and aliases with exact case (default false). */
  caseSensitive?: boolean;
  /** Only find the term on these routes; null or absent means any route. */
  routes?: string[] | null;
}

/** One glossary entry as stored in the document. */
export interface Term {
  term: string;
  aliases?: string[];
  category: Category;
  short: string;
  full: string[];
  equations?: Equation[];
  image?: TermImage;
  cite?: string[];
  related?: string[];
  match?: TermMatch;
}

/** A term together with its id (the key it is stored under). */
export interface TermEntry extends Term {
  id: string;
}

/** The whole glossary document. */
export interface GlossaryDoc {
  version: number;
  terms: Record<string, Term>;
  /** Route path → the curated core term ids for that page, in reading order. */
  routes: Record<string, string[]>;
}

/** Panel headings for each category. */
export const CATEGORY_LABELS: Record<Category, string> = {
  concept: "Concepts",
  unit: "Units",
  place: "Places",
  planet: "Planets",
  rashi: "Signs (rashi)",
  nakshatra: "Nakshatras",
  tithi: "Lunar days (tithi)",
  yoga: "Yogas",
  karana: "Karanas",
  weekday: "Weekdays (vara)",
  month: "Months (masa)",
  season: "Seasons (ritu)",
  samvatsara: "Jovian years (samvatsara)",
  instrument: "Instruments",
  star: "Stars",
};

/** The order categories appear in under "Also mentioned". */
export const CATEGORY_ORDER: Category[] = [
  "concept",
  "unit",
  "instrument",
  "place",
  "planet",
  "star",
  "rashi",
  "nakshatra",
  "tithi",
  "yoga",
  "karana",
  "weekday",
  "month",
  "season",
  "samvatsara",
];
