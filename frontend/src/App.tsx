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
import { BookChapter } from "./pages/book/BookChapter";

// three.js adds several hundred kilobytes; loading the Instruments page on
// demand keeps it out of the bundle every other page downloads.
const Instruments = lazy(() =>
  import("./pages/Instruments").then((m) => ({ default: m.Instruments })),
);
const LearningLab = lazy(() =>
  import("./pages/learn/LearningLab").then((m) => ({ default: m.LearningLab })),
);
const LearningPaths = lazy(() => import("./pages/learn/LearningPaths").then(m => ({ default: m.LearningPaths })));
const RahuLesson = lazy(() => import("./pages/learn/RahuLesson").then(m => ({ default: m.RahuLesson })));
const ResearchExplorer = lazy(() => import("./pages/research/ResearchExplorer").then(m => ({ default: m.ResearchExplorer })));
const UniverseExplorer = lazy(() => import("./pages/universe/UniverseExplorer").then(m => ({ default: m.UniverseExplorer })));

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/positions" replace />} />
        <Route path="/positions" element={<PlanetPositions />} />
        <Route path="/universe" element={<Suspense fallback={<p role="status">Opening the Universe Explorer…</p>}><UniverseExplorer /></Suspense>} />
        <Route path="/learn" element={<Suspense fallback={<p role="status">Loading the learning lab…</p>}><LearningPaths /></Suspense>} />
        <Route path="/learn/mars" element={<Suspense fallback={<p role="status">Loading lesson…</p>}><LearningLab key="Mars" body="Mars" /></Suspense>} />
        <Route path="/learn/sun" element={<Suspense fallback={<p role="status">Loading lesson…</p>}><LearningLab key="Sun" body="Sun" /></Suspense>} />
        <Route path="/learn/moon" element={<Suspense fallback={<p role="status">Loading lesson…</p>}><LearningLab key="Moon" body="Moon" /></Suspense>} />
        <Route path="/learn/mercury" element={<Suspense fallback={<p role="status">Loading lesson…</p>}><LearningLab key="Mercury" body="Mercury" /></Suspense>} />
        <Route path="/learn/venus" element={<Suspense fallback={<p role="status">Loading lesson…</p>}><LearningLab key="Venus" body="Venus" /></Suspense>} />
        <Route path="/learn/jupiter" element={<Suspense fallback={<p role="status">Loading lesson…</p>}><LearningLab key="Jupiter" body="Jupiter" /></Suspense>} />
        <Route path="/learn/saturn" element={<Suspense fallback={<p role="status">Loading lesson…</p>}><LearningLab key="Saturn" body="Saturn" /></Suspense>} />
        <Route path="/learn/rahu" element={<Suspense fallback={<p role="status">Loading lesson…</p>}><RahuLesson /></Suspense>} />
        <Route path="/research" element={<Suspense fallback={<p role="status">Loading the research explorer…</p>}><ResearchExplorer /></Suspense>} />
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
        <Route path="/chat" element={<Navigate to="/positions" replace state={{ openChat: true }} />} />
      </Route>
    </Routes>
  );
}
