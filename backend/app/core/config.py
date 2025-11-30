from pydantic_settings import BaseSettings
from pydantic import field_validator


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

    # Allow empty env strings for optional fields
    @field_validator("hr_max", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        if v in ("", None, "null", "None"):
            return None
        return v

    class Config:
        env_file = ".env"


settings = Settings()
