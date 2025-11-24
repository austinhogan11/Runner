import { useEffect, useState } from "react";
import { getWeeklyMileage, getRunsInRange } from "./api";
import type { WeeklyMileagePoint, Run } from "./api";

function toISODate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

// Monday–Sunday window for a given offset (0 = this week, -1 = last, etc.)
function getWeekRange(offset: number): { start: string; end: string } {
  const now = new Date();

  // JS: 0 = Sunday, 1 = Monday, ..., 6 = Saturday
  const day = now.getDay();
  const daysSinceMonday = (day + 6) % 7; // 0 if Monday, 1 if Tuesday, ... 6 if Sunday

  const monday = new Date(now);
  monday.setHours(0, 0, 0, 0);
  monday.setDate(monday.getDate() - daysSinceMonday + offset * 7);

  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);

  return {
    start: toISODate(monday),
    end: toISODate(sunday),
  };
}

function App() {
  // 0 = this week, -1 = previous week, etc.
  const [weekOffset, setWeekOffset] = useState(0);
  const [mileage, setMileage] = useState<WeeklyMileagePoint[]>([]);
  const [isLoadingMileage, setIsLoadingMileage] = useState(true);
  const [mileageError, setMileageError] = useState<string | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [runsError, setRunsError] = useState<string | null>(null);

  const weeklyDistance = runs.reduce((sum, run) => sum + run.distance_mi, 0);
  const { start: weekStart, end: weekEnd } = getWeekRange(weekOffset);

  const handlePrevWeek = () => setWeekOffset((w) => w - 1);
  const handleNextWeek = () => {
    // don’t go into the future
    setWeekOffset((w) => (w < 0 ? w + 1 : w));
  };

  useEffect(() => {
    async function loadMileage() {
      try {
        setIsLoadingMileage(true);
        setMileageError(null);
        const data = await getWeeklyMileage();
        setMileage(data);
      } catch (err) {
        console.error(err);
        setMileageError("Failed to load weekly mileage");
      } finally {
        setIsLoadingMileage(false);
      }
    }

    loadMileage();
  }, []);

  useEffect(() => {
  async function loadRunsForWeek() {
    try {
      setIsLoadingRuns(true);
      setRunsError(null);

      const { start, end } = getWeekRange(weekOffset);
      const data = await getRunsInRange(start, end);
      setRuns(data);
    } catch (err) {
      console.error(err);
      setRunsError("Failed to load runs for this week");
    } finally {
      setIsLoadingRuns(false);
    }
  }

  loadRunsForWeek();
}, [weekOffset]);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* HEADER */}
      <header className="py-10 text-center">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
          <span className="px-4 py-1 rounded-full bg-sky-500/10 text-sky-300 shadow-lg shadow-sky-500/30 border border-sky-500/40">
            Runner Dashboard
          </span>
        </h1>
        <p className="text-slate-400 mt-4">
          12-week mileage &amp; weekly training log
        </p>
      </header>

      <main className="max-w-5xl mx-auto px-4 pb-12 space-y-8">
        {/* GRAPHS ROW */}
        <section className="grid gap-6 md:grid-cols-2">
          <div className="bg-slate-800/80 border border-slate-700 rounded-2xl shadow-lg shadow-black/40 p-4">
            <h2 className="font-semibold mb-2 text-slate-100">
              Weekly mileage (last 12 weeks)
            </h2>
            <div className="h-64 flex flex-col items-center justify-center text-slate-300 text-sm">
              {isLoadingMileage && (
                <p className="text-slate-500">Loading mileage...</p>
              )}

              {!isLoadingMileage && mileageError && (
                <p className="text-red-400 text-sm">{mileageError}</p>
              )}

              {!isLoadingMileage && !mileageError && mileage.length === 0 && (
                <p className="text-slate-500">No mileage data yet.</p>
              )}

              {!isLoadingMileage && !mileageError && mileage.length > 0 && (
                <ul className="space-y-1 text-center">
                  {mileage.map((w) => (
                    <li key={w.week_start}>
                      <span className="text-sky-300">{w.week_start}</span>
                      {" — "}
                      {(w.total_mileage ?? 0).toFixed(2)} mi
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="bg-slate-800/80 border border-slate-700 rounded-2xl shadow-lg shadow-black/40 p-4">
            <h2 className="font-semibold mb-2 text-slate-100">Second graph</h2>
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
              Another graph placeholder
              <br />
              (pace trends, distance distribution, etc.)
            </div>
          </div>
        </section>

        {/* WEEKLY RUN LOG */}
        <section className="bg-slate-800/80 border border-slate-700 rounded-2xl shadow-lg shadow-black/40 p-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
              <div>
                <h2 className="font-semibold text-slate-100">
                  This week&apos;s runs
                </h2>
                <p className="text-xs text-slate-500">
                  {weekStart} → {weekEnd} • Total:{" "}
                  <span className="text-sky-300">
                    {weeklyDistance.toFixed(2)} mi
                  </span>
                </p>
                <p className="text-[10px] text-slate-600">
                  Week offset: {weekOffset} (0 = current week)
                </p>
              </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handlePrevWeek}
                className="px-3 py-1.5 rounded-full border border-slate-600 text-sm text-slate-200 hover:bg-slate-700/80 transition"
              >
                ← Previous
              </button>
              <button
                onClick={handleNextWeek}
                className="px-3 py-1.5 rounded-full border border-sky-500/60 bg-sky-500/20 text-sm text-sky-200 hover:bg-sky-500/30 shadow shadow-sky-500/40 transition disabled:opacity-40"
                disabled={weekOffset === 0}
              >
                Next →
              </button>
            </div>
          </div>

          {/* Placeholder list – to be wired to GET /runs */}
          <div className="space-y-3">
            {isLoadingRuns && (
              <p className="text-sm text-slate-500">Loading runs...</p>
            )}

            {!isLoadingRuns && runsError && (
              <p className="text-sm text-red-400">{runsError}</p>
            )}

            {!isLoadingRuns && !runsError && runs.length === 0 && (
              <p className="text-sm text-slate-500">
                No runs logged for this week.
              </p>
            )}

            {!isLoadingRuns && !runsError && runs.length > 0 && (
              <div className="space-y-3">
                {runs.map((run) => (
                  <article
                    key={run.id}
                    className="rounded-xl border border-slate-700 bg-slate-900/40 p-3 shadow-md shadow-black/40 hover:border-sky-500/60 hover:shadow-sky-500/30 transition cursor-pointer"
                  >
                    {/* Top row: date + title */}
                    <div className="flex items-baseline justify-between gap-3">
                      <div>
                        <p className="text-xs text-slate-400">{run.date}</p>
                        <h3 className="text-sm font-semibold text-slate-100">
                          {run.title}
                        </h3>
                      </div>
                      <div className="text-right text-xs text-slate-400">
                        <div className="text-sky-300 font-semibold">
                          {run.distance_mi.toFixed(2)} mi
                        </div>
                        <div>
                          {run.duration} • {run.pace}
                        </div>
                      </div>
                    </div>

                    {/* Notes */}
                    {run.notes && (
                      <p className="mt-2 text-xs text-slate-400 line-clamp-2">
                        {run.notes}
                      </p>
                    )}

                    {/* Future: heart rate, elevation, GPS, etc. */}
                    <div className="mt-2 text-[10px] uppercase tracking-wide text-slate-600">
                      Click to view details (HR, pace, elevation, GPS) — coming soon
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;