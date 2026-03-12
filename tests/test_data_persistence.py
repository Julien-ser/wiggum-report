"""Tests for data_persistence module."""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.data_persistence import DataPersistence


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def persistence(temp_db):
    """Create DataPersistence instance with temporary database."""
    return DataPersistence(db_path=temp_db)


def test_init_creates_database_and_tables(temp_db):
    """Test that initialization creates database and required tables."""
    # Create DataPersistence instance to trigger initialization
    persistence = DataPersistence(db_path=temp_db)
    db_path = Path(temp_db)
    assert db_path.exists()

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "reported_repos" in tables
        assert "weekly_reports" in tables
        assert "repo_week_association" in tables


def test_mark_repo_reported_inserts_new_repo(persistence):
    """Test marking a repository as reported creates a new record."""
    full_name = "testuser/testrepo"
    reported_at = datetime.now()
    created_at = "2024-01-01T00:00:00"
    updated_at = "2024-01-15T00:00:00"

    persistence.mark_repo_reported(full_name, reported_at, created_at, updated_at)

    with sqlite3.connect(persistence.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_name, last_reported_date, times_reported, created_at, updated_at FROM reported_repos WHERE full_name = ?",
            (full_name,),
        )
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == full_name
    assert row[2] == 1  # times_reported
    assert row[3] == created_at
    assert row[4] == updated_at


def test_mark_repo_reported_updates_existing_repo(persistence):
    """Test marking an already reported repo increments times_reported."""
    full_name = "testuser/testrepo"
    reported_at1 = datetime.now() - timedelta(days=7)
    reported_at2 = datetime.now()

    persistence.mark_repo_reported(full_name, reported_at1)
    persistence.mark_repo_reported(full_name, reported_at2)

    with sqlite3.connect(persistence.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT times_reported, last_reported_date FROM reported_repos WHERE full_name = ?",
            (full_name,),
        )
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == 2  # times_reported should be incremented
    # last_reported_date should be updated to latest
    assert row[1] == reported_at2.isoformat()


def test_is_repo_reported_returns_false_when_not_reported(persistence):
    """Test is_repo_reported returns False for unreported repo."""
    full_name = "testuser/newrepo"
    since = datetime.now() - timedelta(days=7)

    assert not persistence.is_repo_reported(full_name, since)


def test_is_repo_reported_returns_true_when_reported_since(persistence):
    """Test is_repo_reported returns True when repo was reported after since date."""
    full_name = "testuser/testrepo"
    reported_at = datetime.now() - timedelta(days=3)
    since = datetime.now() - timedelta(days=7)

    persistence.mark_repo_reported(full_name, reported_at)
    assert persistence.is_repo_reported(full_name, since)


def test_is_repo_reported_returns_false_when_reported_before_since(persistence):
    """Test is_repo_reported returns False when repo was reported before since date."""
    full_name = "testuser/oldrepo"
    reported_at = datetime.now() - timedelta(days=10)
    since = datetime.now() - timedelta(days=7)

    persistence.mark_repo_reported(full_name, reported_at)
    assert not persistence.is_repo_reported(full_name, since)


def test_get_reported_repos_since_returns_set_of_repos(persistence):
    """Test getting set of repos reported since a date."""
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    persistence.mark_repo_reported("user/repo1", now)
    persistence.mark_repo_reported("user/repo2", week_ago)
    persistence.mark_repo_reported("user/repo3", two_weeks_ago)

    reported_since = persistence.get_reported_repos_since(week_ago)
    assert "user/repo1" in reported_since
    assert "user/repo2" in reported_since
    assert "user/repo3" not in reported_since


