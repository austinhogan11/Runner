from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.config import settings
from app.models.run import Run
from app.models.run_track import RunTrack
from app.models.run_metrics import RunMetrics
from app.models.run_split import RunSplit
from app.core.time_utils import compute_pace, seconds_to_hhmmss, hhmm_to_time
from app.core.constants import HR_ZONE_BOUNDS, MILE_M, SAMPLE_STEP_M, MOVING_SPEED_MPS
from app.api.runs import _haversine
import os, json, time, math
import httpx
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/strava", tags=["strava"])


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _infer_run_type_from_strava(activity: dict) -> str:
    """Map Strava fields to our run_type.

    Strava has `workout_type` on run activities:
      0 or None = default, 1 = race, 2 = long run, 3 = workout
    We also fall back to heuristics based on title and distance.
    """
    wt = activity.get("workout_type")
    name = (activity.get("name") or "").lower()
    dist_m = float(activity.get("distance") or 0.0)
    miles = dist_m / 1609.34 if dist_m else 0.0

    if wt == 1:
        return "race"
    if wt == 2:
        return "long"
    if wt == 3:
        return "workout"

    # Title heuristics
    race_terms = ["race", "marathon", "half marathon", "10k", "5k", "5 km", "10 km"]
    if any(t in name for t in race_terms):
        return "race"
    if "workout" in name or "interval" in name or "tempo" in name:
        return "workout"
    if "long" in name or "lr" in name:
        return "long"

    # Distance heuristic for long run (only when reasonably big)
    if miles >= 12.0:
        return "long"
    return "easy"


@router.get("/auth_url")
def get_auth_url():
    if not (settings.strava_client_id and settings.strava_redirect_uri):
        raise HTTPException(status_code=400, detail="Strava client not configured")
    base = "https://www.strava.com/oauth/authorize"
    params = {
        "client_id": settings.strava_client_id,
        "redirect_uri": settings.strava_redirect_uri,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "read,activity:read_all",
    }
    from urllib.parse import urlencode
    return {"url": f"{base}?{urlencode(params)}"}


@router.get("/callback")
def oauth_callback(code: str):
    if not (settings.strava_client_id and settings.strava_client_secret):
        raise HTTPException(status_code=400, detail="Strava client not configured")
    data = {
        "client_id": settings.strava_client_id,
        "client_secret": settings.strava_client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }
    with httpx.Client(timeout=30) as client:
        r = client.post("https://www.strava.com/oauth/token", data=data)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Strava auth failed: {r.text}")
        tok = r.json()
    _ensure_dir(settings.strava_tokens_path)
    with open(settings.strava_tokens_path, "w") as f:
        json.dump(tok, f)
    return {"message": "Strava linked. You can close this window."}


