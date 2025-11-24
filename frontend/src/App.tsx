import { useState } from "react";

function App() {
  // 0 = this week, -1 = previous week, etc.
  const [weekOffset, setWeekOffset] = useState(0);

  const handlePrevWeek = () => setWeekOffset((w) => w - 1);
  const handleNextWeek = () => {
    // don’t go into the future
    setWeekOffset((w) => (w < 0 ? w + 1 : w));
  };

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
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
              Graph placeholder – we&apos;ll wire this to
              <br />
              <code className="bg-slate-900/70 px-1 mt-1 rounded text-sky-300">
                /runs/weekly_mileage
              </code>
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
            <div className="border border-dashed border-slate-600 rounded-xl p-3 text-sm text-slate-400">
              Run list placeholder – we&apos;ll fetch from
              <code className="bg-slate-900/70 px-1 ml-1 rounded text-sky-300">
                GET /runs?start_date=&amp;end_date=
              </code>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;