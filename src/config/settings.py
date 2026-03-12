import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # GitHub
    github_token: str

    # X (Twitter) API
    x_api_key: str
    x_api_secret: str
    x_access_token: str
    x_access_token_secret: str

    # LinkedIn API
    linkedin_client_id: str
    linkedin_client_secret: str
    linkedin_access_token: str

    # Scheduling
    schedule_cron: str = "0 9 * * 1"  # Default: Monday 9 AM
    schedule_interval_hours: Optional[int] = None

    # Data
    data_dir: str = "./data"

    def __post_init__(self):
        """Validate required settings after initialization."""
        required_fields = [
            ("github_token", self.github_token),
            ("x_api_key", self.x_api_key),
            ("x_api_secret", self.x_api_secret),
            ("x_access_token", self.x_access_token),
            ("x_access_token_secret", self.x_access_token_secret),
            ("linkedin_client_id", self.linkedin_client_id),
            ("linkedin_client_secret", self.linkedin_client_secret),
            ("linkedin_access_token", self.linkedin_access_token),
        ]

        missing = [name for name, value in required_fields if not value]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


def load_settings() -> Settings:
    """
    Load application settings from environment.

    Loads .env file if it exists, then reads environment variables.
    Returns a Settings instance with validation.

    Raises:
        ValueError: If required environment variables are missing
    """
    # Load .env file from project root
    load_dotenv()

    return Settings(
        github_token=os.getenv("GITHUB_TOKEN", ""),
        x_api_key=os.getenv("X_API_KEY", ""),
        x_api_secret=os.getenv("X_API_SECRET", ""),
        x_access_token=os.getenv("X_ACCESS_TOKEN", ""),
        x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET", ""),
        linkedin_client_id=os.getenv("LINKEDIN_CLIENT_ID", ""),
        linkedin_client_secret=os.getenv("LINKEDIN_CLIENT_SECRET", ""),
        linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN", ""),
        schedule_cron=os.getenv("SCHEDULE_CRON", "0 9 * * 1"),
        schedule_interval_hours=_parse_int(os.getenv("SCHEDULE_INTERVAL_HOURS")),
        data_dir=os.getenv("DATA_DIR", "./data"),
    )


def _parse_int(value: Optional[str]) -> Optional[int]:
    """Parse string to int, returning None if invalid."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
