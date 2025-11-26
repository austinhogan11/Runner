from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.weekly_goal import WeeklyGoal
from app.schemas.goal import WeeklyGoalRead, WeeklyGoalUpsert


router = APIRouter(prefix="/goals", tags=["goals"])


def monday_of(d: date) -> date:
    # Monday = 0, Sunday = 6
    return d - timedelta(days=d.weekday())


@router.get("/weekly", response_model=list[WeeklyGoalRead])
def list_weekly_goals(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    # normalize to Mondays covering the range
    start = monday_of(start_date)
    end = monday_of(end_date)
    rows = (
        db.query(WeeklyGoal)
        .filter(WeeklyGoal.week_start >= start)
        .filter(WeeklyGoal.week_start <= end)
        .order_by(WeeklyGoal.week_start)
        .all()
    )
    return rows


@router.get("/{week_start}", response_model=WeeklyGoalRead)
def get_week_goal(week_start: date, db: Session = Depends(get_db)):
    wk = monday_of(week_start)
    row = db.query(WeeklyGoal).filter(WeeklyGoal.week_start == wk).first()
    if not row:
        raise HTTPException(status_code=404, detail="Goal not set")
    return row


@router.put("/{week_start}", response_model=WeeklyGoalRead)
def upsert_week_goal(
    week_start: date,
    payload: WeeklyGoalUpsert,
    db: Session = Depends(get_db),
):
    wk = monday_of(week_start)
    if payload.goal_miles <= 0:
        raise HTTPException(status_code=422, detail="goal_miles must be > 0")

    row = db.query(WeeklyGoal).filter(WeeklyGoal.week_start == wk).first()
    if not row:
        row = WeeklyGoal(week_start=wk, goal_miles=payload.goal_miles, notes=payload.notes)
        db.add(row)
    else:
        row.goal_miles = payload.goal_miles
        row.notes = payload.notes
    db.commit()
    db.refresh(row)
    return row

