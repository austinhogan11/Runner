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

// -------- API Functions -------- //
export async function getWeeklyMileage(): Promise<WeeklyMileagePoint[]> {
  const res = await fetch(`${API_URL}/runs/weekly_mileage`);
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