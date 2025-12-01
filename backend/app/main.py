from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.runs import router as runs_router
from app.api.goals import router as goals_router
from app.api.strava import router as strava_router
from app.db import Base, engine
from app.models.run import Run  # noqa: F401  (import ensures table is registered)
from app.models.weekly_goal import WeeklyGoal  # noqa: F401
from app.core.config import settings
import os


app = FastAPI()

# Allow CORS for local frontend
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables (runs, etc.) on startup
Base.metadata.create_all(bind=engine)

# Ensure uploads directory exists
os.makedirs(settings.uploads_dir, exist_ok=True)

app.include_router(runs_router)
app.include_router(goals_router)
app.include_router(strava_router)


@app.get("/")
def root():
    return {"message": "Runner backend is running"}
