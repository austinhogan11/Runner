from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/runner"
    )
    uploads_dir: str = "uploads"  # relative to backend working dir
    # Timezone for displaying/importing activity local times.
    # Examples: "America/New_York", "Europe/London", or "local" to use system tz.
    timezone: str = "local"
    # Heart rate settings
    age: int = 27
    hr_max: int | None = None  # if None, computed as 220 - age

    # Strava OAuth (optional)
    strava_client_id: str | None = None
    strava_client_secret: str | None = None
    strava_redirect_uri: str | None = None
    strava_tokens_path: str = "uploads/strava/tokens.json"

    class Config:
        env_file = ".env"


settings = Settings()