def _load_tokens():
    try:
        with open(settings.strava_tokens_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _save_tokens(tok):
    _ensure_dir(settings.strava_tokens_path)
    with open(settings.strava_tokens_path, "w") as f:
        json.dump(tok, f)


def _refresh_if_needed(tok):
    now = int(time.time())
    if tok.get("expires_at", 0) - now > 60:
        return tok
    data = {
        "client_id": settings.strava_client_id,
        "client_secret": settings.strava_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": tok.get("refresh_token"),
    }
    with httpx.Client(timeout=30) as client:
        r = client.post("https://www.strava.com/oauth/token", data=data)
        r.raise_for_status()
        nt = r.json()
    _save_tokens(nt)
    return nt


@router.post("/sync")
def sync_recent_runs(
    weeks: int = Query(12, ge=1, le=104, description="Ignored if start_date provided"),
    types: str = Query("Run", description="Comma-separated Strava activity types to import (default: Run)"),
    max_activities: int | None = Query(None, ge=1, description="Optional hard cap of activities to import this call"),
    start_date: str | None = Query(None, description="YYYY-MM-DD (inclusive). Overrides weeks when set."),
    end_date: str | None = Query(None, description="YYYY-MM-DD (exclusive). Optional with start_date."),
    start_page: int = Query(1, ge=1, description="Start page when paginating a date window"),
    db: Session = Depends(get_db),
):
    tok = _load_tokens()
    if not tok:
        raise HTTPException(status_code=400, detail="Strava not linked. Hit /strava/auth_url first.")
    tok = _refresh_if_needed(tok)
    hdrs = {"Authorization": f"Bearer {tok['access_token']}"}
    # Build time window: prefer explicit dates
    if start_date:
        sd = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        after = int(sd.timestamp())
        if end_date:
            ed = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            before = int(ed.timestamp())
        else:
            before = None
    else:
        after = int(time.time() - weeks * 7 * 86400)
        before = None

    imported = 0
    # Decide per_page optimally for pagination
    per_page = 200
    if max_activities and max_activities < per_page:
        per_page = max(1, min(200, max_activities))

    pages = start_page
    allowed_types = {t.strip() for t in types.split(",") if t.strip()}

    def _check_limits(resp):
        ml = resp.headers.get("X-RateLimit-Limit")
        mu = resp.headers.get("X-RateLimit-Usage")
        try:
            minute_limit, day_limit = [int(x) for x in ml.split(",")] if ml else (100, 1000)
            minute_used, day_used = [int(x) for x in mu.split(",")] if mu else (0, 0)
        except Exception:
            minute_limit, day_limit, minute_used, day_used = 100, 1000, 0, 0
        return minute_limit, minute_used, day_limit, day_used
    with httpx.Client(timeout=60, headers=hdrs) as client:
        while True:
            params = {"after": after, "per_page": per_page, "page": pages}
            if before:
                params["before"] = before
            r = client.get("https://www.strava.com/api/v3/athlete/activities", params=params)
            if r.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Strava list activities failed: {r.text}")
            acts = r.json()
            # Stop early if approaching minute limit
            mlim, mused, _, _ = _check_limits(r)
            if mused >= max(1, mlim - 5):
                break
            if not acts:
                break
            for a in acts:
                if allowed_types and a.get("type") not in allowed_types:
                    continue
                act_id = a.get("id")
                start_local = a.get("start_date_local")
                start_dt = datetime.fromisoformat(start_local.replace("Z", "+00:00")) if start_local else None
                dist_m = float(a.get("distance") or 0.0)
                dur_s = int(a.get("moving_time") or 0)
                miles = dist_m / 1609.34
                title = a.get("name") or "Strava Run"
                inferred_type = _infer_run_type_from_strava(a)

                # naive dedupe: same date + duration + distance rounded
                date_only = start_dt.date() if start_dt else None
                existing = (
                    db.query(Run)
                    .filter(Run.date == date_only)
                    .filter(Run.duration_seconds == dur_s)
                    .filter(Run.distance_mi == round(miles, 2))
                    .first()
                )
                if existing:
                    # Update run_type if we can infer and the run looks auto-imported/easy
                    if inferred_type and existing.source in ("strava", "manual", None):
                        if not existing.run_type or existing.run_type in ("easy", "other"):
                            existing.run_type = inferred_type
                            db.commit()
                    continue

                run = Run(
                    date=date_only or datetime.utcnow().date(),
                    title=title,
                    notes=None,
                    distance_mi=round(miles, 2),
                    duration_seconds=dur_s,
                    run_type=inferred_type or "easy",
                    start_time=hhmm_to_time(start_dt.strftime("%H:%M")) if start_dt else None,
                    source="strava",
                )
                db.add(run)
                db.commit(); db.refresh(run)

                # Streams for track + metrics
                keys = ["time","latlng","altitude","heartrate","velocity_smooth"]
                sr = client.get(f"https://www.strava.com/api/v3/activities/{act_id}/streams", params={"keys": ",".join(keys), "key_by_type": True})
                if sr.status_code != 200:
                    continue
                streams = sr.json()
                # Rate limited? Bail gracefully; user can call sync again.
                mlim2, mused2, _, _ = _check_limits(sr)
                if mused2 >= max(1, mlim2 - 5):
                    db.commit()
                    return {"imported": imported, "note": "rate limit reached; run sync again to continue"}
                time_s = streams.get("time", {}).get("data") or []
                latlng = streams.get("latlng", {}).get("data") or []
                altitude = streams.get("altitude", {}).get("data") or []
                heartrate = streams.get("heartrate", {}).get("data") or []
                vel = streams.get("velocity_smooth", {}).get("data") or []

                # Build points and geojson
                points = []
                total_m = 0.0
                elev_gain = 0.0
                elev_loss = 0.0
                prev = None
                for i, ll in enumerate(latlng):
                    lat, lon = ll
                    ele = float(altitude[i]) if i < len(altitude) else None
                    t = int(time_s[i]) if i < len(time_s) else None
                    points.append({"lat": lat, "lon": lon, "ele": ele, "t": t, "time": None})
                    if prev is not None:
                        total_m += _haversine(prev[0], prev[1], lat, lon)
                        if ele is not None and prev[2] is not None:
                            de = ele - prev[2]
                            if de > 0: elev_gain += de
                            else: elev_loss += -de
                    prev = (lat, lon, ele)

                if points:
                    lats = [p["lat"] for p in points]
                    lons = [p["lon"] for p in points]
                    bounds = {"minLat": min(lats), "minLon": min(lons), "maxLat": max(lats), "maxLon": max(lons)}
                    coords = [[p["lon"], p["lat"]] for p in points]
                    geojson = {"type": "LineString", "coordinates": coords}
                else:
                    bounds = None; geojson = None

                track = db.query(RunTrack).filter(RunTrack.run_id == run.id).first() or RunTrack(run_id=run.id)
                track.geojson = geojson; track.bounds = bounds; track.points_count = len(points)
                db.add(track)

                # Splits by distance using moving time
                target_m = MILE_M
                acc_m = 0.0
                seg_elapsed = 0.0
                splits = []
                sample_step_m = SAMPLE_STEP_M
                next_sample_m = sample_step_m

                hr_dist_series = []
                pace_dist_series = []
                elev_dist_series = []
                cumulative_m = 0.0

                for i in range(1, len(points)):
                    a, b = points[i-1], points[i]
                    d = _haversine(a["lat"], a["lon"], b["lat"], b["lon"]) if a and b else 0.0
                    dt = 0.0
                    if a.get("t") is not None and b.get("t") is not None:
                        dt = float(b["t"] - a["t"]) if b["t"] >= a["t"] else 0.0
                    moving_dt = dt
                    if vel and i < len(vel) and vel[i] is not None and vel[i] < MOVING_SPEED_MPS:
                        moving_dt = 0.0

                    acc_before = acc_m
                    acc_m += d
                    cumulative_m += d
                    while cumulative_m >= next_sample_m:
                        d_mi = next_sample_m / 1609.34
                        if dt > 0 and d > 0:
                            pace = int(1609.34 * (dt / d))
                            pace_dist_series.append({"d": round(d_mi,3), "pace_s_per_mi": pace})
                        if b.get("ele") is not None:
                            elev_dist_series.append({"d": round(d_mi,3), "elev_ft": int(float(b["ele"]) * 3.28084)})
                        if heartrate and i < len(heartrate) and heartrate[i] is not None:
                            hr_dist_series.append({"d": round(d_mi,3), "hr": int(heartrate[i])})
                        next_sample_m += sample_step_m

                    rem_d = d
                    rem_moving_dt = moving_dt
                    while acc_before + rem_d >= target_m:
                        needed = target_m - acc_before
                        frac = (needed / rem_d) if rem_d > 0 else 0.0
                        seg_elapsed += rem_moving_dt * frac
                        splits.append({"idx": len(splits)+1, "distance_mi": 1.0, "duration_sec": int(seg_elapsed) if seg_elapsed>0 else 0})
                        rem_d -= needed
                        rem_moving_dt = rem_moving_dt * (1 - frac)
                        acc_before = 0.0
                        acc_m -= target_m
                        seg_elapsed = 0.0
                    seg_elapsed += rem_moving_dt

                db.query(RunSplit).filter(RunSplit.run_id == run.id).delete()
                for s in splits:
                    db.add(RunSplit(run_id=run.id, idx=s["idx"], distance_mi=s["distance_mi"], duration_sec=s["duration_sec"]))

                m = db.query(RunMetrics).filter(RunMetrics.run_id == run.id).first() or RunMetrics(run_id=run.id)
                m.elev_gain_ft = float(elev_gain) * 3.28084 if elev_gain else None
                m.elev_loss_ft = float(elev_loss) * 3.28084 if elev_loss else None
                m.moving_time_sec = int(sum(s["duration_sec"] for s in splits)) if splits else None
                m.hr_dist_series = hr_dist_series
                m.pace_dist_series = pace_dist_series
                m.elev_dist_series = elev_dist_series

                # HR zones from streams when available
                if heartrate and time_s and len(heartrate) == len(time_s):
                    hr_max = settings.hr_max or (220 - settings.age)
                    zone_bounds = HR_ZONE_BOUNDS
                    zones = [0, 0, 0, 0, 0]
                    max_hr = 0
                    sum_hr = 0
                    count_hr = 0
                    for i in range(1, len(time_s)):
                        dt = max(1, int(time_s[i]) - int(time_s[i-1]))
                        hr_val = int(heartrate[i-1]) if heartrate[i-1] is not None else None
                        if hr_val is not None:
                            sum_hr += hr_val
                            count_hr += 1
                            if hr_val > max_hr:
                                max_hr = hr_val
                            frac = (hr_val / hr_max) if hr_max else 0
                            for z in range(5):
                                if zone_bounds[z] <= frac < zone_bounds[z+1]:
                                    zones[z] += dt
                                    break
                    if count_hr > 0:
                        m.avg_hr = int(sum_hr / count_hr)
                        m.max_hr = int(max_hr)
                        m.hr_zones = {"z1": zones[0], "z2": zones[1], "z3": zones[2], "z4": zones[3], "z5": zones[4], "hr_max": hr_max}
                db.add(m)

                imported += 1
                db.commit()
                if max_activities and imported >= max_activities:
                    return {"imported": imported}

            pages += 1

    return {"imported": imported}
