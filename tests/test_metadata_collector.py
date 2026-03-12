"""Unit tests for metadata collector."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, ANY
from src.metadata_collector import MetadataCollector
from src.github_client import GitHubClient


class TestMetadataCollector:
    """Test cases for MetadataCollector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_github_client = MagicMock(spec=GitHubClient)
        self.collector = MetadataCollector(self.mock_github_client)
        self.now = datetime.now()
        self.week_ago = self.now - timedelta(days=7)

    def test_init(self):
        """Test collector initialization."""
        assert self.collector.github_client == self.mock_github_client

    def test_collect_weekly_metadata_basic(self):
        """Test basic weekly metadata collection."""
        # Mock repository data
        mock_new_repo = {
            "full_name": "owner/new-repo",
            "name": "new-repo",
            "description": "A new repository",
            "stars": 10,
            "forks": 2,
        }
        mock_updated_repo = {
            "full_name": "owner/updated-repo",
            "name": "updated-repo",
            "description": "An updated repository",
            "stars": 5,
            "forks": 1,
        }

        self.mock_github_client.get_new_repositories.return_value = [mock_new_repo]
        self.mock_github_client.get_repositories_updated_since.return_value = [
            mock_updated_repo,  # Only the truly updated repo, not the new one
        ]

        def mock_get_repository(full_name):
            if full_name == "owner/new-repo":
                return MagicMock(full_name="owner/new-repo")
            elif full_name == "owner/updated-repo":
                return MagicMock(full_name="owner/updated-repo")
            return None

        def mock_get_detailed_info(repo, **kwargs):
            # Return a dict with at least full_name matching the repo
            return {
                "full_name": repo.full_name,
                "name": repo.full_name.split("/")[1],
                "description": "Mocked",
                "stars": 0,
                "forks": 0,
                "recent_commits": [],
                "releases": [],
                "readme": None,
            }

        self.mock_github_client.get_repository.side_effect = mock_get_repository
        self.mock_github_client.get_repository_detailed_info.side_effect = (
            mock_get_detailed_info
        )

        result = self.collector.collect_weekly_metadata()

        # Verify structure
        assert "collection_date" in result
        assert "week_start" in result
        assert "summary" in result
        assert "new_repositories" in result
        assert "updated_repositories" in result

        # Verify summary
        summary = result["summary"]
        assert summary["new_repositories_count"] == 1
        assert summary["updated_repositories_count"] == 1
        assert summary["total_repos_processed"] == 2

        # Verify no duplication (new repo not in updated)
        new_full_names = {r["full_name"] for r in result["new_repositories"]}
        updated_full_names = {r["full_name"] for r in result["updated_repositories"]}
        assert new_full_names == {"owner/new-repo"}
        assert updated_full_names == {"owner/updated-repo"}
        assert len(new_full_names & updated_full_names) == 0

    def test_collect_weekly_metadata_empty(self):
        """Test collection with no repositories."""
        self.mock_github_client.get_new_repositories.return_value = []
        self.mock_github_client.get_repositories_updated_since.return_value = []

        result = self.collector.collect_weekly_metadata()

        assert result["summary"]["total_repos_processed"] == 0
        assert result["summary"]["new_repositories_count"] == 0
        assert result["summary"]["updated_repositories_count"] == 0
        assert len(result["new_repositories"]) == 0
        assert len(result["updated_repositories"]) == 0

    def test_collect_weekly_metadata_with_limits(self):
        """Test collection with max_repos_per_category limit."""
        # Create many mock repos
        many_new = [
            {"full_name": f"owner/new-repo-{i}", "name": f"new-repo-{i}", "stars": i}
            for i in range(10)
        ]
        many_updated = [
            {
                "full_name": f"owner/updated-repo-{i}",
                "name": f"updated-repo-{i}",
                "stars": i,
            }
            for i in range(10)
        ]

        self.mock_github_client.get_new_repositories.return_value = many_new
        self.mock_github_client.get_repositories_updated_since.return_value = (
            many_new + many_updated
        )

        # Mock get_repository to return None for all (skip detailed fetch)
        self.mock_github_client.get_repository.return_value = None

        result = self.collector.collect_weekly_metadata(max_repos_per_category=3)

        # Should only process up to 3 from each category
        assert result["summary"]["new_repositories_count"] <= 3
        assert result["summary"]["updated_repositories_count"] <= 3

    def test_collect_weekly_metadata_detailed_info_params(self):
        """Test that detailed info is fetched with correct parameters."""
        mock_repo_stats = {
            "full_name": "owner/test-repo",
            "name": "test-repo",
            "stars": 10,
        }
        self.mock_github_client.get_new_repositories.return_value = [mock_repo_stats]
        self.mock_github_client.get_repositories_updated_since.return_value = []

        mock_repo_obj = MagicMock()
        self.mock_github_client.get_repository.return_value = mock_repo_obj
        self.mock_github_client.get_repository_detailed_info.return_value = {
            "full_name": "owner/test-repo",
            "recent_commits": [],
            "releases": [],
            "readme": None,
        }

        self.collector.collect_weekly_metadata(commits_limit=30, releases_limit=5)

        # Verify get_repository_detailed_info was called with correct params
        self.mock_github_client.get_repository_detailed_info.assert_called_once()
        call_kwargs = self.mock_github_client.get_repository_detailed_info.call_args[1]
        assert call_kwargs["commits_limit"] == 30
        assert call_kwargs["releases_limit"] == 5
        assert call_kwargs["include_commits"] is True
        assert call_kwargs["include_releases"] is True
        assert call_kwargs["include_readme"] is True

    def test_collect_weekly_metadata_handles_errors(self):
        """Test that collection continues even if some repos fail."""
        mock_repo1 = {"full_name": "owner/working-repo", "name": "working-repo"}
        mock_repo2 = {"full_name": "owner/failing-repo", "name": "failing-repo"}
        mock_repo3 = {"full_name": "owner/also-working", "name": "also-working"}

        self.mock_github_client.get_new_repositories.return_value = [mock_repo1]
        self.mock_github_client.get_repositories_updated_since.return_value = [
            mock_repo2,
            mock_repo3,
        ]

        def mock_get_repository(full_name):
            # Return a mock repo object for all
            return MagicMock(full_name=full_name)

        def mock_get_detailed_info(repo, **kwargs):
            if repo.full_name == "owner/failing-repo":
                raise Exception("API Error")
            return {
                "full_name": repo.full_name,
                "name": repo.name,
                "recent_commits": [],
                "releases": [],
                "readme": None,
            }

        self.mock_github_client.get_repository.side_effect = mock_get_repository
        self.mock_github_client.get_repository_detailed_info.side_effect = (
            mock_get_detailed_info
        )

        result = self.collector.collect_weekly_metadata()

        # Should still collect the working repos (2 total: 1 new + 1 updated that works)
        assert result["summary"]["total_repos_processed"] == 2
        full_names = {
            r["full_name"]
            for r in result["new_repositories"] + result["updated_repositories"]
        }
        assert "owner/working-repo" in full_names
        assert "owner/also-working" in full_names
        assert "owner/failing-repo" not in full_names

    def test_summary_statistics_calculation(self):
        """Test summary statistics are calculated correctly."""
        repos = [
            {
                "stars": 10,
                "forks": 5,
                "language": "Python",
                "recent_commits": [{"sha": "1"}, {"sha": "2"}],
                "releases": [{"tag_name": "v1.0"}],
            },
            {
                "stars": 20,
                "forks": 3,
                "language": "Python",
                "recent_commits": [{"sha": "3"}],
                "releases": [],
            },
            {
                "stars": 5,
                "forks": 2,
                "language": "JavaScript",
                "recent_commits": [],
                "releases": [{"tag_name": "v2.0"}, {"tag_name": "v2.1"}],
            },
        ]

        # Mock to return these repos as both new and updated
        self.mock_github_client.get_new_repositories.return_value = [
            {"full_name": "owner/repo1", "name": "repo1"},
            {"full_name": "owner/repo2", "name": "repo2"},
            {"full_name": "owner/repo3", "name": "repo3"},
        ]
        self.mock_github_client.get_repositories_updated_since.return_value = []

        def mock_get_repo(full_name):
            mapping = {
                "owner/repo1": MagicMock(full_name="owner/repo1"),
                "owner/repo2": MagicMock(full_name="owner/repo2"),
                "owner/repo3": MagicMock(full_name="owner/repo3"),
            }
            return mapping.get(full_name)

        def mock_get_detailed_info(repo, **kwargs):
            return repos.pop(0) if repos else {}

        self.mock_github_client.get_repository.side_effect = mock_get_repo
        self.mock_github_client.get_repository_detailed_info.side_effect = (
            mock_get_detailed_info
        )

        result = self.collector.collect_weekly_metadata()

        summary = result["summary"]
        assert summary["total_stars"] == 35  # 10 + 20 + 5
        assert summary["total_forks"] == 10  # 5 + 3 + 2
        assert summary["languages"] == {"Python": 2, "JavaScript": 1}
        assert summary["recent_commits_count"] == 3  # 2 + 1 + 0
        assert summary["releases_count"] == 3  # 1 + 0 + 2

    def test_collection_dates(self):
        """Test that collection dates are set correctly."""
        self.mock_github_client.get_new_repositories.return_value = []
        self.mock_github_client.get_repositories_updated_since.return_value = []

        result = self.collector.collect_weekly_metadata()

        collection_date = datetime.fromisoformat(result["collection_date"])
        week_start = datetime.fromisoformat(result["week_start"])

        # Collection date should be recent (within last minute)
        time_diff = self.now - collection_date
        assert time_diff.total_seconds() < 60

        # Week start should be approximately 7 days ago
        expected_week_start = self.now - timedelta(days=7)
        week_diff = abs((week_start - expected_week_start).total_seconds())
        assert week_diff < 60

    def test_filter_recent_readme_updates(self):
        """Test filtering repositories with README updates."""
        repos = [
            {
                "full_name": "repo1",
                "pushed_at": (self.now - timedelta(days=1)).isoformat(),
            },
            {
                "full_name": "repo2",
                "pushed_at": (self.now - timedelta(days=3)).isoformat(),
            },
            {
                "full_name": "repo3",
                "pushed_at": (self.week_ago - timedelta(days=1)).isoformat(),
            },
            {"full_name": "repo4", "pushed_at": None},
        ]

        recent = self.collector.filter_recent_readme_updates(repos, self.week_ago)

        # Should include repos updated within the last week
        assert len(recent) == 2
        recent_names = {r["full_name"] for r in recent}
        assert "repo1" in recent_names
        assert "repo2" in recent_names
        assert "repo3" not in recent_names
        assert "repo4" not in recent_names

    def test_filter_recent_readme_updates_empty(self):
        """Test filtering with empty list."""
        result = self.collector.filter_recent_readme_updates([], self.week_ago)
        assert result == []

    def test_include_private_parameter(self):
        """Test that include_private is passed correctly."""
        mock_repo = {"full_name": "owner/repo", "name": "repo"}
        self.mock_github_client.get_new_repositories.return_value = [mock_repo]
        self.mock_github_client.get_repositories_updated_since.return_value = []
        self.mock_github_client.get_repository.return_value = None

        self.collector.collect_weekly_metadata(include_private=False)

        self.mock_github_client.get_new_repositories.assert_called_once_with(
            since=ANY, include_private=False
        )
        self.mock_github_client.get_repositories_updated_since.assert_called_once_with(
            since=ANY, include_private=False
        )
