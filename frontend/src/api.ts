export const API_URL = "http://127.0.0.1:8000";

// -------- Types -------- //
export interface WeeklyMileagePoint {
  week_start: string;
  total_mileage: number;
}

export interface WeeklyGoal {
  week_start: string;
  goal_miles: number;
  notes?: string | null;
}

export interface Run {
  id: number;
  date: string;
  start_time?: string | null;
  title: string;
  notes: string | null;
  distance_mi: number;
  duration: string;
  run_type: string;
  pace: string;
}

export interface RunCreate {
  date: string;
  start_time?: string | null;
  title: string;
  notes: string;
  distance_mi: number;
  duration: string;
  run_type: string;
  pace: string;
}

// -------- API Functions -------- //
export async function getWeeklyMileage(
  maxWeeks: number = 52
): Promise<WeeklyMileagePoint[]> {
  const url = new URL(`${API_URL}/runs/weekly_mileage`);
  url.searchParams.set("weeks", String(maxWeeks));

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error("Failed to fetch weekly mileage");
  }
  return res.json();
}

export async function getRunsInRange(
  start: string,
  end: string,
  opts?: { run_type?: string }
): Promise<Run[]> {
  const url = new URL(`${API_URL}/runs/`);
  url.searchParams.set("start_date", start);
  url.searchParams.set("end_date", end);
  if (opts?.run_type && opts.run_type !== "all") {
    url.searchParams.set("run_type", opts.run_type);
  }

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch runs");
  }
  return res.json();
}

export async function createRun(payload: RunCreate): Promise<Run> {
  const res = await fetch(`${API_URL}/runs/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("Failed to create run");
  }

  return res.json();
}

// ------- Goals API ------- //
export async function getWeeklyGoal(weekStart: string): Promise<WeeklyGoal | null> {
  const res = await fetch(`${API_URL}/goals/${weekStart}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch weekly goal");
  return res.json();
}

export async function upsertWeeklyGoal(weekStart: string, data: { goal_miles: number; notes?: string }): Promise<WeeklyGoal> {
  const res = await fetch(`${API_URL}/goals/${weekStart}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save weekly goal");
  return res.json();
}

export async function updateRun(id: number, data: Partial<Run>): Promise<Run> {
  const res = await fetch(`${API_URL}/runs/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update run");
  return res.json();
}

export async function deleteRun(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/runs/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete run");
}

export async function importRun(file: File): Promise<Run> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/runs/import`, { method: "POST", body: form });
  if (!res.ok) throw new Error("Failed to import GPX");
  return res.json();
}
