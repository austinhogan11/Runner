from datetime import date, timedelta
import random

from app.db import SessionLocal
from app.models.run import Run


def hhmmss_to_seconds(hhmmss: str) -> int:
    """Convert HH:MM:SS string to total seconds."""
    parts = hhmmss.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid HH:MM:SS value: {hhmmss}")
    hours, minutes, seconds = map(int, parts)
    return hours * 3600 + minutes * 60 + seconds


def clear_recent_runs(db, days: int = 120) -> None:
    """Delete runs in the last N days so we can reseed cleanly."""
    cutoff = date.today() - timedelta(days=days)
    db.query(Run).filter(Run.date >= cutoff).delete()
    db.commit()


def seed_demo_runs(db) -> None:
    """Insert a 12-week block of demo runs (easy, workout, long)."""
    today = date.today()
    # Go back 11 full weeks + current week (12 total)
    start_day = today - timedelta(weeks=11)

    runs_to_add = []

    for week in range(12):
        week_start = start_day + timedelta(weeks=week)

        # Example: Tue easy, Thu workout/tempo, Sun long run
        tue = week_start + timedelta(days=1)
        thu = week_start + timedelta(days=3)
        sun = week_start + timedelta(days=6)

        easy_dist = round(random.uniform(4.0, 7.0), 1)
        workout_dist = round(random.uniform(6.0, 10.0), 1)
        long_dist = round(random.uniform(10.0, 18.0), 1)

        # Skip future weeks
        for d, title, dist, dur_str, notes in [
            (
                tue,
                "Easy run",
                easy_dist,
                "00:50:00",
                "Easy aerobic miles.",
            ),
            (
                thu,
                "Workout",
                workout_dist,
                "01:00:00",
                "Threshold / tempo workout.",
            ),
            (
                sun,
                "Long run",
                long_dist,
                "02:00:00",
                "Long run on rolling hills.",
            ),
        ]:
            if d > today:
                continue

            duration_seconds = hhmmss_to_seconds(dur_str)

            runs_to_add.append(
                Run(
                    date=d,
                    title=title,
                    notes=notes,
                    distance_mi=dist,
                    duration_seconds=duration_seconds,
                )
            )

    if runs_to_add:
        db.add_all(runs_to_add)
        db.commit()

    print(f"Seeded {len(runs_to_add)} demo runs")


def main():
    db = SessionLocal()
    try:
        clear_recent_runs(db, days=150)
        seed_demo_runs(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()