from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.db import Base


class RunTrack(Base):
    __tablename__ = "run_track"

    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)
    geojson = Column(JSONB, nullable=True)  # LineString
    bounds = Column(JSONB, nullable=True)   # {minLat, minLon, maxLat, maxLon}
    points_count = Column(Integer, nullable=True)

