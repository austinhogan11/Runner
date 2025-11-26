from datetime import date
from typing import Optional
from enum import Enum

from pydantic import BaseModel
try:  # Pydantic v2
    from pydantic import ConfigDict
except Exception:  # fallback for v1, not used but keeps import safe
    ConfigDict = dict  # type: ignore


class RunType(str, Enum):
    easy = "easy"
    workout = "workout"
    long = "long"
    race = "race"


class RunBase(BaseModel):
    date: date
    start_time: Optional[str] = None  # 'HH:MM'
    title: str
    notes: Optional[str] = None

    distance_mi: float  # what the user types, e.g. 7.35
    duration: str       # "HH:MM:SS" as seen in the UI, e.g. "00:45:32"

    # New field: run type categorization
    run_type: RunType = RunType.easy


class RunCreate(RunBase):
    """Schema for creating a new run."""
    pass


class RunUpdate(BaseModel):
    """Schema for updating an existing run (all fields optional)."""

    # Accept date as string for updates to avoid strict parsing issues
    date: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    distance_mi: Optional[float] = None
    duration: Optional[str] = None  # still "HH:MM:SS"
    run_type: Optional[RunType] = None
    # Tolerate common extras a client might include
    id: Optional[int] = None
    pace: Optional[str] = None
    start_time: Optional[str] = None  # 'HH:MM'

    # Be lenient with extra fields from clients
    try:
        model_config = ConfigDict(extra="ignore")  # type: ignore
    except Exception:
        pass


class RunRead(RunBase):
    """Schema returned to the frontend when reading a run."""

    id: int
    pace: str  # e.g. "6:30/mi"
    source: str | None = None
    try:
        model_config = ConfigDict(from_attributes=True)  # pydantic v2
    except Exception:
        class Config:
            orm_mode = True


class WeeklyMileagePoint(BaseModel):
    week_start: date
    total_mileage: float
