"""Data persistence layer for storing weekly report history and tracking reported repos."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from src.config.settings import Settings


class DataPersistence:
    """Handles SQLite database operations for wiggum-report."""

    def __init__(self, db_path: str = "data/wiggum_report.db"):
        """
        Initialize data persistence with database path.

        Args:
            db_path: Path to SQLite database file (default: data/wiggum_report.db)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reported_repos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT UNIQUE NOT NULL,
                    last_reported_date TEXT NOT NULL,
                    times_reported INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS weekly_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    week_start_date TEXT UNIQUE NOT NULL,
                    collection_date TEXT NOT NULL,
                    summary_data TEXT NOT NULL,  -- JSON string
                    new_repos_count INTEGER NOT NULL,
                    updated_repos_count INTEGER NOT NULL,
                    total_repos_processed INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS repo_week_association (
                    repo_id INTEGER NOT NULL,
                    report_id INTEGER NOT NULL,
                    repo_type TEXT NOT NULL,  -- 'new' or 'updated'
                    FOREIGN KEY (repo_id) REFERENCES reported_repos(id),
                    FOREIGN KEY (report_id) REFERENCES weekly_reports(id),
                    UNIQUE(repo_id, report_id, repo_type)
                )
            """)

            conn.commit()

    def is_repo_reported(self, full_name: str, since: datetime) -> bool:
        """
        Check if a repository has been reported since the given date.

        Args:
            full_name: Repository full name (owner/repo)
            since: Datetime threshold

        Returns:
            True if repo was reported after 'since' date, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT last_reported_date FROM reported_repos
                WHERE full_name = ? AND datetime(last_reported_date) >= datetime(?)
                """,
                (full_name, since.isoformat()),
            )
            result = cursor.fetchone()
            return result is not None

    def get_reported_repos_since(self, since: datetime) -> Set[str]:
        """
        Get set of repository full names reported since a given date.

        Args:
            since: Datetime threshold

        Returns:
            Set of repository full names
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT full_name FROM reported_repos
                WHERE datetime(last_reported_date) >= datetime(?)
                """,
                (since.isoformat(),),
            )
            results = cursor.fetchall()
            return {row[0] for row in results}

    def mark_repo_reported(
        self,
        full_name: str,
        reported_at: datetime,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        """
        Mark a repository as reported (insert or update record).

        Args:
            full_name: Repository full name
            reported_at: Datetime when repo was reported
            created_at: Repository creation date (ISO format)
            updated_at: Repository last update date (ISO format)
        """
        now = datetime.now().isoformat()
        created_at = created_at or now
        updated_at = updated_at or now

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO reported_repos (full_name, last_reported_date, times_reported, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(full_name) DO UPDATE SET
                    last_reported_date = excluded.last_reported_date,
                    times_reported = reported_repos.times_reported + 1,
                    updated_at = excluded.updated_at
                """,
                (full_name, reported_at.isoformat(), created_at, updated_at),
            )
            conn.commit()

    def save_weekly_report(
        self,
        week_start: datetime,
        collection_date: datetime,
        summary: Dict[str, Any],
        new_repos: List[Dict[str, Any]],
        updated_repos: List[Dict[str, Any]],
    ) -> int:
        """
        Save weekly report and mark repos as reported.

        Args:
            week_start: Start date of the week
            collection_date: When data was collected
            summary: Summary statistics dictionary
            new_repos: List of new repository data
            updated_repos: List of updated repository data

        Returns:
            Report ID (database row ID)
        """
        collection_iso = collection_date.isoformat()
        week_start_iso = week_start.isoformat()
        summary_json = json.dumps(summary, ensure_ascii=False)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert weekly report
            cursor.execute(
                """
                INSERT OR REPLACE INTO weekly_reports
                (week_start_date, collection_date, summary_data, new_repos_count,
                 updated_repos_count, total_repos_processed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    week_start_iso,
                    collection_iso,
                    summary_json,
                    len(new_repos),
                    len(updated_repos),
                    summary.get("total_repos_processed", 0),
                    collection_iso,
                ),
            )
            report_id = cursor.lastrowid

            # Clear any existing associations for this week (in case of REPLACE)
            cursor.execute(
                "DELETE FROM repo_week_association WHERE report_id = ?", (report_id,)
            )

            # Helper to upsert repo record and return its ID
            def upsert_repo(repo: Dict[str, Any]) -> int:
                full_name = repo["full_name"]
                created_at = repo.get("created_at") or collection_iso
                updated_at = repo.get("updated_at") or collection_iso

                cursor.execute(
                    """
                    INSERT INTO reported_repos (full_name, last_reported_date, times_reported, created_at, updated_at)
                    VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(full_name) DO UPDATE SET
                        last_reported_date = excluded.last_reported_date,
                        times_reported = reported_repos.times_reported + 1,
                        updated_at = excluded.updated_at
                    """,
                    (full_name, collection_iso, created_at, updated_at),
                )
                cursor.execute(
                    "SELECT id FROM reported_repos WHERE full_name = ?", (full_name,)
                )
                result = cursor.fetchone()
                return result[0] if result else None

            # Process new repos
            for repo in new_repos:
                repo_id = upsert_repo(repo)
                if repo_id:
                    cursor.execute(
                        """
                        INSERT INTO repo_week_association (repo_id, report_id, repo_type)
                        VALUES (?, ?, 'new')
                        """,
                        (repo_id, report_id),
                    )

            # Process updated repos
            for repo in updated_repos:
                repo_id = upsert_repo(repo)
                if repo_id:
                    cursor.execute(
                        """
                        INSERT INTO repo_week_association (repo_id, report_id, repo_type)
                        VALUES (?, ?, 'updated')
                        """,
                        (repo_id, report_id),
                    )

            conn.commit()
            return report_id

    def get_weekly_report(self, week_start: datetime) -> Optional[Dict[str, Any]]:
        """
        Retrieve a weekly report by its start date.

        Args:
            week_start: Start date of the week

        Returns:
            Dictionary with report data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM weekly_reports
                WHERE week_start_date = ?
                """,
                (week_start.isoformat(),),
            )
            row = cursor.fetchone()

            if not row:
                return None

            report = dict(row)
            report["summary_data"] = json.loads(report["summary_data"])

            # Get associated repos
            cursor.execute(
                """
                SELECT r.full_name, rwa.repo_type
                FROM repo_week_association rwa
                JOIN reported_repos r ON rwa.repo_id = r.id
                WHERE rwa.report_id = ?
                """,
                (report["id"],),
            )
            repos = cursor.fetchall()
            report["new_repositories"] = [
                dict(row) for row in repos if row["repo_type"] == "new"
            ]
            report["updated_repositories"] = [
                dict(row) for row in repos if row["repo_type"] == "updated"
            ]

            return report

    def get_all_weekly_reports(self) -> List[Dict[str, Any]]:
        """
        Get all weekly reports in reverse chronological order.

        Returns:
            List of weekly report dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM weekly_reports
                ORDER BY week_start_date DESC
                """
            )
            rows = cursor.fetchall()

            reports = []
            for row in rows:
                report = dict(row)
                report["summary_data"] = json.loads(report["summary_data"])
                reports.append(report)

            return reports

    def get_repo_report_count(self, full_name: str) -> int:
        """
        Get how many times a repository has been reported.

        Args:
            full_name: Repository full name

        Returns:
            Number of times reported
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT times_reported FROM reported_repos WHERE full_name = ?",
                (full_name,),
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def clear_all_data(self) -> None:
        """Delete all data from database (useful for testing)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM repo_week_association")
            conn.execute("DELETE FROM weekly_reports")
            conn.execute("DELETE FROM reported_repos")
            conn.commit()

    @classmethod
    def from_settings(cls, settings: Settings) -> "DataPersistence":
        """
        Create DataPersistence from Settings object.

        Args:
            settings: Settings instance with database path

        Returns:
            DataPersistence instance
        """
        db_path = getattr(settings, "database_path", "data/wiggum_report.db")
        return cls(db_path=db_path)
