"""Tests for markdown templates and report generator."""

import pytest
from datetime import datetime, timedelta
from src.scripts.templates import (
    format_date_range,
    generate_summary_statistics_section,
    generate_repository_card,
    generate_new_repositories_section,
    generate_notable_updates_section,
    generate_trending_repos_section,
    generate_call_to_action_section,
    generate_full_report,
    generate_social_media_summary,
)


@pytest.fixture
def sample_repo():
    """Sample repository data for testing."""
    return {
        "name": "test-repo",
        "full_name": "owner/test-repo",
        "description": "A test repository",
        "html_url": "https://github.com/owner/test-repo",
        "stars": 42,
        "forks": 10,
        "language": "Python",
        "created_at": "2024-01-10T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
        "recent_commits": [
            {
                "commit": {
                    "message": "Fix bug in login",
                    "author": {"name": "John Doe", "date": "2024-01-15T09:00:00Z"},
                }
            },
            {
                "commit": {
                    "message": "Add new feature",
                    "author": {"name": "Jane Smith", "date": "2024-01-14T14:30:00Z"},
                }
            },
        ],
        "releases": [
            {
                "tag_name": "v1.0.0",
                "name": "Initial release",
                "published_at": "2024-01-12T12:00:00Z",
            }
        ],
    }


@pytest.fixture
def sample_metadata():
    """Sample weekly metadata for testing."""
    now = datetime.now()
    week_start = now - timedelta(days=7)

    return {
        "collection_date": now.isoformat(),
        "week_start": week_start.isoformat(),
        "summary": {
            "total_repos_processed": 5,
            "new_repositories_count": 2,
            "updated_repositories_count": 3,
            "total_stars": 150,
            "total_forks": 30,
            "languages": {"Python": 3, "JavaScript": 2},
            "recent_commits_count": 15,
            "releases_count": 2,
        },
        "new_repositories": [
            {
                "name": "new-repo-1",
                "full_name": "owner/new-repo-1",
                "description": "A new repository",
                "html_url": "https://github.com/owner/new-repo-1",
                "stars": 10,
                "forks": 2,
                "language": "Python",
                "created_at": "2024-01-10T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
                "recent_commits": [],
                "releases": [],
            },
            {
                "name": "new-repo-2",
                "full_name": "owner/new-repo-2",
                "description": "Another new repository",
                "html_url": "https://github.com/owner/new-repo-2",
                "stars": 5,
                "forks": 1,
                "language": "JavaScript",
                "created_at": "2024-01-11T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
                "recent_commits": [],
                "releases": [],
            },
        ],
        "updated_repositories": [
            {
                "name": "existing-repo-1",
                "full_name": "owner/existing-repo-1",
                "description": "An existing repository with updates",
                "html_url": "https://github.com/owner/existing-repo-1",
                "stars": 50,
                "forks": 15,
                "language": "Python",
                "created_at": "2023-12-01T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
                "recent_commits": [],
                "releases": [],
            }
        ],
    }


class TestFormatDateRange:
    """Tests for date range formatting."""

    def test_format_date_range(self):
        """Test date range formatting."""
        week_start = datetime(2024, 1, 8)
        collection_date = datetime(2024, 1, 16)
        result = format_date_range(week_start, collection_date)
        assert "January" in result
        assert "2024" in result
        assert "8" in result
        assert "15" in result


class TestGenerateSummaryStatisticsSection:
    """Tests for summary statistics generation."""

    def test_generate_empty_summary(self):
        """Test with empty summary."""
        summary = {}
        result = generate_summary_statistics_section(summary)
        assert "## 📊 Summary Statistics" in result
        assert "Total Repositories" in result

    def test_generate_full_summary(self, sample_metadata):
        """Test with full summary data."""
        summary = sample_metadata["summary"]
        result = generate_summary_statistics_section(summary)

        assert "## 📊 Summary Statistics" in result
        assert "| Total Repositories | 5 |" in result
        assert "| New Repositories | 🆕 2 |" in result
        assert "| Updated Repositories | 🔄 3 |" in result
        assert "| Total Stars | ⭐ 150 |" in result
        assert "| Total Forks | 🍴 30 |" in result
        assert "| Recent Commits | 💻 15 |" in result
        assert "| Releases | 📦 2 |" in result
        assert "### Languages Used" in result
        assert "| Python | 3 |" in result
        assert "| JavaScript | 2 |" in result

    def test_languages_sorted_by_count(self):
        """Test that languages are sorted by count descending."""
        summary = {"languages": {"Python": 1, "JavaScript": 3, "Go": 2}}
        result = generate_summary_statistics_section(summary)
        # JavaScript should appear before Go, Go before Python
        js_pos = result.find("JavaScript")
        go_pos = result.find("Go")
        python_pos = result.find("Python")
        assert js_pos < go_pos < python_pos


