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

### Details endpoints

- `GET /runs/{id}/track` – GeoJSON + bounds + points_count
- `GET /runs/{id}/splits` – `[ { idx, distance_mi, duration_sec, avg_hr?, max_hr?, elev_gain_ft? } ]`
- `GET /runs/{id}/metrics` – `{ avg_hr?, max_hr?, elev_gain_ft?, elev_loss_ft?, moving_time_sec?, device?, hr_zones? }`
- `GET /runs/{id}/series` – `{ hr_series: [{t,hr}], pace_series: [{t, pace_s_per_mi}] }`

## Goals

- `GET /goals/weekly?start_date=&end_date=` – list goals for a range
- `GET /goals/{week_start}` – single week goal (404 if not set)
- `PUT /goals/{week_start}` – upsert `{ goal_miles, notes? }`

