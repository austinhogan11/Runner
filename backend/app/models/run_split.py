from sqlalchemy import Column, Integer, ForeignKey, Numeric
from app.db import Base


class RunSplit(Base):
    __tablename__ = "run_splits"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)

    idx = Column(Integer, nullable=False)  # 1-based split index
    distance_mi = Column(Numeric(6, 3), nullable=False)
    duration_sec = Column(Integer, nullable=False)
    avg_hr = Column(Integer, nullable=True)
    max_hr = Column(Integer, nullable=True)
    elev_gain_ft = Column(Numeric(7, 1), nullable=True)

