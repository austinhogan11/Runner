from datetime import date
from typing import Optional
from pydantic import BaseModel
try:
    from pydantic import ConfigDict  # pydantic v2
except Exception:  # v1 fallback
    ConfigDict = None  # type: ignore


class WeeklyGoalBase(BaseModel):
    week_start: date
    goal_miles: float
    notes: Optional[str] = None


class WeeklyGoalRead(WeeklyGoalBase):
    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)  # type: ignore
    else:
        class Config:
            orm_mode = True


class WeeklyGoalUpsert(BaseModel):
    goal_miles: float
    notes: Optional[str] = None
