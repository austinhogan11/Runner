#!/usr/bin/env python3
"""
Seed 16 weeks of training data into the Runner API.

Pattern per week (Mon–Sun):
  - Mon: easy
  - Tue: easy
  - Wed: workout ("marathon workout")
  - Thu: easy
  - Fri: easy
  - Sat: long run
  - Sun: rest

Weekly mileage plan (16 weeks total):
  Build from 30 → 70 by week 12, hold 70 for 2 weeks, then taper.
  [30,33,36,39,42,45,48,52,56,60,65,70,70,70,50,35]

Usage examples:
  - Against Ingress (external IP/host):
      python projects/Runner/scripts/seed_16_weeks.py --base-url http://<EXTERNAL-IP>/api
  - Against port-forwarded backend:
      kubectl -n runner port-forward svc/runner-runner-backend 8080:80 &
      python projects/Runner/scripts/seed_16_weeks.py --base-url http://localhost:8080
  - Against cluster-internal service (from a machine with network access):
      python ... --base-url http://runner-runner-backend.runner.svc.cluster.local
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from typing import List, Tuple

try:
    import requests  # type: ignore
except Exception as exc:  # pragma: no cover
    print("This script requires the 'requests' package.\nInstall with: pip install requests", file=sys.stderr)
    raise


WEEKLY_MILES = [30, 33, 36, 39, 42, 45, 48, 52, 56, 60, 65, 70, 70, 70, 50, 35]


def monday_of_week(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def round1(x: float) -> float:
    return round(x + 1e-9, 1)


def pace_duration(distance_mi: float, pace_min_per_mile: float) -> str:
    minutes = distance_mi * pace_min_per_mile
    total_seconds = int(minutes * 60)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def split_weekly_dist(total: float) -> Tuple[float, float, List[float]]:
    """Return long_run, workout, list_of_four_easy distances summing to total."""
    long_run = round1(total * 0.30)
    workout = round1(total * 0.20)
    easy_total = round1(total - long_run - workout)
    # Split easy into 4 roughly equal parts
    base = round1(easy_total / 4.0)
    easies = [base, base, base, base]
    # Fix rounding drift on the last day
    diff = round1(easy_total - round1(sum(easies)))
    easies[-1] = round1(easies[-1] + diff)
    # Safety: ensure non-negative
    easies = [max(0.1, e) for e in easies]
    return long_run, workout, easies


def post_json(base_url: str, path: str, payload: dict) -> None:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    r = requests.request("PUT" if path.startswith("goals/") else "POST", url, json=payload, timeout=15)
    if r.status_code >= 300:
        raise RuntimeError(f"{path} -> HTTP {r.status_code}: {r.text}")


def seed_week(base_url: str, week_start: dt.date, target_mi: float) -> None:
    # Goal
    post_json(base_url, f"goals/{week_start.isoformat()}", {"goal_miles": round1(target_mi)})

    long_mi, workout_mi, easies = split_weekly_dist(target_mi)

    # Days mapping
    days = {
        0: ("Easy", easies[0], 9.0, "easy"),
        1: ("Easy", easies[1], 9.0, "easy"),
        2: ("Marathon Workout", workout_mi, 7.0, "workout"),
        3: ("Easy", easies[2], 9.0, "easy"),
        4: ("Easy", easies[3], 9.0, "easy"),
        5: ("Long Run", long_mi, 8.5, "long"),
        # 6=Sunday off
    }

    for dow, (title, miles, pace, rtype) in days.items():
        run_date = week_start + dt.timedelta(days=dow)
        duration = pace_duration(miles, pace)
        payload = {
            "date": run_date.isoformat(),
            "title": f"{title} {miles:.1f}mi",
            "notes": "seed",
            "distance_mi": round1(miles),
            "duration": duration,
            "run_type": rtype,
        }
        post_json(base_url, "runs/", payload)


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed 16 weeks of runs and weekly goals")
    ap.add_argument("--base-url", required=True, help="API base URL (e.g., http://<IP>/api or http://localhost:8080)")
    ap.add_argument("--include-current-week", action="store_true", help="Include the current week (default yes)")
    args = ap.parse_args()

    base_url = args.base_url

    today = dt.date.today()
    this_monday = monday_of_week(today)

    # Generate 16 week starts ending with current week
    week_starts = [this_monday - dt.timedelta(weeks=15 - i) for i in range(16)]

    for ws, miles in zip(week_starts, WEEKLY_MILES):
        seed_week(base_url, ws, float(miles))

    print("Seed complete: 16 weeks created.")


if __name__ == "__main__":
    main()

