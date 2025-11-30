# API quick reference

Base URL: `http://127.0.0.1:8000`

## Runs

- `POST /runs/` – create manual run
- `GET /runs/?start_date=&end_date=&run_type=` – list runs
- `PUT /runs/{id}` – update fields
- `DELETE /runs/{id}` – delete run
- `GET /runs/weekly_mileage?weeks=12` – weekly mileage series
- `GET /runs/stats?start_date=&end_date=` – aggregates

### Import

- `POST /runs/import` (multipart)
  - file: `.fit` or `.gpx`
  - Creates a `Run` and triggers background processing

### Reprocess

- `POST /runs/{id}/reprocess`
  - Rebuilds splits, metrics, series, and track from the stored file(s).
  - Preference order: FIT > GPX. Returns `{ message, run_id, file, source }`.

### Details endpoints

- `GET /runs/{id}/track` – GeoJSON + bounds + points_count
- `GET /runs/{id}/splits` – `[ { idx, distance_mi, duration_sec, avg_hr?, max_hr?, elev_gain_ft? } ]`
- `GET /runs/{id}/metrics` – `{ avg_hr?, max_hr?, elev_gain_ft?, elev_loss_ft?, moving_time_sec?, device?, hr_zones? }`
- `GET /runs/{id}/series` – `{ hr_series: [{t,hr}], pace_series: [{t, pace_s_per_mi}] }`

## Goals

## Strava (optional)

Environment variables in `backend/.env`:

- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI` (e.g., `http://127.0.0.1:8000/strava/callback`)

Endpoints:

- `GET /strava/auth_url` → returns the OAuth URL; open it in a browser and authorize.
- `GET /strava/callback?code=...` → Strava redirects here; backend stores tokens under `uploads/strava/tokens.json`.
- `POST /strava/sync?weeks=12&types=Run&max_activities=50` → pulls the last N weeks, filtered by activity `types` (comma-separated, default `Run`). Optional `max_activities` caps work per call to stay under minute limits. The endpoint respects Strava rate-limit headers and will stop early when close to the 100/15m cap; run it again to continue.

- Date window + pagination:
  - `POST /strava/sync?start_date=2025-11-01&end_date=2025-12-01&types=Run&max_activities=50&start_page=1`
  - To pull the next page: same query with `start_page=2` (and so on). Use `max_activities<=50` to make `per_page` = 50.

- `GET /goals/weekly?start_date=&end_date=` – list goals for a range
- `GET /goals/{week_start}` – single week goal (404 if not set)
- `PUT /goals/{week_start}` – upsert `{ goal_miles, notes? }`