class TestGenerateRepositoryCard:
    """Tests for repository card generation."""

    def test_generate_basic_card(self, sample_repo):
        """Test basic repository card."""
        result = generate_repository_card(sample_repo)

        assert "### [owner/test-repo](https://github.com/owner/test-repo)" in result
        assert "> A test repository" in result
        assert "⭐ 42" in result
        assert "🍴 10" in result
        assert "💻 Python" in result

    def test_card_without_description(self, sample_repo):
        """Test card without description."""
        repo = sample_repo.copy()
        repo["description"] = ""
        result = generate_repository_card(repo, show_description=True)
        assert ">" not in result

    def test_card_with_commits(self, sample_repo):
        """Test card with recent commits."""
        result = generate_repository_card(sample_repo)
        assert "**Recent Commits:**" in result
        assert "`Fix bug in login`" in result
        assert "*John Doe*" in result

    def test_card_with_releases(self, sample_repo):
        """Test card with releases."""
        result = generate_repository_card(sample_repo)
        assert "**Recent Releases:**" in result
        assert "v1.0.0" in result

    def test_truncate_long_commit_message(self, sample_repo):
        """Test that long commit messages are truncated."""
        repo = sample_repo.copy()
        repo["recent_commits"] = [
            {
                "commit": {
                    "message": "A" * 100,  # Very long message
                    "author": {"name": "Test", "date": "2024-01-15T09:00:00Z"},
                }
            }
        ]
        result = generate_repository_card(repo)
        assert "..." in result
        # Should be truncated to 60 chars max
        assert len(result.split("`")[1].split("`")[0]) <= 60


class TestGenerateNewRepositoriesSection:
    """Tests for new repositories section."""

    def test_generate_with_new_repos(self, sample_metadata):
        """Test with new repositories."""
        new_repos = sample_metadata["new_repositories"]
        result = generate_new_repositories_section(new_repos)

        assert "## 🆕 New Repositories" in result
        assert "Found **2** new repositories" in result
        assert "owner/new-repo-1" in result
        assert "owner/new-repo-2" in result

    def test_generate_empty_list(self):
        """Test with empty list."""
        result = generate_new_repositories_section([])
        assert "## 🆕 New Repositories" in result
        assert "*No new repositories this week.*" in result


class TestGenerateNotableUpdatesSection:
    """Tests for notable updates section."""

    def test_generate_with_updated_repos(self, sample_metadata):
        """Test with updated repositories."""
        updated_repos = sample_metadata["updated_repositories"]
        result = generate_notable_updates_section(updated_repos)

        assert "## 🔄 Notable Updates" in result
        assert "Showing top **1** most starred updated repositories" in result
        assert "owner/existing-repo-1" in result

    def test_sorted_by_stars(self):
        """Test that repositories are sorted by stars."""
        repos = [
            {"full_name": "repo1", "stars": 10},
            {"full_name": "repo2", "stars": 100},
            {"full_name": "repo3", "stars": 50},
        ]
        result = generate_notable_updates_section(repos)
        # repo2 should appear before repo3, repo3 before repo1
        repo2_pos = result.find("repo2")
        repo3_pos = result.find("repo3")
        repo1_pos = result.find("repo1")
        assert repo2_pos < repo3_pos < repo1_pos

    def test_limit_results(self):
        """Test limiting to top N repos."""
        repos = [{"full_name": f"repo{i}", "stars": i} for i in range(20)]
        result = generate_notable_updates_section(repos)
        # Should only show top 10 by default
        assert "repo19" in result  # highest stars
        assert "repo0" not in result  # lowest stars

    def test_generate_empty_list(self):
        """Test with empty list."""
        result = generate_notable_updates_section([])
        assert "## 🔄 Notable Updates" in result
        assert "*No significant updates this week.*" in result


