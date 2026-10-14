import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { PlanetPositions } from "./pages/PlanetPositions";
import { Panchanga } from "./pages/Panchanga";
import { LunarEclipse } from "./pages/LunarEclipse";
import { SolarEclipse } from "./pages/SolarEclipse";
import { Conjunctions } from "./pages/Conjunctions";
import { Stars } from "./pages/Stars";
import { Heliacal } from "./pages/Heliacal";
import { Moon } from "./pages/Moon";
import { Patas } from "./pages/Patas";
import { Cosmography } from "./pages/Cosmography";
import { PlaceTime } from "./pages/PlaceTime";
import { DailyPanchanga } from "./pages/DailyPanchanga";
import { Chat } from "./pages/Chat";
import { BookChapter } from "./pages/book/BookChapter";

// three.js adds several hundred kilobytes; loading the Instruments page on
// demand keeps it out of the bundle every other page downloads.
const Instruments = lazy(() =>
  import("./pages/Instruments").then((m) => ({ default: m.Instruments })),
);

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/positions" replace />} />
        <Route path="/positions" element={<PlanetPositions />} />
        <Route path="/panchanga" element={<Panchanga />} />
        <Route path="/eclipse/lunar" element={<LunarEclipse />} />
        <Route path="/eclipse/solar" element={<SolarEclipse />} />
        <Route path="/conjunctions" element={<Conjunctions />} />
        <Route path="/stars" element={<Stars />} />
        <Route path="/heliacal" element={<Heliacal />} />
        <Route path="/moon" element={<Moon />} />
        <Route path="/patas" element={<Patas />} />
        <Route path="/cosmography" element={<Cosmography />} />
        <Route
          path="/instruments"
          element={
            <Suspense fallback={<p className="ss-note">Loading the armillary sphere…</p>}>
              <Instruments />
            </Suspense>
          }
        />
        <Route path="/place-time" element={<PlaceTime />} />
        <Route path="/daily-panchanga" element={<DailyPanchanga />} />
        <Route path="/book/:chapter" element={<BookChapter />} />
        <Route path="/chat" element={<Chat />} />
      </Route>
    </Routes>
  );
}
