import { useParams } from "react-router-dom";
import { PageHeader } from "../../components/Tables";
import { Chapter1 } from "./ch01/Chapter1";
import { Chapter2 } from "./ch02/Chapter2";
import { Chapter3 } from "./ch03/Chapter3";
import { Chapter4 } from "./ch04/Chapter4";
import { Chapter5 } from "./ch05/Chapter5";
import { Chapter6 } from "./ch06/Chapter6";
import { Chapter7 } from "./ch07/Chapter7";
import { Chapter8 } from "./ch08/Chapter8";
import { Chapter9 } from "./ch09/Chapter9";
import { Chapter10 } from "./ch10/Chapter10";
import { Chapter11 } from "./ch11/Chapter11";
import { Chapter12 } from "./ch12/Chapter12";
import { Chapter13 } from "./ch13/Chapter13";
import { Chapter14 } from "./ch14/Chapter14";

/** The fourteen chapters of Burgess's translation, for the sidebar and here. */
export const BOOK_CHAPTERS: { number: number; title: string; ready: boolean }[] = [
  { number: 1, title: "Of the Mean Motions of the Planets", ready: true },
  { number: 2, title: "Of the True Places of the Planets", ready: true },
  { number: 3, title: "Of Direction, Place and Time", ready: true },
  { number: 4, title: "Of Eclipses, and especially of Lunar Eclipses", ready: true },
  { number: 5, title: "Of Parallax in a Solar Eclipse", ready: true },
  { number: 6, title: "Of the Projection of Eclipses", ready: true },
  { number: 7, title: "Of Planetary Conjunctions", ready: true },
  { number: 8, title: "Of the Asterisms", ready: true },
  { number: 9, title: "Of Heliacal Risings and Settings", ready: true },
  { number: 10, title: "Of the Moon's Rising and Setting, and of her Cusps", ready: true },
  { number: 11, title: "Of certain malignant Aspects of the Sun and Moon", ready: true },
  { number: 12, title: "Cosmogony, Geography, and Dimensions of the Creation", ready: true },
  { number: 13, title: "Of the Armillary Sphere and other Instruments", ready: true },
  { number: 14, title: "Of the Different Modes of Reckoning Time", ready: true },
];

/**
 * The /book/:chapter route.
 *
 * All fourteen chapters have verse cards. Anything else (a mistyped URL, or a
 * chapter marked not ready should one be added) gets a plain note rather than
 * a 404.
 */
export function BookChapter() {
  const { chapter } = useParams();
  const number = Number(chapter);

  if (number === 1) return <Chapter1 />;
  if (number === 2) return <Chapter2 />;
  if (number === 3) return <Chapter3 />;
  if (number === 4) return <Chapter4 />;
  if (number === 5) return <Chapter5 />;
  if (number === 6) return <Chapter6 />;
  if (number === 7) return <Chapter7 />;
  if (number === 8) return <Chapter8 />;
  if (number === 9) return <Chapter9 />;
  if (number === 10) return <Chapter10 />;
  if (number === 11) return <Chapter11 />;
  if (number === 12) return <Chapter12 />;
  if (number === 13) return <Chapter13 />;
  if (number === 14) return <Chapter14 />;

  const entry = BOOK_CHAPTERS.find((c) => c.number === number);
  return (
    <div>
      <PageHeader
        title={entry ? `Chapter ${entry.number} — ${entry.title}` : "No such chapter"}
        subtitle={
          entry
            ? "This chapter is not yet laid out verse by verse."
            : "The book has fourteen chapters."
        }
      />
      <p className="ss-note">
        The book has fourteen chapters, /book/1 to /book/14, each laid out verse by verse.
      </p>
    </div>
  );
}
