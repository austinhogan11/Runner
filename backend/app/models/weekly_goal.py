from sqlalchemy import Column, Date, Numeric, String
from app.db import Base


class WeeklyGoal(Base):
    __tablename__ = "weekly_goals"

    # Monday of the week (local), unique per week
    week_start = Column(Date, primary_key=True, index=True, nullable=False)

    goal_miles = Column(Numeric(5, 2), nullable=False)
    notes = Column(String, nullable=True)

