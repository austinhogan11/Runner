# Architecture

High‑level map of the Runner app.

## Backend (FastAPI)

- `app/main.py` – app, CORS, router registration; creates tables on startup.
- `app/core/config.py` – environment configuration (DB URL, uploads dir, timezone, HR settings).
- `app/core/time_utils.py` – HH:MM:SS ↔ seconds, HH:MM ↔ time, tz conversion.
- `app/db.py` – SQLAlchemy engine/session/Base.
- `app/models/`:
  - `Run` – primary activity row (date, title, notes, distance_mi, duration_seconds, run_type, start_time, source,...)
  - `RunFile` – uploaded files metadata (filename, path, processed flag)
  - `RunMetrics` – aggregates: elev gain/loss, moving time, avg/max HR, HR zones, downsampled series
  - `RunSplit` – per‑split rows (mile splits currently)
  - `RunTrack` – track GeoJSON + bounds (#points)
  - `WeeklyGoal` – weekly mileage goals (by Monday)
- `app/schemas/` – Pydantic v2 schemas (RunCreate/Read/Update, Goal, etc).
- `app/api/runs.py` – CRUD, list, stats, GPX/FIT import, metrics/splits/track endpoints.
- `alembic/` – migrations for model changes.

### Import pipeline

1. `POST /runs/import` saves the file to `uploads/` and creates a `Run` row with inferred stats.
2. Background task parses the file:
   - GPX: builds track, moving‑time mile splits, elevation gain/loss
   - FIT: prefers device laps for splits (timer time), builds track if GPS exists, HR/pace series + zones
3. Data is persisted into `RunTrack`, `RunSplit`, `RunMetrics`.

## Frontend (React + Vite + Tailwind)

- `src/App.tsx` – main dashboard + weekly log + run details panel
- `src/api.ts` – typed API client
- `src/components/RunMap.tsx` – Leaflet map (Carto Dark Matter tiles) with route polyline

### Details view

Left column: route map; Right column: Tabs (Splits, Heart rate). HR tab shows a donut chart; splits show a compact table with time/pace/elev.

## Data flow

Frontend requests a week range and weekly mileage series; it also requests per‑run resources on demand (splits, metrics, series, track) when the Details panel opens.