def test_save_weekly_report_creates_record(persistence):
    """Test saving a weekly report creates a database record."""
    now = datetime.now()
    week_start = now - timedelta(days=7)

    summary = {
        "total_repos_processed": 5,
        "new_repositories_count": 2,
        "updated_repositories_count": 3,
        "total_stars": 100,
        "total_forks": 25,
        "languages": {"Python": 3, "JavaScript": 2},
        "recent_commits_count": 15,
        "releases_count": 2,
    }

    new_repos = [
        {"full_name": "user/new1", "stars": 10},
        {"full_name": "user/new2", "stars": 20},
    ]
    updated_repos = [
        {"full_name": "user/updated1", "stars": 30},
        {"full_name": "user/updated2", "stars": 40},
    ]

    report_id = persistence.save_weekly_report(
        week_start=week_start,
        collection_date=now,
        summary=summary,
        new_repos=new_repos,
        updated_repos=updated_repos,
    )

    assert report_id > 0

    # Verify report was saved
    report = persistence.get_weekly_report(week_start)
    assert report is not None
    assert report["week_start_date"] == week_start.isoformat()
    assert report["collection_date"] == now.isoformat()
    assert report["summary_data"] == summary
    assert report["new_repos_count"] == 2
    assert report["updated_repos_count"] == 2
    assert report["total_repos_processed"] == 5


def test_save_weekly_report_also_marks_repos_as_reported(persistence):
    """Test that saving a weekly report also updates reported_repos table."""
    now = datetime.now()
    week_start = now - timedelta(days=7)

    summary = {
        "total_repos_processed": 2,
        "new_repositories_count": 1,
        "updated_repositories_count": 1,
    }

    new_repos = [
        {
            "full_name": "user/newrepo",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
    ]
    updated_repos = [
        {
            "full_name": "user/updatedrepo",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
    ]

    persistence.save_weekly_report(
        week_start=week_start,
        collection_date=now,
        summary=summary,
        new_repos=new_repos,
        updated_repos=updated_repos,
    )

    # Check repos are in reported_repos
    assert persistence.get_repo_report_count("user/newrepo") == 1
    assert persistence.get_repo_report_count("user/updatedrepo") == 1


def test_get_weekly_report_returns_none_if_not_found(persistence):
    """Test get_weekly_report returns None for non-existent week."""
    week_start = datetime.now() - timedelta(days=7)
    assert persistence.get_weekly_report(week_start) is None


def test_get_all_weekly_reports_returns_in_reverse_chronological_order(persistence):
    """Test that get_all_weekly_reports returns reports ordered by week_start DESC."""
    now = datetime.now()
    week1_start = now - timedelta(days=7)
    week2_start = now - timedelta(days=14)

    summary = {"total_repos_processed": 1}

    persistence.save_weekly_report(
        week_start=week1_start,
        collection_date=now,
        summary=summary,
        new_repos=[],
        updated_repos=[],
    )
    persistence.save_weekly_report(
        week_start=week2_start,
        collection_date=now,
        summary=summary,
        new_repos=[],
        updated_repos=[],
    )

    reports = persistence.get_all_weekly_reports()
    assert len(reports) == 2
    assert reports[0]["week_start_date"] == week1_start.isoformat()
    assert reports[1]["week_start_date"] == week2_start.isoformat()


def test_clear_all_data_removes_all_records(persistence):
    """Test clear_all_data deletes all data from database."""
    now = datetime.now()
    week_start = now - timedelta(days=7)

    summary = {"total_repos_processed": 1}

    persistence.mark_repo_reported("user/repo", now)
    persistence.save_weekly_report(
        week_start=week_start,
        collection_date=now,
        summary=summary,
        new_repos=[],
        updated_repos=[],
    )

    persistence.clear_all_data()

    with sqlite3.connect(persistence.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reported_repos")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM weekly_reports")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM repo_week_association")
        assert cursor.fetchone()[0] == 0


def test_from_settings_creates_instance_with_settings_database_path():
    """Test from_settings class method uses settings.database_path."""

    class MockSettings:
        database_path = "custom/path/report.db"

    persistence = DataPersistence.from_settings(MockSettings())
    assert persistence.db_path == Path("custom/path/report.db")
