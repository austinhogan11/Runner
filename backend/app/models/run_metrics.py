from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from app.db import Base


class RunMetrics(Base):
    __tablename__ = "run_metrics"

    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)

    avg_hr = Column(Integer, nullable=True)
    max_hr = Column(Integer, nullable=True)
    elev_gain_ft = Column(Numeric(7, 1), nullable=True)
    elev_loss_ft = Column(Numeric(7, 1), nullable=True)
    moving_time_sec = Column(Integer, nullable=True)
    device = Column(String, nullable=True)
    # Aggregated telemetry
    hr_zones = Column(JSONB, nullable=True)
    hr_series = Column(JSONB, nullable=True)   # [{t: seconds, hr: bpm}] (downsampled)
    pace_series = Column(JSONB, nullable=True) # [{t: seconds, pace_s_per_mi: number}]
