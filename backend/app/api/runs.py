from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, Date
from app.schemas.run import RunCreate, RunRead, WeeklyMileagePoint, RunUpdate, RunType
from app.models.run import Run
from app.models.run_file import RunFile
from app.models.run_metrics import RunMetrics
from app.models.run_split import RunSplit
from app.models.run_track import RunTrack
from app.db import get_db
from app.core.time_utils import (
    hhmmss_to_seconds,
    compute_pace,
    seconds_to_hhmmss,
    hhmm_to_time,
    time_to_hhmm,
    to_local_datetime,
)
from app.core.config import settings
import os
import math
import gpxpy
import gpxpy.gpx
from fitparse import FitFile

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("/", response_model=RunRead)
def create_run(payload: RunCreate, db: Session = Depends(get_db)):
    # Convert duration string -> seconds
    duration_seconds = hhmmss_to_seconds(payload.duration)

    # Validate inputs
    if payload.distance_mi <= 0:
        raise HTTPException(status_code=422, detail="distance_mi must be > 0")

    # Parse optional start_time safely
    try:
        parsed_start = (
            hhmm_to_time(payload.start_time)
            if getattr(payload, "start_time", None)
            else None
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    run = Run(
        date=payload.date,
        title=payload.title,
        notes=payload.notes,
        distance_mi=payload.distance_mi,
        duration_seconds=duration_seconds,
        run_type=payload.run_type,
        start_time=parsed_start,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    # Compute pace for response
    pace = compute_pace(run.duration_seconds, run.distance_mi)

    # Convert seconds -> HH:MM:SS for the API response
    duration_hhmmss = seconds_to_hhmmss(run.duration_seconds)

    # Return using the schema format
    return RunRead(
        id=run.id,
        date=run.date,
        start_time=time_to_hhmm(run.start_time),
        title=run.title,
        notes=run.notes,
        distance_mi=run.distance_mi,
        duration=duration_hhmmss,
        run_type=run.run_type,
        source=run.source if hasattr(run, 'source') else None,
        pace=pace,
    )

@router.get("/", response_model=list[RunRead])
def list_runs(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    run_type: Optional[RunType] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List runs, optionally filtered by [start_date, end_date].

    This is what the weekly log will call:
      GET /runs?start_date=2025-01-06&end_date=2025-01-12
    """
    query = db.query(Run)

    if start_date is not None:
        query = query.filter(Run.date >= start_date)
    if end_date is not None:
        query = query.filter(Run.date <= end_date)
    if run_type is not None:
        query = query.filter(Run.run_type == run_type.value)

    # Most recent first
    runs = query.order_by(Run.date.desc()).all()

    results: list[RunRead] = []
    for run in runs:
        pace = compute_pace(run.duration_seconds, float(run.distance_mi))
        duration_hhmmss = seconds_to_hhmmss(run.duration_seconds)

        results.append(
            RunRead(
                id=run.id,
                date=run.date,
                start_time=time_to_hhmm(run.start_time),
                title=run.title,
                notes=run.notes,
                distance_mi=float(run.distance_mi),
                duration=duration_hhmmss,
                run_type=run.run_type,
                source=run.source if hasattr(run, 'source') else None,
                pace=pace,
            )
        )

    return results


@router.put("/{run_id}", response_model=RunRead)
def update_run(run_id: int, payload: RunUpdate, db: Session = Depends(get_db)):
    db_run = db.query(Run).filter(Run.id == run_id).first()
    if not db_run:
        raise HTTPException(status_code=404, detail="Run not found")

    # pydantic v2 prefers model_dump; dict() kept for v1 compat
    update_data = (
        payload.model_dump(exclude_unset=True)  # type: ignore[attr-defined]
        if hasattr(payload, "model_dump")
        else payload.dict(exclude_unset=True)
    )

    if "duration" in update_data and update_data["duration"] is not None:
        db_run.duration_seconds = hhmmss_to_seconds(update_data.pop("duration"))

    if "start_time" in update_data:
        val = update_data.pop("start_time")
        try:
            db_run.start_time = hhmm_to_time(val) if val else None
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    # Normalize types for known fields
    if "date" in update_data and isinstance(update_data["date"], str):
        update_data["date"] = date.fromisoformat(update_data["date"])  # type: ignore
    if "distance_mi" in update_data and isinstance(update_data["distance_mi"], str):
        try:
            update_data["distance_mi"] = float(update_data["distance_mi"])  # type: ignore
        except ValueError:
            raise HTTPException(status_code=422, detail="distance_mi must be a number")

    # Validate distance if present
    if "distance_mi" in update_data and update_data["distance_mi"] is not None:
        if float(update_data["distance_mi"]) <= 0:
            raise HTTPException(status_code=422, detail="distance_mi must be > 0")

    # Set other fields directly
    for key, value in update_data.items():
        setattr(db_run, key, value)

    db.commit()
    db.refresh(db_run)

    pace = compute_pace(db_run.duration_seconds, float(db_run.distance_mi))
    duration_hhmmss = seconds_to_hhmmss(db_run.duration_seconds)

    return RunRead(
        id=db_run.id,
        date=db_run.date,
        start_time=time_to_hhmm(db_run.start_time),
        title=db_run.title,
        notes=db_run.notes,
        distance_mi=float(db_run.distance_mi),
        duration=duration_hhmmss,
        run_type=db_run.run_type,
        source=db_run.source if hasattr(db_run, 'source') else None,
        pace=pace,
    )


@router.get("/stats")
def get_run_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Run)
    if start_date is not None:
        query = query.filter(Run.date >= start_date)
    if end_date is not None:
        query = query.filter(Run.date <= end_date)

    # Total miles
    total = query.with_entities(func.sum(Run.distance_mi)).scalar() or 0

    # By type
    rows = (
        query.with_entities(Run.run_type, func.sum(Run.distance_mi))
        .group_by(Run.run_type)
        .all()
    )

    by_type: dict[str, float] = {t: 0.0 for t in [e.value for e in RunType]}
    for t, s in rows:
        by_type[str(t)] = float(s or 0.0)

    return {
        "total_miles": float(total or 0.0),
        "by_type": by_type,
    }


# --------- File Upload + Processing (GPX) --------- #

def _haversine(lat1, lon1, lat2, lon2):
    """Return great‑circle distance in meters between two WGS84 points.

    Uses the standard haversine formula; sufficient for per‑point distances
    over a typical GPS activity track.
    """
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _process_gpx_file(db: Session, run_id: int, path: str):
    """Parse a GPX file and persist derived data for a run.

    - Track: GeoJSON LineString + bounds + point count
    - Splits: per‑mile using moving time only (speed >= MOVING_SPEED_MPS)
    - Metrics: elevation gain/loss (ft) and moving time
    """
    with open(path, "r", encoding="utf-8") as f:
        gpx = gpxpy.parse(f)

    points = []
    total_dist_m = 0.0
    elev_gain = 0.0
    elev_loss = 0.0
    last = None

    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                pt = {
                    "lat": p.latitude,
                    "lon": p.longitude,
                    "ele": p.elevation,
                    "time": p.time.isoformat() if p.time else None,
                }
                points.append(pt)
                if last is not None:
                    total_dist_m += _haversine(last[0], last[1], p.latitude, p.longitude)
                    if p.elevation is not None and last[2] is not None:
                        de = p.elevation - last[2]
                        if de > 0:
                            elev_gain += de
                        else:
                            elev_loss += -de
                last = (p.latitude, p.longitude, p.elevation)

    # Build track geojson and bounds
    if points:
        lats = [p["lat"] for p in points]
        lons = [p["lon"] for p in points]
        bounds = {
            "minLat": min(lats),
            "minLon": min(lons),
            "maxLat": max(lats),
            "maxLon": max(lons),
        }
        coords = [[p["lon"], p["lat"]] for p in points]
        geojson = {"type": "LineString", "coordinates": coords}
    else:
        bounds = None
        geojson = None

    # Save track
    track = db.query(RunTrack).filter(RunTrack.run_id == run_id).first()
    if not track:
        track = RunTrack(run_id=run_id)
        db.add(track)
    track.geojson = geojson
    track.bounds = bounds
    track.points_count = len(points)

    # Simple splits per mile by distance along series using timestamps if available
    # For MVP, approximate duration by time deltas; if missing timestamps, skip splits
    splits = []
    split_idx = 1
    target_m = 1609.34
    acc_m = 0.0
    last_time = None
    seg_elapsed = 0.0  # moving time accumulated for current split
    MOVING_SPEED_MPS = 0.5  # ~1.1 mph; below this we treat as stopped

    # Distance-indexed series for charts
    hr_dist_series: list[dict] = []  # GPX usually lacks HR but keep structure
    pace_dist_series: list[dict] = []
    elev_dist_series: list[dict] = []
    cumulative_m = 0.0
    sample_step_m = 160.934  # ~0.1 mi
    next_sample_m = sample_step_m

    # Flatten timestamps
    from datetime import datetime
    def parse_iso(ts):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
        except Exception:
            return None

    for i in range(1, len(points)):
        a, b = points[i-1], points[i]
        d = _haversine(a["lat"], a["lon"], b["lat"], b["lon"]) if a and b else 0.0
        ta, tb = parse_iso(a["time"]), parse_iso(b["time"])
        dt = (tb - ta).total_seconds() if ta and tb else 0.0
        moving_dt = 0.0
        if dt > 0 and d > 0:
            speed = d / dt
            if speed >= MOVING_SPEED_MPS:
                moving_dt = dt

        acc_before = acc_m
        acc_m += d
        cumulative_m += d

        # sample distance-indexed series if timestamps/elevation present
        while cumulative_m >= next_sample_m:
            d_mi = next_sample_m / 1609.34
            if dt > 0 and d > 0:
                pace = int(1609.34 * (dt / d))
                pace_dist_series.append({"d": d_mi, "pace_s_per_mi": pace})
            if b.get("ele") is not None:
                elev_dist_series.append({"d": d_mi, "elev_ft": int(float(b["ele"]) * 3.28084)})
            next_sample_m += sample_step_m

        # proportionally allocate moving time into each mile boundary crossed
        rem_d = d
        rem_moving_dt = moving_dt
        while acc_before + rem_d >= target_m:
            needed = target_m - acc_before
            frac = (needed / rem_d) if rem_d > 0 else 0.0
            seg_elapsed += rem_moving_dt * frac
            # close a split
            duration_sec = int(seg_elapsed) if seg_elapsed > 0 else 0
            splits.append({"idx": split_idx, "distance_mi": 1.0, "duration_sec": duration_sec})
            split_idx += 1
            # prepare remainder for next split
            rem_d -= needed
            rem_moving_dt = rem_moving_dt * (1 - frac)
            acc_before = 0.0
            acc_m -= target_m
            # start fresh timer for the new split
            seg_elapsed = 0.0

        # whatever remains stays in current split
        seg_elapsed += rem_moving_dt

    # Clear existing splits and reinsert
    db.query(RunSplit).filter(RunSplit.run_id == run_id).delete()
    for s in splits:
        db.add(RunSplit(run_id=run_id, idx=s["idx"], distance_mi=s["distance_mi"], duration_sec=s["duration_sec"]))

    # Metrics
    metrics = db.query(RunMetrics).filter(RunMetrics.run_id == run_id).first()
    if not metrics:
        metrics = RunMetrics(run_id=run_id)
        db.add(metrics)
    metrics.elev_gain_ft = float(elev_gain) * 3.28084 if elev_gain else None
    metrics.elev_loss_ft = float(elev_loss) * 3.28084 if elev_loss else None
    metrics.moving_time_sec = int(sum(s["duration_sec"] for s in splits)) if splits else None
    metrics.hr_dist_series = hr_dist_series
    metrics.pace_dist_series = pace_dist_series
    metrics.elev_dist_series = elev_dist_series

    db.commit()


def _gpx_basic_stats(path: str):
    """Return (date, start_time_hhmm, duration_seconds, distance_miles) from a GPX file.
    Falls back gracefully if timestamps are missing.
    """
    from datetime import datetime

    with open(path, "r", encoding="utf-8") as f:
        gpx = gpxpy.parse(f)

    first_time = None
    last_time = None
    total_m = 0.0
    first_date = None
    prev = None

    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                if p.time and first_time is None:
                    first_time = p.time
                    first_date = p.time.date()
                if p.time:
                    last_time = p.time
                if prev is not None:
                    total_m += _haversine(prev[0], prev[1], p.latitude, p.longitude)
                prev = (p.latitude, p.longitude)

    duration_seconds = int((last_time - first_time).total_seconds()) if first_time and last_time else 0
    distance_miles = total_m / 1609.34
    if first_time:
        local_first = to_local_datetime(first_time, settings.timezone)
        start_hhmm = local_first.strftime("%H:%M")
        first_date = local_first.date()
    else:
        start_hhmm = None
    return first_date, start_hhmm, duration_seconds, distance_miles and round(distance_miles, 2) or 0.0


def _semicircles_to_degrees(val):
    return val * (180 / 2**31) if val is not None else None


def _fit_basic_stats(path: str):
    """Extract (date, local_start_hhmm, duration_seconds, distance_miles) from FIT."""
    from datetime import timezone
    ff = FitFile(path)
    start_ts = None
    end_ts = None
    total_m = 0.0
    prev = None
    # Prefer session totals when present (covers treadmill with no GPS)
    session_distance_m = None
    session_elapsed_s = None
    session_timer_s = None
    for session in ff.get_messages("session"):
        fields = {f.name: f.value for f in session}
        if fields.get("total_distance") is not None and session_distance_m is None:
            session_distance_m = float(fields.get("total_distance"))
        if fields.get("total_elapsed_time") is not None and session_elapsed_s is None:
            session_elapsed_s = int(fields.get("total_elapsed_time"))
        if fields.get("total_timer_time") is not None and session_timer_s is None:
            session_timer_s = int(fields.get("total_timer_time"))

    for record in ff.get_messages("record"):
        fields = {f.name: f.value for f in record}
        ts = fields.get("timestamp")
        lat = _semicircles_to_degrees(fields.get("position_lat"))
        lon = _semicircles_to_degrees(fields.get("position_long"))
        if ts and start_ts is None:
            start_ts = ts
        if ts:
            end_ts = ts
        if lat is not None and lon is not None:
            if prev is not None:
                total_m += _haversine(prev[0], prev[1], lat, lon)
            prev = (lat, lon)

    # Choose distance/duration: prefer session totals; fallback to GPS-derived
    duration_seconds = (
        session_timer_s if session_timer_s is not None else
        (session_elapsed_s if session_elapsed_s is not None else
        (int((end_ts - start_ts).total_seconds()) if start_ts and end_ts else 0)
    ))
    distance_miles = (
        (session_distance_m / 1609.34) if session_distance_m is not None else
        (total_m / 1609.34)
    )
    # convert to local time
    if start_ts:
        local_start = to_local_datetime(start_ts, settings.timezone)
        start_hhmm = local_start.strftime("%H:%M")
        first_date = local_start.date()
    else:
        start_hhmm = None
        first_date = None
    return first_date, start_hhmm, duration_seconds, round(distance_miles, 2)


def _process_fit_file(db: Session, run_id: int, path: str):
    """Parse a FIT file and persist derived data.

    - Prefer device "lap" messages for mile splits (timer time, excludes pauses)
    - Fall back to moving‑time per‑mile splits when no laps are available
    - Store HR/pace downsampled series and HR zones summary
    """
    ff = FitFile(path)
    points = []
    total_m = 0.0
    elev_gain = 0.0
    elev_loss = 0.0
    prev = None
    prev_ele = None
    start_ts = None
    hr_points: list[dict] = []
    pace_points: list[dict] = []
    last_sampled_t = -999.0

    for record in ff.get_messages("record"):
        fields = {f.name: f.value for f in record}
        lat = _semicircles_to_degrees(fields.get("position_lat"))
        lon = _semicircles_to_degrees(fields.get("position_long"))
        ts = fields.get("timestamp")
        # Prefer enhanced fields when present
        ele = fields.get("enhanced_altitude")
        if ele is None:
            ele = fields.get("altitude")
        hr = fields.get("heart_rate")
        speed = fields.get("enhanced_speed")  # m/s
        if speed is None:
            speed = fields.get("speed")
        if ts and start_ts is None:
            start_ts = ts
        t = (ts - start_ts).total_seconds() if (ts and start_ts) else None
        if lat is not None and lon is not None:
            points.append({
                "lat": lat,
                "lon": lon,
                "ele": float(ele) if ele is not None else None,
                "time": ts.isoformat() if ts else None,
                "t": int(t) if t is not None else None,
            })
            if prev is not None:
                total_m += _haversine(prev[0], prev[1], lat, lon)
                if ele is not None and prev_ele is not None:
                    de = float(ele) - float(prev_ele)
                    if de > 0:
                        elev_gain += de
                    else:
                        elev_loss += -de
            prev = (lat, lon)
            prev_ele = float(ele) if ele is not None else None

        # downsample to ~1Hz
        if t is not None and (t - last_sampled_t) >= 1.0:
            if hr is not None:
                hr_points.append({"t": int(t), "hr": int(hr)})
            if speed is not None and speed > 0:
                pace_s_per_mi = float(1609.34 / float(speed))
                pace_points.append({"t": int(t), "pace_s_per_mi": int(pace_s_per_mi)})
            last_sampled_t = t

    # Build geojson/bounds
    if points:
        lats = [p["lat"] for p in points]
        lons = [p["lon"] for p in points]
        bounds = {
            "minLat": min(lats),
            "minLon": min(lons),
            "maxLat": max(lats),
            "maxLon": max(lons),
        }
        coords = [[p["lon"], p["lat"]] for p in points]
        geojson = {"type": "LineString", "coordinates": coords}
    else:
        bounds = None
        geojson = None

    track = db.query(RunTrack).filter(RunTrack.run_id == run_id).first()
    if not track:
        track = RunTrack(run_id=run_id)
        db.add(track)
    track.geojson = geojson
    track.bounds = bounds
    track.points_count = len(points)

    # Splits (prefer device laps if present; fallback to approximation)
    splits = []
    target_m = 1609.34
    acc_m = 0.0
    seg_elapsed = 0.0  # moving time in current split
    MOVING_SPEED_MPS = 0.5

    from datetime import datetime
    def parse_iso(ts):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
        except Exception:
            return None

    for i in range(1, len(points)):
        a, b = points[i-1], points[i]
        d = _haversine(a["lat"], a["lon"], b["lat"], b["lon"]) if a and b else 0.0
        ta, tb = parse_iso(a["time"]), parse_iso(b["time"])
        dt = (tb - ta).total_seconds() if ta and tb else 0.0
        # moving dt from FIT 'speed' if present
        # We don't have per-point speed here; we downsampled earlier but for splits we approximate:
        speed = 0.0
        if dt > 0 and d > 0:
            speed = d / dt
        moving_dt = dt if speed >= MOVING_SPEED_MPS else 0.0

        acc_before = acc_m
        acc_m += d
        rem_d = d
        rem_moving_dt = moving_dt
        while acc_before + rem_d >= target_m:
            needed = target_m - acc_before
            frac = (needed / rem_d) if rem_d > 0 else 0.0
            seg_elapsed += rem_moving_dt * frac
            splits.append({"idx": len(splits)+1, "distance_mi": 1.0, "duration_sec": int(seg_elapsed) if seg_elapsed > 0 else 0})
            rem_d -= needed
            rem_moving_dt = rem_moving_dt * (1 - frac)
            acc_before = 0.0
            acc_m -= target_m
            seg_elapsed = 0.0
        seg_elapsed += rem_moving_dt

    # Prefer FIT lap messages when present (gives timer_time excluding pauses)
    laps = []
    # Also read session totals to compute a final partial split if needed
    session_distance_m = None
    session_timer_s = None
    for session in ff.get_messages("session"):
        fields = {f.name: f.value for f in session}
        if session_distance_m is None and fields.get("total_distance") is not None:
            session_distance_m = float(fields.get("total_distance"))
        if session_timer_s is None and fields.get("total_timer_time") is not None:
            session_timer_s = int(fields.get("total_timer_time"))
    for lap in ff.get_messages("lap"):
        fields = {f.name: f.value for f in lap}
        td = fields.get("total_distance")  # meters
        tt = fields.get("total_timer_time")  # seconds
        if td is None or tt is None:
            continue
        laps.append({
            "distance_mi": float(td) / 1609.34,
            "duration_sec": int(tt),
            "avg_hr": int(fields.get("avg_heart_rate")) if fields.get("avg_heart_rate") is not None else None,
            "max_hr": int(fields.get("max_heart_rate")) if fields.get("max_heart_rate") is not None else None,
            "elev_gain_ft": (float(fields.get("total_ascent")) * 3.28084) if fields.get("total_ascent") is not None else None,
        })

    # If laps exist and look like 1-mile autolaps, use them for splits
    if laps and sum(1 for l in laps if 0.9 <= l["distance_mi"] <= 1.1) >= 1:
        db.query(RunSplit).filter(RunSplit.run_id == run_id).delete()
        idx = 1
        total_kept_miles = 0.0
        total_kept_sec = 0
        for l in laps:
            # Only keep near-mile laps for the table; other custom laps may be shown later
            if 0.9 <= l["distance_mi"] <= 1.1:
                db.add(RunSplit(
                    run_id=run_id,
                    idx=idx,
                    distance_mi=l["distance_mi"],
                    duration_sec=l["duration_sec"],
                    avg_hr=l["avg_hr"],
                    max_hr=l["max_hr"],
                    elev_gain_ft=l["elev_gain_ft"],
                ))
                idx += 1
                total_kept_miles += float(l["distance_mi"])
                total_kept_sec += int(l["duration_sec"])

        # Add final partial split if session totals indicate remaining distance
        rem_mi = None
        rem_sec = None
        if session_distance_m is not None:
            total_mi = session_distance_m / 1609.34
            rem_mi = max(0.0, float(total_mi) - float(total_kept_miles))
            # Some devices round laps; treat negligible remainders as zero
            if rem_mi is not None and rem_mi < 0.01:
                rem_mi = 0.0
        if session_timer_s is not None:
            rem_sec = max(0, int(session_timer_s) - int(total_kept_sec))

        # Fallback: if no session totals, use leftover from approximate pass
        if (rem_mi is None or rem_mi == 0.0) and acc_m > 0:
            rem_mi = acc_m / 1609.34
            rem_sec = int(seg_elapsed)

        if rem_mi and rem_mi > 0.01 and rem_sec is not None and rem_sec > 0:
            db.add(RunSplit(
                run_id=run_id,
                idx=idx,
                distance_mi=round(rem_mi, 3),
                duration_sec=int(rem_sec),
            ))
    else:
        # Use approximated splits if no laps present
        db.query(RunSplit).filter(RunSplit.run_id == run_id).delete()
        for s in splits:
            db.add(RunSplit(run_id=run_id, idx=s["idx"], distance_mi=s["distance_mi"], duration_sec=s["duration_sec"]))

    # (Note: the split insert now happens above depending on lap availability)

    metrics = db.query(RunMetrics).filter(RunMetrics.run_id == run_id).first()
    if not metrics:
        metrics = RunMetrics(run_id=run_id)
        db.add(metrics)
    metrics.elev_gain_ft = float(elev_gain) * 3.28084 if elev_gain else None
    metrics.elev_loss_ft = float(elev_loss) * 3.28084 if elev_loss else None
    # Prefer timer time from session (excludes pauses); fallback to splits or elapsed
    session_timer_s = None
    if not splits:
        for session in ff.get_messages("session"):
            fields = {f.name: f.value for f in session}
            if fields.get("total_timer_time") is not None:
                session_timer_s = int(fields.get("total_timer_time"))
                break
    if session_timer_s is not None:
        metrics.moving_time_sec = session_timer_s
    elif splits:
        metrics.moving_time_sec = int(sum(s["duration_sec"] for s in splits))
    else:
        # last resort
        session_elapsed_s = None
        for session in ff.get_messages("session"):
            fields = {f.name: f.value for f in session}
            if fields.get("total_elapsed_time") is not None:
                session_elapsed_s = int(fields.get("total_elapsed_time"))
                break
        metrics.moving_time_sec = session_elapsed_s

    # HR summary + zones using estimated HR max
    hr_max = settings.hr_max or (220 - settings.age)
    zone_bounds = [0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
    zones = [0, 0, 0, 0, 0]
    for i in range(1, len(hr_points)):
        prev_p, p = hr_points[i-1], hr_points[i]
        dt = max(1, p["t"] - prev_p["t"])  # seconds
        hr_val = prev_p["hr"]
        frac = (hr_val / hr_max) if hr_max else 0
        for z in range(5):
            if zone_bounds[z] <= frac < zone_bounds[z+1]:
                zones[z] += dt
                break
    if hr_points:
        metrics.avg_hr = int(sum(pt["hr"] for pt in hr_points) / len(hr_points))
        metrics.max_hr = int(max(pt["hr"] for pt in hr_points))
    metrics.hr_zones = {"z1": zones[0], "z2": zones[1], "z3": zones[2], "z4": zones[3], "z5": zones[4], "hr_max": hr_max}

    # store time-indexed downsampled series (cap ~600 points)
    def _thin(arr, step):
        return arr[::step] if step > 1 else arr
    step = max(1, int(len(hr_points) / 600))
    metrics.hr_series = _thin(hr_points, step)
    step_p = max(1, int(len(pace_points) / 600))
    metrics.pace_series = _thin(pace_points, step_p)
    # Build distance-indexed series sampled ~every 0.1 mile using point timestamps
    hr_dist_series: list[dict] = []
    pace_dist_series: list[dict] = []
    elev_dist_series: list[dict] = []

    def interp(series, t_val):
        if not series or t_val is None:
            return None
        # series is sorted by 't'
        lo = 0
        hi = len(series) - 1
        if t_val <= series[0]["t"]:
            return series[0]
        if t_val >= series[-1]["t"]:
            return series[-1]
        # binary search
        while lo <= hi:
            mid = (lo + hi) // 2
            mt = series[mid]["t"]
            if mt == t_val:
                return series[mid]
            if mt < t_val:
                lo = mid + 1
            else:
                hi = mid - 1
        # lo is first greater than t_val, hi is last less than t_val
        a = series[hi]
        b = series[lo]
        ta, tb = a["t"], b["t"]
        frac = (t_val - ta) / (tb - ta) if (tb - ta) else 0.0
        out = {"t": t_val}
        for k, v in a.items():
            if k == "t":
                continue
            vb = b.get(k)
            if isinstance(v, (int, float)) and isinstance(vb, (int, float)):
                out[k] = v + (vb - v) * frac
        return out

    # walk distance and sample
    if len(points) >= 2:
        sample_step_m = 160.934  # ~0.1 mi
        next_sample_m = sample_step_m
        acc_m = 0.0
        for i in range(1, len(points)):
            a, b = points[i-1], points[i]
            d = _haversine(a["lat"], a["lon"], b["lat"], b["lon"]) if a and b else 0.0
            acc_before = acc_m
            acc_m += d
            while acc_m >= next_sample_m:
                # fraction along this segment
                needed = next_sample_m - acc_before
                frac = (needed / d) if d > 0 else 0.0
                # distance in miles
                d_mi = (next_sample_m) / 1609.34
                # time at sample
                ta = a.get("t")
                tb = b.get("t")
                t_samp = None
                if ta is not None and tb is not None:
                    t_samp = ta + (tb - ta) * frac
                # interpolate hr/pace by time series
                hri = interp(hr_points, t_samp)
                pci = interp(pace_points, t_samp)
                if hri and ("hr" in hri):
                    hr_dist_series.append({"d": round(d_mi, 3), "hr": int(round(hri["hr"]))})
                if pci and ("pace_s_per_mi" in pci):
                    pace_dist_series.append({"d": round(d_mi, 3), "pace_s_per_mi": int(round(pci["pace_s_per_mi"]))})
                # elevation from point interpolation
                ele_a = a.get("ele")
                ele_b = b.get("ele")
                if ele_a is not None and ele_b is not None:
                    ele = ele_a + (ele_b - ele_a) * frac
                    elev_dist_series.append({"d": round(d_mi, 3), "elev_ft": int(round(ele * 3.28084))})
                next_sample_m += sample_step_m

    metrics.hr_dist_series = hr_dist_series
    metrics.pace_dist_series = pace_dist_series
    metrics.elev_dist_series = elev_dist_series
    db.commit()


@router.post("/{run_id}/files")
def upload_run_file(
    run_id: int,
    file: UploadFile = File(...),
    background: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    filename = file.filename or "upload.gpx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".gpx"]:
        raise HTTPException(status_code=400, detail="Only .gpx files are supported currently")

    # Save to uploads/runs/{id}/
    dir_path = os.path.join(settings.uploads_dir, "runs", str(run_id))
    os.makedirs(dir_path, exist_ok=True)
    save_path = os.path.join(dir_path, filename)

    data = file.file.read()
    with open(save_path, "wb") as out:
        out.write(data)

    rf = RunFile(
        run_id=run_id,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        storage_path=save_path,
        source="gpx",
        processed=False,
    )
    db.add(rf)
    db.commit()
    db.refresh(rf)

    # Background processing
    if background is not None:
        background.add_task(_process_gpx_file, db, run_id, save_path)
        rf.processed = True  # mark optimistic; processor commits the outputs
        db.commit()
    else:
        _process_gpx_file(db, run_id, save_path)
        rf.processed = True
        db.commit()

    return {"message": "File uploaded", "file_id": rf.id}


@router.get("/{run_id}/metrics")
def get_run_metrics(run_id: int, db: Session = Depends(get_db)):
    m = db.query(RunMetrics).filter(RunMetrics.run_id == run_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="No metrics")
    return {
        "avg_hr": m.avg_hr,
        "max_hr": m.max_hr,
        "elev_gain_ft": float(m.elev_gain_ft) if m.elev_gain_ft is not None else None,
        "elev_loss_ft": float(m.elev_loss_ft) if m.elev_loss_ft is not None else None,
        "moving_time_sec": m.moving_time_sec,
        "device": m.device,
        "hr_zones": m.hr_zones,
    }


@router.get("/{run_id}/series")
def get_run_series(run_id: int, db: Session = Depends(get_db)):
    m = db.query(RunMetrics).filter(RunMetrics.run_id == run_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="No series")
    return {
        "hr_series": m.hr_series or [],
        "pace_series": m.pace_series or [],
        "hr_dist_series": m.hr_dist_series or [],
        "pace_dist_series": m.pace_dist_series or [],
        "elev_dist_series": m.elev_dist_series or [],
    }


@router.get("/{run_id}/splits")
def get_run_splits(run_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(RunSplit)
        .filter(RunSplit.run_id == run_id)
        .order_by(RunSplit.idx)
        .all()
    )
    return [
        {
            "idx": r.idx,
            "distance_mi": float(r.distance_mi),
            "duration_sec": r.duration_sec,
            "avg_hr": r.avg_hr,
            "max_hr": r.max_hr,
            "elev_gain_ft": float(r.elev_gain_ft) if r.elev_gain_ft is not None else None,
        }
        for r in rows
    ]


@router.get("/{run_id}/track")
def get_run_track(run_id: int, db: Session = Depends(get_db)):
    t = db.query(RunTrack).filter(RunTrack.run_id == run_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="No track")
    return {
        "geojson": t.geojson,
        "bounds": t.bounds,
        "points_count": t.points_count,
    }


@router.post("/{run_id}/reprocess")
def reprocess_run(
    run_id: int,
    background: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """Rebuild splits/metrics/series/track for a run from its stored file.

    Preference order: FIT > GPX. If no file found, return 404.
    """
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    files = (
        db.query(RunFile)
        .filter(RunFile.run_id == run_id)
        .order_by(RunFile.created_at.asc())
        .all()
    )
    if not files:
        raise HTTPException(status_code=404, detail="No stored files for run")

    chosen = None
    # Prefer FIT when available
    for f in files:
        if (f.source or "").lower() == "fit":
            chosen = f
            break
    if chosen is None:
        # Fall back to first GPX or any
        for f in files:
            if (f.source or "").lower() == "gpx":
                chosen = f
                break
        if chosen is None:
            chosen = files[0]

    # Clear existing derived rows so we don't duplicate
    db.query(RunSplit).filter(RunSplit.run_id == run_id).delete()
    db.query(RunTrack).filter(RunTrack.run_id == run_id).delete()
    db.query(RunMetrics).filter(RunMetrics.run_id == run_id).delete()
    db.commit()

    path = chosen.storage_path
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Stored file missing on disk")

    src = (chosen.source or "").lower()
    if background is not None:
        if src == "gpx" or path.lower().endswith(".gpx"):
            background.add_task(_process_gpx_file, db, run_id, path)
        else:
            background.add_task(_process_fit_file, db, run_id, path)
        # Mark processed optimistically; processors will commit outputs
        chosen.processed = True
        db.commit()
    else:
        if src == "gpx" or path.lower().endswith(".gpx"):
            _process_gpx_file(db, run_id, path)
        else:
            _process_fit_file(db, run_id, path)
        chosen.processed = True
        db.commit()

    return {
        "message": "Reprocess started" if background is not None else "Reprocessed",
        "run_id": run_id,
        "file": chosen.filename,
        "source": chosen.source,
    }

@router.post("/import", response_model=RunRead)
def import_activity(
    file: UploadFile = File(...),
    background: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    filename = file.filename or "import"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".gpx", ".fit"]:
        raise HTTPException(status_code=400, detail="Only .gpx or .fit files are supported")

    # Save to temp location
    dir_path = os.path.join(settings.uploads_dir, "imports")
    os.makedirs(dir_path, exist_ok=True)
    save_path = os.path.join(dir_path, filename)
    data = file.file.read()
    with open(save_path, "wb") as out:
        out.write(data)

    # Basic stats to create the run
    try:
        if ext == ".gpx":
            first_date, start_hhmm, duration_seconds, distance_miles = _gpx_basic_stats(save_path)
        else:
            first_date, start_hhmm, duration_seconds, distance_miles = _fit_basic_stats(save_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file: {e}")

    if not first_date:
        first_date = date.today()

    run = Run(
        date=first_date,
        title=os.path.splitext(filename)[0] or "GPX import",
        notes=None,
        distance_mi=round(distance_miles, 2),
        duration_seconds=duration_seconds if duration_seconds > 0 else 0,
        run_type="easy",
        start_time=hhmm_to_time(start_hhmm) if start_hhmm else None,
        source="fit" if ext == ".fit" else "gpx",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Move file under the run-specific folder and record it, then process
    run_dir = os.path.join(settings.uploads_dir, "runs", str(run.id))
    os.makedirs(run_dir, exist_ok=True)
    final_path = os.path.join(run_dir, filename)
    try:
        if save_path != final_path:
            os.replace(save_path, final_path)
    except Exception:
        final_path = save_path

    rf = RunFile(
        run_id=run.id,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        storage_path=final_path,
        source="fit" if ext == ".fit" else "gpx",
        processed=False,
    )
    db.add(rf)
    db.commit()
    db.refresh(rf)

    if background is not None:
        if ext == ".gpx":
            background.add_task(_process_gpx_file, db, run.id, final_path)
        else:
            background.add_task(_process_fit_file, db, run.id, final_path)
        rf.processed = True
        db.commit()
    else:
        if ext == ".gpx":
            _process_gpx_file(db, run.id, final_path)
        else:
            _process_fit_file(db, run.id, final_path)
        rf.processed = True
        db.commit()

    # Build response
    pace = compute_pace(run.duration_seconds, float(run.distance_mi))
    duration_hhmmss = seconds_to_hhmmss(run.duration_seconds)
    return RunRead(
        id=run.id,
        date=run.date,
        start_time=time_to_hhmm(run.start_time),
        title=run.title,
        notes=run.notes,
        distance_mi=float(run.distance_mi),
        duration=duration_hhmmss,
        run_type=run.run_type,
        source=run.source if hasattr(run, 'source') else None,
        pace=pace,
    )


@router.delete("/{run_id}")
def delete_run(run_id: int, db: Session = Depends(get_db)):
    db_run = db.query(Run).filter(Run.id == run_id).first()
    if not db_run:
        raise HTTPException(status_code=404, detail="Run not found")

    db.delete(db_run)
    db.commit()
    return {"message": "Run deleted"}

@router.get("/weekly_mileage", response_model=list[WeeklyMileagePoint])
def get_weekly_mileage(
    weeks: int = 12,
    db: Session = Depends(get_db),
):
    """
    Return weekly mileage totals for the last `weeks` weeks (including the current week).

    - Weeks are Monday–Sunday.
    - Even if there are no runs in a given week, it appears with 0.0 mileage.
    """
    today = date.today()

    # Monday of the current week
    start_of_this_week = today - timedelta(days=today.weekday())

    # Oldest Monday we care about
    start_date = start_of_this_week - timedelta(weeks=weeks - 1)

    # Aggregate distance per week using Postgres date_trunc('week', ...)
    week_start_col = func.date_trunc("week", Run.date).cast(Date).label("week_start")
    total_distance_col = func.sum(Run.distance_mi).label("total_mileage")

    rows = (
        db.query(week_start_col, total_distance_col)
        .filter(Run.date >= start_date)
        .group_by(week_start_col)
        .order_by(week_start_col)
        .all()
    )

    # Map from week_start (date) -> total mileage
    mileage_by_week: dict[date, float] = {}
    for week_start, total in rows:
        mileage_by_week[week_start] = float(total or 0.0)

    # Build continuous list of weeks from oldest -> newest
    results: list[WeeklyMileagePoint] = []
    for i in range(weeks):
        week_start = start_date + timedelta(weeks=i)
        total = mileage_by_week.get(week_start, 0.0)

        results.append(
            WeeklyMileagePoint(
                week_start=week_start,
                total_mileage=total,
            )
        )

    return results