class TestGenerateTrendingReposSection:
    """Tests for trending repositories section."""

    def test_generate_with_repos(self, sample_metadata):
        """Test with repos."""
        all_repos = (
            sample_metadata["new_repositories"]
            + sample_metadata["updated_repositories"]
        )
        result = generate_trending_repos_section(
            sample_metadata["new_repositories"], sample_metadata["updated_repositories"]
        )

        assert "## 📈 Trending Repositories" in result
        assert "Top **" in result
        assert "trending repositories this week" in result

    def test_empty_list(self):
        """Test with no repos."""
        result = generate_trending_repos_section([], [])
        assert "## 📈 Trending Repositories" in result
        assert "*No trending data available.*" in result


class TestGenerateCallToActionSection:
    """Tests for CTA section."""

    def test_generate_cta(self):
        """Test CTA section generation."""
        result = generate_call_to_action_section()

        assert "## 🚀 Call to Action" in result
        assert "Check out these awesome repositories" in result
        assert "**Star** repos you find interesting" in result
        assert "**Fork** and contribute to projects" in result
        assert "**Share** this report" in result
        assert "**Follow** me on GitHub" in result
        assert "This report was automatically generated by **Wiggum Report**" in result
        assert "[source code]" in result


class TestGenerateFullReport:
    """Tests for full report generation."""

    def test_generate_full_report(self, sample_metadata):
        """Test complete report generation."""
        result = generate_full_report(sample_metadata)

        # Check all sections are present
        assert "# 📰 Wiggum Weekly Report" in result
        assert "## 📊 Summary Statistics" in result
        assert "## 🆕 New Repositories" in result
        assert "## 🔄 Notable Updates" in result
        assert "## 📈 Trending Repositories" in result
        assert "## 🚀 Call to Action" in result

        # Check content
        assert "owner/new-repo-1" in result
        assert "owner/existing-repo-1" in result
        assert "| Metric | Count |" in result

    def test_generate_with_empty_data(self):
        """Test with empty metadata."""
        metadata = {
            "collection_date": datetime.now().isoformat(),
            "week_start": (datetime.now() - timedelta(days=7)).isoformat(),
            "summary": {
                "total_repos_processed": 0,
                "new_repositories_count": 0,
                "updated_repositories_count": 0,
                "total_stars": 0,
                "total_forks": 0,
                "languages": {},
                "recent_commits_count": 0,
                "releases_count": 0,
            },
            "new_repositories": [],
            "updated_repositories": [],
        }
        result = generate_full_report(metadata)

        assert "# 📰 Wiggum Weekly Report" in result
        assert "*No new repositories this week.*" in result
        assert "*No significant updates this week.*" in result
        assert "*No trending data available.*" in result


class TestGenerateSocialMediaSummary:
    """Tests for social media summary generation."""

    def test_generate_x_summary(self, sample_metadata):
        """Test X/Twitter summary generation."""
        result = generate_social_media_summary(sample_metadata, platform="x")

        assert "🧵 Weekly GitHub roundup!" in result
        assert "📊 5 repos" in result
        assert "2 new" in result
        assert "3 updated" in result
        assert "⭐ 150 total stars" in result
        assert "#WiggumReport #GitHub #OpenSource" in result
        # Should be <= 280 characters
        assert len(result) <= 280

    def test_generate_linkedin_summary(self, sample_metadata):
        """Test LinkedIn summary generation."""
        result = generate_social_media_summary(sample_metadata, platform="linkedin")

        assert "📢 Weekly GitHub Activity Update" in result
        assert "• Total repositories: 5" in result
        assert "• New repositories: 2" in result
        assert "• Updated repositories: 3" in result
        assert "• Total stars earned: ⭐ 150" in result
        assert "#OpenSource #GitHub #WiggumReport" in result

    def test_truncate_for_x_when_needed(self):
        """Test truncation for X platform when content exceeds limit."""
        # Create metadata with many repos to force truncation
        many_new_repos = [{"name": f"repo{i}"} for i in range(50)]
        metadata = {
            "summary": {
                "total_repos_processed": 100,
                "new_repositories_count": 50,
                "updated_repositories_count": 50,
                "total_stars": 1000,
            },
            "new_repositories": many_new_repos,
        }
        result = generate_social_media_summary(metadata, platform="x")
        assert len(result) <= 280
