from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Time
from sqlalchemy.sql import func
from app.db import Base

class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)

    date = Column(Date, nullable=False)

    title = Column(String, nullable=False)
    notes = Column(String, nullable=True)

    distance_mi = Column(Numeric(5, 2), nullable=False)  # e.g. 7.35 miles

    # Duration stored as **total seconds** (int)
    # Frontend will convert HH:MM:SS ↔ seconds
    duration_seconds = Column(Integer, nullable=False)

    # Optional start time (local day time only)
    start_time = Column(Time, nullable=True)

    # Run categorization
    run_type = Column(
        String(20),
        nullable=False,
        server_default="easy",   # easy, workout, long, race, other
    )

    # Source of run data
    source = Column(
        String(20),
        nullable=False,
        server_default="manual",  # manual entry, imported, api
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Pace is NOT stored — it’s computed on the fly
    # pace = duration_seconds / distance_mi  (we will compute this in schema)
