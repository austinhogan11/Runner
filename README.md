# Runner
Running Log &amp; Race Predictor

# 1 App Overview
- Single Page Running Dashboard
    - Mileage Trends
    - Running Activity Log
- Frontend
    - ReactJS
    - TailwindCSS
- Backend
    - Python / FastAPI
        - CRUD
            - POST /runs
            - GET /runs?
            - GET /runs?start_date=&end_date= (for weekly window)
	        - PUT /runs/{id}
	        - DELETE /runs/{id}
        - Aggregates for charts:
	        GET /stats/weekly-mileage?weeks=12
- DB
    - PostgreSQL
        - Schema
            - date
            - title
            - notes
            - distance mi
            - duration HH:MM:SS
            - pace 6:30/mi

# Runner Project – Build Log

This document tracks the major steps taken to build the **Runner** app
(FastAPI backend + React/TypeScript/Tailwind frontend).

---

## 1. Backend scaffolding

- Created `backend/` folder and Python virtualenv.
- Installed core dependencies:

  - `fastapi`, `uvicorn[standard]`
  - `SQLAlchemy`
  - `psycopg2-binary`
  - `python-dotenv`
  - `pydantic-settings` (for Pydantic v2 config)

- Added `requirements.txt` and froze initial deps.

---

## 2. Core app structure

Created the following modules under `app/`:

- `app/main.py` – FastAPI app entrypoint.
- `app/core/config.py` – application settings using `BaseSettings` from `pydantic-settings`.
- `app/db.py` – database engine, `SessionLocal`, and `Base` using SQLAlchemy.
- `app/models/run.py` – SQLAlchemy `Run` model.
- `app/schemas/run.py` – Pydantic schemas for request/response (`RunCreate`, `RunRead`, etc.).
- `app/api/runs.py` – router with CRUD + extra endpoints.
- `app/utils/time.py` – helpers for parsing/formatting durations and computing paces.

---

## 3. Database setup

- Ran PostgreSQL locally (via Docker container named `runner-postgres`).
- Created database `runner`.
- Set `DATABASE_URL` in `.env`, e.g.:

  ```env
  DATABASE_URL=postgresql://postgres:password@localhost:5432/runner