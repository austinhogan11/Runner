## Runner

A modern running log with weekly trends, quick entry, and rich activity details
(GPX/FIT import, splits, HR zones, and a dark basemap route view).

### Features

- Weekly dashboard with charts and a per‑week log
- CRUD for manual runs
- Run type taxonomy: easy / workout / long / race
- Import activities from GPX or FIT
  - FIT: uses device laps for accurate mile splits (timer time)
  - HR zones, HR/pace series, elevation gain/loss
- Goals: set weekly mileage targets with a progress bar
- Dark map for GPS routes (Leaflet + Carto Dark Matter)

### Stack

- Frontend: React + TypeScript + Tailwind + Vite
- Backend: FastAPI + SQLAlchemy + Pydantic v2
- DB: PostgreSQL
- Migrations: Alembic

---

## Quick start

### Backend

1) Create a venv and install deps

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure environment

Copy `.env.example` to `.env` and adjust if needed.

Important settings:

- `DATABASE_URL` – Postgres DSN
- `TIMEZONE` – IANA tz (e.g. `America/New_York`) or `local`
- `AGE` / `HR_MAX` – used to compute HR zones (if `HR_MAX` missing, uses `220 - AGE`)

3) Init DB and run the server

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm i
# if using the map view
npm i react-leaflet leaflet
npm run dev
```

By default the backend runs on `http://127.0.0.1:8000` and the frontend on `http://127.0.0.1:5173`.

---

## Key directories

- `backend/app/api/` – FastAPI routers (runs, goals)
- `backend/app/models/` – SQLAlchemy models (Run, RunFile, RunMetrics, RunSplit, RunTrack, WeeklyGoal)
- `backend/app/schemas/` – Pydantic request/response models
- `backend/app/core/` – configuration + time utilities
- `backend/alembic/` – migrations
- `frontend/src/` – React app
  - `components/RunMap.tsx` – Leaflet map for the route
  - `App.tsx` – dashboard + details UI

---

## Importing activities

Use the “Import GPX/FIT” button in the weekly header.

Backend behavior:

- GPX: builds a route LineString, moving‑time mile splits, and elevation metrics
- FIT: prefers device laps for splits (uses `total_timer_time`), builds HR/pace series and zones
- Timestamps are converted to `TIMEZONE` for start time + date

Endpoints of interest:

- `POST /runs/import` – accepts `.fit` or `.gpx` and creates a run
- `GET /runs/{id}/track` – GeoJSON + bounds for map
- `GET /runs/{id}/splits` – mile splits
- `GET /runs/{id}/metrics` – elevation, moving time, HR zones
- `GET /runs/{id}/series` – HR + pace time series (downsampled)

---

## Developer docs

See `docs/ARCHITECTURE.md` for a deeper overview and `docs/API.md` for endpoint details.

### Code style and notes

- Pydantic v2 is used (`model_config=from_attributes=True`)
- Splits use moving time only (stop time excluded)
- FIT laps are used when present for more accurate per‑mile pacing
- Leaflet dark tiles provide a modern map look; the route is layered for a neon glow

---

## Roadmap

- Workout/interval laps view (from FIT lap messages)
- Pace‑colored route
- Reprocess an activity from stored files (without re‑upload)
- Optional Garmin API integration (webhook ingestion)
