"""Unit tests for GitHub client."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from github import GithubException, Repository as PyGithubRepository

from src.github_client import GitHubClient


class TestGitHubClient:
    """Test cases for GitHubClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.token = "test_token"
        self.client = GitHubClient(self.token)
        self.mock_github = MagicMock()
        self.client.github = self.mock_github

    def test_init(self):
        """Test client initialization."""
        client = GitHubClient("my_token")
        assert client.token == "my_token"

    def test_get_authenticated_user_success(self):
        """Test successful user retrieval."""
        mock_user = MagicMock()
        mock_user.login = "testuser"
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        mock_user.html_url = "https://github.com/testuser"
        mock_user.avatar_url = "https://avatar.url"
        mock_user.public_repos = 10
        mock_user.total_private_repos = 5
        mock_user.type = "User"

        self.mock_github.get_user.return_value = mock_user

        result = self.client.get_authenticated_user()

        assert result["login"] == "testuser"
        assert result["name"] == "Test User"
        assert result["email"] == "test@example.com"
        assert result["public_repos"] == 10
        assert result["total_private_repos"] == 5

    def test_get_authenticated_user_org(self):
        """Test user retrieval for organization."""
        mock_user = MagicMock()
        mock_user.login = "testorg"
        mock_user.name = "Test Org"
        mock_user.email = None
        mock_user.public_repos = 20
        mock_user.total_private_repos = None
        mock_user.type = "Organization"

        self.mock_github.get_user.return_value = mock_user

        result = self.client.get_authenticated_user()

        assert result["login"] == "testorg"
        assert result["total_private_repos"] is None

    def test_get_authenticated_user_failure(self):
        """Test user retrieval failure."""
        self.mock_github.get_user.side_effect = GithubException(401, "Unauthorized")

        with pytest.raises(GithubException) as exc_info:
            self.client.get_authenticated_user()
        assert "Failed to authenticate" in str(exc_info.value)

    def test_get_repositories_success(self):
        """Test successful repository retrieval."""
        mock_repo1 = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo1.private = False

        mock_repo2 = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo2.private = True

        mock_user = MagicMock()
        mock_user.get_repos.return_value = [mock_repo1, mock_repo2]

        self.mock_github.get_user.return_value = mock_user

        repos = self.client.get_repositories(include_private=True)
        assert len(repos) == 2

    def test_get_repositories_exclude_private(self):
        """Test repository retrieval excluding private repos."""
        mock_repo1 = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo1.private = False

        mock_repo2 = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo2.private = True

        mock_user = MagicMock()
        mock_user.get_repos.return_value = [mock_repo1, mock_repo2]

        self.mock_github.get_user.return_value = mock_user

        repos = self.client.get_repositories(include_private=False)
        assert len(repos) == 1
        assert repos[0].private is False

    def test_get_repository_success(self):
        """Test getting specific repository."""
        mock_repo = MagicMock(spec=PyGithubRepository.Repository)
        self.mock_github.get_repo.return_value = mock_repo

        result = self.client.get_repository("owner/repo")

        assert result == mock_repo
        self.mock_github.get_repo.assert_called_once_with("owner/repo")

    def test_get_repository_not_found(self):
        """Test repository not found."""
        self.mock_github.get_repo.side_effect = GithubException(404, "Not Found")

        result = self.client.get_repository("nonexistent/repo")
        assert result is None

    def test_get_repository_stats_basic(self):
        """Test repository stats extraction (basic fields)."""
        mock_repo = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo.name = "test-repo"
        mock_repo.full_name = "owner/test-repo"
        mock_repo.description = "A test repository"
        mock_repo.html_url = "https://github.com/owner/test-repo"
        mock_repo.private = False
        mock_repo.stargazers_count = 10
        mock_repo.forks_count = 5
        mock_repo.watchers_count = 3
        mock_repo.open_issues_count = 2
        mock_repo.created_at = datetime(2024, 1, 1)
        mock_repo.updated_at = datetime(2024, 1, 15)
        mock_repo.pushed_at = datetime(2024, 1, 10)
        mock_repo.default_branch = "main"
        mock_repo.language = "Python"
        mock_repo.size = 1024
        mock_repo.has_wiki = True
        mock_repo.has_pages = False
        mock_repo.archived = False
        mock_repo.disabled = False

        # Mock get_topics
        mock_repo.get_topics.return_value = ["test", "api"]

        # Simulate commit count retrieval failure
        mock_repo.get_commits.side_effect = Exception("API error")

        stats = self.client.get_repository_stats(mock_repo)

        assert stats["name"] == "test-repo"
        assert stats["full_name"] == "owner/test-repo"
        assert stats["description"] == "A test repository"
        assert stats["stars"] == 10
        assert stats["forks"] == 5
        assert stats["topics"] == ["test", "api"]
        assert stats["size_kb"] == 1024
        assert (
            stats["commit_count"] is None
        )  # May be None if default branch not available

    def test_get_recent_commits_success(self):
        """Test successful commit retrieval."""
        mock_repo = MagicMock(spec=PyGithubRepository.Repository)

        mock_commit1 = MagicMock()
        mock_commit1.sha = "abc123def456"
        mock_commit1.commit.message = "Fix bug"
        mock_commit1.commit.author = MagicMock()
        mock_commit1.commit.author.name = "Developer"
        mock_commit1.commit.author.email = "dev@example.com"
        mock_commit1.commit.author.date = datetime(2024, 1, 15, 10, 0)
        mock_commit1.html_url = "https://github.com/owner/repo/commit/abc123"

        mock_commit2 = MagicMock()
        mock_commit2.sha = "def789abc012"
        mock_commit2.commit.message = "Add feature"
        mock_commit2.commit.author = None
        mock_commit2.html_url = "https://github.com/owner/repo/commit/def789"

        commits_list = [mock_commit1, mock_commit2]
        mock_commit_iter = MagicMock()
        mock_commit_iter.__iter__.return_value = iter(commits_list)
        mock_repo.get_commits.return_value = mock_commit_iter

        result = self.client.get_recent_commits(mock_repo, limit=10)

        assert len(result) == 2
        assert result[0]["sha"] == "abc123de"  # Truncated to 8 chars
        assert result[0]["message"] == "Fix bug"
        assert result[0]["author"] == "Developer"
        assert result[0]["email"] == "dev@example.com"
        assert result[1]["author"] is None

    def test_get_recent_commits_with_since_filter(self):
        """Test commit retrieval with since filter."""
        mock_repo = MagicMock(spec=PyGithubRepository.Repository)
        mock_commit_iter = MagicMock()
        mock_commit_iter.__iter__.return_value = iter([])  # No commits
        mock_repo.get_commits.return_value = mock_commit_iter

        since_date = datetime(2024, 1, 1)
        self.client.get_recent_commits(mock_repo, since=since_date, limit=10)

        mock_repo.get_commits.assert_called_once()
        call_args = mock_repo.get_commits.call_args
        # Verify that since parameter is passed via .since() method
        assert mock_commit_iter.since.called

    def test_get_releases_success(self):
        """Test successful release retrieval."""
        mock_repo = MagicMock(spec=PyGithubRepository.Repository)

        mock_release1 = MagicMock()
        mock_release1.tag_name = "v1.0.0"
        mock_release1.name = "Version 1.0.0"
        mock_release1.body = "Initial release"
        mock_release1.draft = False
        mock_release1.prerelease = False
        mock_release1.created_at = datetime(2024, 1, 15)
        mock_release1.published_at = datetime(2024, 1, 16)
        mock_release1.html_url = "https://github.com/owner/repo/releases/v1.0.0"
        mock_release1.get_assets.return_value = [MagicMock(), MagicMock()]  # 2 assets

        mock_release2 = MagicMock()
        mock_release2.tag_name = "v0.9.0-beta"
        mock_release2.name = None
        mock_release2.body = "Beta release"
        mock_release2.draft = True
        mock_release2.prerelease = True
        mock_release2.created_at = datetime(2024, 1, 10)
        mock_release2.published_at = None
        mock_release2.html_url = "https://github.com/owner/repo/releases/v0.9.0-beta"
        mock_release2.get_assets.return_value = []

        mock_repo.get_releases.return_value = [mock_release1, mock_release2]

        result = self.client.get_releases(mock_repo, limit=10)

        assert len(result) == 2
        assert result[0]["tag_name"] == "v1.0.0"
        assert result[0]["assets_count"] == 2
        assert result[0]["draft"] is False
        assert result[1]["name"] is None
        assert result[1]["draft"] is True

    def test_get_readme_success(self):
        """Test successful README retrieval."""
        mock_repo = MagicMock(spec=PyGithubRepository.Repository)
        mock_readme = MagicMock()
        mock_readme.path = "README.md"
        mock_readme.sha = "abc123"
        mock_readme.decoded_content = b"# Test Repository\n\nThis is a test."
        mock_readme.size = 50
        mock_readme.download_url = (
            "https://raw.githubusercontent.com/owner/repo/main/README.md"
        )

        mock_repo.get_readme.return_value = mock_readme

        result = self.client.get_readme(mock_repo)

        assert result is not None
        assert result["path"] == "README.md"
        assert result["content"] == "# Test Repository\n\nThis is a test."
        assert result["size"] == 50

    def test_get_readme_not_found(self):
        """Test README not found."""
        mock_repo = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo.get_readme.side_effect = GithubException(404, "Not Found")

        result = self.client.get_readme(mock_repo)
        assert result is None

    def test_get_repositories_updated_since(self):
        """Test filtering repositories by update date."""
        mock_repo1 = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo1.updated_at = datetime(2024, 1, 15)
        mock_repo1.private = False
        mock_repo1.name = "repo1"
        mock_repo1.full_name = "owner/repo1"
        mock_repo1.description = "Updated repo"
        mock_repo1.html_url = "https://github.com/owner/repo1"
        mock_repo1.stargazers_count = 5
        mock_repo1.forks_count = 2
        mock_repo1.watchers_count = 3
        mock_repo1.open_issues_count = 1
        mock_repo1.created_at = datetime(2024, 1, 1)
        mock_repo1.pushed_at = datetime(2024, 1, 15)
        mock_repo1.default_branch = "main"
        mock_repo1.language = "Python"
        mock_repo1.size = 512
        mock_repo1.has_wiki = False
        mock_repo1.has_pages = False
        mock_repo1.archived = False
        mock_repo1.disabled = False

        mock_repo2 = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo2.updated_at = datetime(2024, 1, 5)  # Older
        mock_repo2.private = False

        mock_user = MagicMock()
        mock_user.get_repos.return_value = [mock_repo1, mock_repo2]
        self.mock_github.get_user.return_value = mock_user

        since_date = datetime(2024, 1, 10)
        result = self.client.get_repositories_updated_since(since_date)

        assert len(result) == 1
        assert result[0]["name"] == "repo1"

    def test_get_new_repositories(self):
        """Test filtering repositories by creation date."""
        mock_repo1 = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo1.created_at = datetime(2024, 1, 15)
        mock_repo1.private = False
        mock_repo1.name = "new-repo"
        mock_repo1.full_name = "owner/new-repo"
        mock_repo1.description = "Newly created"
        mock_repo1.html_url = "https://github.com/owner/new-repo"
        mock_repo1.stargazers_count = 0
        mock_repo1.forks_count = 0
        mock_repo1.watchers_count = 0
        mock_repo1.open_issues_count = 0
        mock_repo1.updated_at = datetime(2024, 1, 15)
        mock_repo1.pushed_at = datetime(2024, 1, 15)
        mock_repo1.default_branch = "main"
        mock_repo1.language = "Python"
        mock_repo1.size = 0
        mock_repo1.has_wiki = False
        mock_repo1.has_pages = False
        mock_repo1.archived = False
        mock_repo1.disabled = False

        mock_repo2 = MagicMock(spec=PyGithubRepository.Repository)
        mock_repo2.created_at = datetime(2024, 1, 5)  # Older
        mock_repo2.private = False

        mock_user = MagicMock()
        mock_user.get_repos.return_value = [mock_repo1, mock_repo2]
        self.mock_github.get_user.return_value = mock_user

        since_date = datetime(2024, 1, 10)
        result = self.client.get_new_repositories(since_date)

        assert len(result) == 1
        assert result[0]["name"] == "new-repo"

    def test_get_repository_detailed_info(self):
        """Test comprehensive repository info retrieval."""
        mock_repo = MagicMock(spec=PyGithubRepository.Repository)

        # Basic stats
        mock_repo.name = "detailed-repo"
        mock_repo.full_name = "owner/detailed-repo"
        mock_repo.description = "A detailed repository"
        mock_repo.html_url = "https://github.com/owner/detailed-repo"
        mock_repo.private = False
        mock_repo.stargazers_count = 25
        mock_repo.forks_count = 10
        mock_repo.watchers_count = 15
        mock_repo.open_issues_count = 3
        mock_repo.created_at = datetime(2024, 1, 1)
        mock_repo.updated_at = datetime(2024, 1, 15)
        mock_repo.pushed_at = datetime(2024, 1, 14)
        mock_repo.default_branch = "main"
        mock_repo.language = "Python"
        mock_repo.size = 2048
        mock_repo.has_wiki = False
        mock_repo.has_pages = False
        mock_repo.archived = False
        mock_repo.disabled = False
        mock_repo.get_topics.return_value = ["detailed", "test"]

        # Commits
        mock_commit = MagicMock()
        mock_commit.sha = "abc123"
        mock_commit.commit.message = "Test commit"
        mock_commit.commit.author = None
        mock_commit.html_url = "https://github.com/owner/repo/commit/abc123"
        mock_commit_iter = MagicMock()
        mock_commit_iter.__iter__.return_value = iter([mock_commit])
        mock_repo.get_commits.return_value = mock_commit_iter

        # Releases
        mock_release = MagicMock()
        mock_release.tag_name = "v1.0"
        mock_release.name = "Release 1.0"
        mock_release.body = "Features"
        mock_release.draft = False
        mock_release.prerelease = False
        mock_release.created_at = datetime(2024, 1, 10)
        mock_release.published_at = datetime(2024, 1, 11)
        mock_release.html_url = "https://github.com/owner/repo/releases/v1.0"
        mock_release.get_assets.return_value = []
        mock_repo.get_releases.return_value = [mock_release]

        # README
        mock_readme = MagicMock()
        mock_readme.path = "README.md"
        mock_readme.sha = "def456"
        mock_readme.decoded_content = b"# Title\n\nContent"
        mock_readme.size = 20
        mock_readme.download_url = (
            "https://raw.githubusercontent.com/owner/repo/main/README.md"
        )
        mock_repo.get_readme.return_value = mock_readme

        result = self.client.get_repository_detailed_info(
            mock_repo,
            include_commits=True,
            include_releases=True,
            include_readme=True,
            commits_limit=10,
            releases_limit=5,
        )

        assert result["name"] == "detailed-repo"
        assert "recent_commits" in result
        assert len(result["recent_commits"]) == 1
        assert "releases" in result
        assert len(result["releases"]) == 1
        assert "readme" in result
        assert result["readme"]["content"] == "# Title\n\nContent"

    def test_from_settings(self):
        """Test creating client from Settings."""
        mock_settings = MagicMock()
        mock_settings.github_token = "token_from_settings"

        client = GitHubClient.from_settings(mock_settings)

        assert client.token == "token_from_settings"

    def test_close(self):
        """Test closing client."""
        mock_close = MagicMock()
        self.client.github.close = mock_close

        self.client.close()
        mock_close.assert_called_once()
