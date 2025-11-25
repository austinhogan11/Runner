export const API_URL = "http://127.0.0.1:8000";

// -------- Types -------- //
export interface WeeklyMileagePoint {
  week_start: string;
  total_mileage: number;
}

export interface Run {
  id: number;
  date: string;
  title: string;
  notes: string | null;
  distance_mi: number;
  duration: string;
  pace: string;
}

export interface RunCreate {
  date: string;
  title: string;
  notes: string;
  distance_mi: number;
  duration: string;
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
  end: string
): Promise<Run[]> {
  const url = new URL(`${API_URL}/runs/`);
  url.searchParams.set("start_date", start);
  url.searchParams.set("end_date", end);

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