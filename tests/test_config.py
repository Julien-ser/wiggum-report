import os
import pytest
from src.config import Settings, load_settings
from src.config.settings import _parse_int


class TestParseInt:
    """Test the _parse_int helper function."""

    def test_parse_valid_int(self):
        assert _parse_int("123") == 123

    def test_parse_none(self):
        assert _parse_int(None) is None

    def test_parse_empty_string(self):
        assert _parse_int("") is None

    def test_parse_invalid_int(self):
        assert _parse_int("abc") is None

    def test_parse_zero(self):
        assert _parse_int("0") == 0


class TestSettings:
    """Test the Settings dataclass."""

    def test_settings_with_all_values(self):
        """Test Settings creation with all required fields."""
        settings = Settings(
            github_token="gh_token",
            x_api_key="x_key",
            x_api_secret="x_secret",
            x_access_token="x_access",
            x_access_token_secret="x_access_secret",
            linkedin_client_id="li_id",
            linkedin_client_secret="li_secret",
            linkedin_access_token="li_token",
        )
        assert settings.github_token == "gh_token"
        assert settings.x_api_key == "x_key"
        assert settings.data_dir == "./data"  # default value
        assert settings.schedule_cron == "0 9 * * 1"  # default value

    def test_settings_missing_required_raises(self):
        """Test that missing required fields raise ValueError."""
        with pytest.raises(ValueError, match="Missing required environment variables"):
            Settings(
                github_token="",  # empty
                x_api_key="x_key",
                x_api_secret="x_secret",
                x_access_token="x_access",
                x_access_token_secret="x_access_secret",
                linkedin_client_id="li_id",
                linkedin_client_secret="li_secret",
                linkedin_access_token="li_token",
            )

    def test_settings_custom_defaults(self):
        """Test Settings with custom optional values."""
        settings = Settings(
            github_token="gh_token",
            x_api_key="x_key",
            x_api_secret="x_secret",
            x_access_token="x_access",
            x_access_token_secret="x_access_secret",
            linkedin_client_id="li_id",
            linkedin_client_secret="li_secret",
            linkedin_access_token="li_token",
            schedule_cron="0 10 * * 1",
            schedule_interval_hours=24,
            data_dir="/custom/data",
        )
        assert settings.schedule_cron == "0 10 * * 1"
        assert settings.schedule_interval_hours == 24
        assert settings.data_dir == "/custom/data"


class TestLoadSettings:
    """Test the load_settings function."""

    def test_load_from_env(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_github_token")
        monkeypatch.setenv("X_API_KEY", "test_x_key")
        monkeypatch.setenv("X_API_SECRET", "test_x_secret")
        monkeypatch.setenv("X_ACCESS_TOKEN", "test_x_access")
        monkeypatch.setenv("X_ACCESS_TOKEN_SECRET", "test_x_access_secret")
        monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test_li_id")
        monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test_li_secret")
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test_li_token")
        monkeypatch.setenv("SCHEDULE_CRON", "0 10 * * 1")
        monkeypatch.setenv("SCHEDULE_INTERVAL_HOURS", "24")
        monkeypatch.setenv("DATA_DIR", "/test/data")

        settings = load_settings()

        assert settings.github_token == "test_github_token"
        assert settings.x_api_key == "test_x_key"
        assert settings.schedule_cron == "0 10 * * 1"
        assert settings.schedule_interval_hours == 24
        assert settings.data_dir == "/test/data"

    def test_load_with_defaults(self, monkeypatch):
        """Test loading settings with only required variables, using defaults."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_github_token")
        monkeypatch.setenv("X_API_KEY", "test_x_key")
        monkeypatch.setenv("X_API_SECRET", "test_x_secret")
        monkeypatch.setenv("X_ACCESS_TOKEN", "test_x_access")
        monkeypatch.setenv("X_ACCESS_TOKEN_SECRET", "test_x_access_secret")
        monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test_li_id")
        monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test_li_secret")
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test_li_token")

        settings = load_settings()

        assert settings.schedule_cron == "0 9 * * 1"
        assert settings.schedule_interval_hours is None
        assert settings.data_dir == "./data"

    def test_missing_required_raises(self, monkeypatch):
        """Test that missing required environment variables raise ValueError."""
        # Set only one required var
        monkeypatch.setenv("GITHUB_TOKEN", "test_github_token")

        with pytest.raises(ValueError, match="Missing required environment variables"):
            load_settings()

    def test_invalid_interval_hours(self, monkeypatch):
        """Test that invalid SCHEDULE_INTERVAL_HOURS is treated as None."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_github_token")
        monkeypatch.setenv("X_API_KEY", "test_x_key")
        monkeypatch.setenv("X_API_SECRET", "test_x_secret")
        monkeypatch.setenv("X_ACCESS_TOKEN", "test_x_access")
        monkeypatch.setenv("X_ACCESS_TOKEN_SECRET", "test_x_access_secret")
        monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test_li_id")
        monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test_li_secret")
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test_li_token")
        monkeypatch.setenv("SCHEDULE_INTERVAL_HOURS", "invalid")

        settings = load_settings()
        assert settings.schedule_interval_hours is None
