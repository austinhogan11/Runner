import { useEffect, useState, useMemo } from "react";
import { getWeeklyMileage, getRunsInRange } from "./api";
import type { WeeklyMileagePoint, Run } from "./api";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  BarChart,
  Bar,
} from "recharts";

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

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function buildWeekDaySeries(runs: Run[], weekStartISO: string) {
  const monday = new Date(weekStartISO);
  monday.setHours(0, 0, 0, 0);

  const series: { date: string; label: string; total: number }[] = [];

  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    const iso = toISODate(d);

    const total = runs
      .filter((run) => run.date === iso)
      .reduce((sum, run) => sum + run.distance_mi, 0);

    series.push({
      date: iso,
      label: DAY_LABELS[i],
      total,
    });
  }

  return series;
}

type MileageRange = "12w" | "6m" | "1y";

function sliceMileageForRange(
  all: WeeklyMileagePoint[],
  range: MileageRange
): WeeklyMileagePoint[] {
  const nWeeks = range === "12w" ? 12 : range === "6m" ? 26 : 52; // approx weeks
  return all.slice(-nWeeks);
}

function App() {
  // 0 = this week, -1 = previous week, etc.
  const [weekOffset, setWeekOffset] = useState(0);
  const [mileage, setMileage] = useState<WeeklyMileagePoint[]>([]);
  const [isLoadingMileage, setIsLoadingMileage] = useState(true);
  const [mileageError, setMileageError] = useState<string | null>(null);
  const [range, setRange] = useState<MileageRange>("12w");
  const [runs, setRuns] = useState<Run[]>([]);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [runsError, setRunsError] = useState<string | null>(null);

  const chartData = useMemo(
    () => sliceMileageForRange(mileage, range),
    [mileage, range]
  );

  const avgMileage = useMemo(() => {
    if (chartData.length === 0) return 0;
    const total = chartData.reduce(
      (sum, pt) => sum + pt.total_mileage,
      0
    );
    return total / chartData.length;
  }, [chartData]);

  const monthLabelMap = useMemo(() => {
    let prevMonth = "";
    const map = new Map<string, string>();

    chartData.forEach((pt) => {
      const d = new Date(pt.week_start);
      const month = d
        .toLocaleString("en-US", { month: "short" })
        .toUpperCase();
      const label = month !== prevMonth ? month : "";
      prevMonth = month;
      map.set(pt.week_start, label);
    });

    return map;
  }, [chartData]);

  const weeklyDistance = runs.reduce((sum, run) => sum + run.distance_mi, 0);
  const { start: weekStart, end: weekEnd } = getWeekRange(weekOffset);

  const weeklyDayData = useMemo(
    () => buildWeekDaySeries(runs, weekStart),
    [runs, weekStart]
  );

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
        // Fetch up to 52 weeks so the front-end can slice for 12w / 6m / 1y ranges
        const data = await getWeeklyMileage(52);
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
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          <span className="inline-block px-6 py-2 rounded-full bg-sky-500/10 text-sky-300 shadow-lg shadow-sky-500/30 border border-sky-500/40">
            Runner Dashboard
          </span>
        </h1>
        <p className="text-slate-400 mt-4">
          12-week mileage &amp; weekly training log
        </p>
      </header>

      <main className="max-w-5xl mx-auto px-4 pb-12 space-y-8">
        {/* GRAPHS ROW */}
        <section className="space-y-2">
          {/* Graph cards */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* WEEKLY MILEAGE CARD */}
            <div className="bg-slate-800/80 border border-slate-700 rounded-2xl shadow-lg shadow-black/40 p-4">
              <div className="flex items-baseline justify-between gap-3 mb-2">
                <div className="flex items-center gap-3">
                  <h2 className="font-semibold text-slate-100">
                    Weekly mileage
                  </h2>
                  {/* Compact range pill inside the card */}
                  <div className="inline-flex rounded-full bg-slate-900/60 p-1 border border-slate-700/80">
                    {(["12w", "6m", "1y"] as MileageRange[]).map((r) => (
                      <button
                        key={r}
                        onClick={() => setRange(r)}
                        className={`px-2.5 py-0.5 text-[11px] md:text-xs rounded-full transition ${
                          range === r
                            ? "bg-sky-500 text-slate-900 font-semibold"
                            : "bg-transparent text-slate-300 hover:bg-slate-700/60"
                        }`}
                      >
                        {r === "12w" && "12w"}
                        {r === "6m" && "6m"}
                        {r === "1y" && "1y"}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-xs text-slate-400">
                  Avg:{" "}
                  <span className="text-sky-300 font-semibold">
                    {avgMileage.toFixed(1)} mi/week
                  </span>
                </p>
              </div>
              <div className="mt-4 h-64">
                {isLoadingMileage ? (
                  <p className="text-slate-500 text-sm">Loading mileage...</p>
                ) : mileageError ? (
                  <p className="text-red-400 text-sm">{mileageError}</p>
                ) : chartData.length === 0 ? (
                  <p className="text-slate-500 text-sm">No mileage data yet.</p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                      data={chartData}
                      margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis
                        dataKey="week_start"
                        tickFormatter={(value: string) =>
                          monthLabelMap.get(value) ?? ""
                        }
                        tick={{ fontSize: 12, fill: "#94a3b8" }}
                        dy={8}
                      />
                      <YAxis
                        tick={{ fontSize: 12, fill: "#94a3b8" }}
                        tickFormatter={(value: number) => value.toFixed(1)}
                        width={40}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#020617",
                          borderColor: "#1e293b",
                          borderRadius: 8,
                        }}
                        labelFormatter={(value: string) => `Week of ${value}`}
                        formatter={(value: number) => [
                          `${value.toFixed(2)} mi`,
                          "Mileage",
                        ]}
                      />
                      {/* Filled area under the line */}
                      <Area
                        type="monotone"
                        dataKey="total_mileage"
                        stroke="none"
                        fill="#38bdf822"
                      />
                      <Line
                        type="monotone"
                        dataKey="total_mileage"
                        stroke="#38bdf8"
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* WEEKLY MILEAGE BY DAY CARD */}
            <div className="bg-slate-800/80 border border-slate-700 rounded-2xl shadow-lg shadow-black/40 p-4">
              <div className="flex items-baseline justify-between gap-3 mb-2">
                <h2 className="font-semibold text-slate-100">
                  This week&apos;s mileage by day
                </h2>
                <p className="text-xs text-slate-400">
                  Week total:&nbsp;
                  <span className="text-sky-300 font-semibold">
                    {weeklyDistance.toFixed(2)} mi
                  </span>
                </p>
              </div>
              <div className="mt-4 h-64">
                {isLoadingRuns ? (
                  <p className="text-slate-500 text-sm">
                    Loading weekly graph...
                  </p>
                ) : runsError ? (
                  <p className="text-red-400 text-sm">{runsError}</p>
                ) : weeklyDayData.length === 0 ? (
                  <p className="text-slate-500 text-sm">
                    No runs logged for this week.
                  </p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={weeklyDayData}
                      margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#1e293b"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="label"
                        tick={{ fontSize: 12, fill: "#94a3b8" }}
                      />
                      <YAxis
                        tick={{ fontSize: 12, fill: "#94a3b8" }}
                        tickFormatter={(value: number) => value.toFixed(1)}
                        width={40}
                      />
                      <Tooltip
                        cursor={false} // remove big white hover rectangle
                        contentStyle={{
                          backgroundColor: "#020617",
                          borderColor: "#1e293b",
                          borderRadius: 8,
                        }}
                        labelFormatter={(_, payload) =>
                          payload && payload[0]
                            ? `Date: ${payload[0].payload.date}`
                            : ""
                        }
                        formatter={(value: number) => [
                          `${value.toFixed(2)} mi`,
                          "Mileage",
                        ]}
                      />
                      <Bar
                        dataKey="total"
                        fill="#38bdf8"
                        radius={[4, 4, 0, 0]}
                        // subtle glow on hover
                        activeBar={{
                          fill: "#38bdf8",
                          stroke: "#e0f2fe",
                          strokeWidth: 2,
                        }}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
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
                      Click to view details (HR, pace, elevation, GPS) — coming
                      soon
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