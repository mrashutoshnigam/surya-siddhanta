import type { DateValue } from "../../components/Inputs";
export const DEMO_DATE = { year: 2026, month: 11, day: 4 };
export const dateLabel = (d: DateValue) => `${d.year}-${String(d.month).padStart(2,"0")}-${String(d.day).padStart(2,"0")}`;
export function validDate(d: DateValue) {
 if(![d.year,d.month,d.day].every(Number.isInteger) || d.year<1600 || d.year>2600) return false;
 const actual=new Date(Date.UTC(d.year,d.month-1,d.day));
 return actual.getUTCFullYear()===d.year && actual.getUTCMonth()+1===d.month && actual.getUTCDate()===d.day;
}
