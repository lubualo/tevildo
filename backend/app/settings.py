"""
Application settings and configuration.

Loads configuration from environment variables or .env file.
Uses pydantic-settings for type validation and defaults.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application paths
    # Note: Default is Docker container path (/app/data)
    # For local development without Docker, override via .env:
    #   TEVILDO_DATA_DIR=/path/to/tevildo/backend/data
    tevildo_data_dir: Path = Path("/app/data")

    # Database configuration
    # SQLite URL is derived from data_dir
    @property
    def database_url(self) -> str:
        """SQLite database URL."""
        return f"sqlite:///{self.tevildo_data_dir / 'app.db'}"

    @property
    def invoices_dir(self) -> Path:
        """Directory for storing invoice PDFs."""
        return self.tevildo_data_dir / "invoices"

    # Application settings
    app_name: str = "Tevildo"
    debug: bool = False

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )


# Single global instance
settings = Settings()
