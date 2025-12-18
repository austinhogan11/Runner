# Runner

## Modern Training Log

### Features

#### 1. Weekly Training Log
- An easy to read running log for the week.
    - Set & Track your goal mileage for the week.
    - Week range is Monday-Sunday
    - Run cards feature metrics for quick observations
        - Title
        - Date & Time
        - Distance, Duration & Pace
    - Expand Run Cards to view detailed data if available.
        - GPS Data
        - Mile splits
        - Heart Rate, Pace, and Elevation data.
            - Time in Heart Rate Zones
            - Pace vs Elevation
            - HR vs Elevation
    - Add manual run entries
    - Import Garmin (.gpx/.fit) or Strava (.tcx) Runs
    - Edit & Delete runs
    - Filter runs by type
        - Easy
        - Workout
        - Race
        - Long Run
    - Easily navigate to previous training weeks.

#### 2. Training Visualizations

###### 2.1 Weekly Mileage Trends Graph
- 12 week, 6 month, or 1 year weekly mileage trends.
- Line graph showing week to week trends
- Displays your average weekly mileage for the time range.

###### 2.2 Current Week Mileage Graph
- A bar graph breaking down your daily mileage for the week being currently viewed.
- Total mileage for the week displayed.

## Tech

This is a lightweight, modern stack focused on fast local iteration and clear data flow from files/Strava → processing → charts.

### Frontend
- React + TypeScript + Vite
  - Vite for instant dev reload and small production bundles.
- Styling: Tailwind CSS utility classes (see `frontend/tailwind.config.js` and `src/index.css`).
- Charts: Recharts
  - Weekly mileage line/bar charts and distance‑indexed overlays (pace/HR vs elevation).
- Map: React‑Leaflet + Leaflet
  - Dark Carto basemap, route glow stroke, start/finish markers.
  - Distance bounds are computed on the backend and fit in the map on load.
- API client: thin fetch wrappers in `src/api.ts`
  - Environment aware: uses `VITE_API_URL` when set or defaults to `same-host:8000` (handy for Docker Compose).
  - Simple typed DTOs for runs, splits, metrics, series, and Strava helpers.

### Backend
- FastAPI (Python)
  - Clear, typed routes under `app/api/` (`runs`, `strava`, `goals`).
- Data modelling: SQLAlchemy ORM (`app/models/*`)
  - Core tables: `runs`, `run_files`, `run_track`, `run_splits`, `run_metrics`, `weekly_goal`.
  - Migrations via Alembic (see `alembic/` and `alembic/env.py`).
- Schemas: Pydantic v2
  - `RunCreate/RunRead/RunUpdate`, `WeeklyMileagePoint`, with lenient update handling.
- Processing pipeline
  - Import endpoints accept `.fit` (fitparse), `.gpx` (gpxpy), and `.tcx` (basic XML).
  - Builds: route GeoJSON + bounds, per‑mile splits (moving time or FIT laps), elevation metrics, downsampled time series.
  - Distance‑indexed series for charts: `hr_dist_series`, `pace_dist_series`, `elev_dist_series` (~0.1 mi sampling).
  - Heart‑rate zones computed with HR_MAX or 220 − AGE; available for FIT and Strava imports.
- Strava integration (`app/api/strava.py`)
  - OAuth link: `GET /strava/auth_url`, callback saves tokens under `uploads/strava/tokens.json`.
  - Sync: `POST /strava/sync` pulls activities via streams (lat/lng, altitude, heartrate, speed) and builds the same artifacts as file import.
  - Status: `GET /strava/status` indicates if tokens are present.
- Config & env
  - `app/core/config.py` (pydantic‑settings): `DATABASE_URL`, `TIMEZONE`, `AGE`, optional `HR_MAX`, uploads dir, and Strava client envs.
  - Reasonable defaults for local dev and Docker.

### Database
- PostgreSQL in development and production.
- For tests we use SQLite in‑memory via `DATABASE_URL=sqlite+pysqlite:///:memory:` to keep smoke tests fast.

### Packaging / Deploy
- Docker images for backend (Uvicorn) and frontend (Nginx serving Vite build).
- Docker Compose orchestrates:
  - Postgres with a named volume.
  - Backend with `/app/uploads` volume (persists imported files + Strava tokens).
  - Frontend built with `VITE_API_URL` passed in, or defaults to same‑host backend.
- See `docs/DEPLOY.md` for detailed steps and Strava one‑time linking instructions.

### Testing (minimal)
- Backend: `backend/tests/test_api_smoke.py`
  - Exercises `/` and a simple create/list run cycle with in‑memory SQLite.
- Frontend: Node’s built‑in `node:test` runner for pure utility functions in `src/lib/format.ts`.
  - Run with `npm run test` in `frontend/`.

