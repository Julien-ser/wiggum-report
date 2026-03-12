# flake8: noqa: E501
"""Tests for social media platform adapters."""

import pytest
from src.social_platforms.x_adapter import XAdapter
from src.social_platforms.linkedin_adapter import LinkedInAdapter
from datetime import datetime, timedelta


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


class TestXAdapter:
    """Tests for X (Twitter) adapter."""

    def test_adapter_properties(self):
        """Test adapter properties."""
        adapter = XAdapter()
        assert adapter.platform_name == "x"
        assert adapter.max_length == 280

    def test_adapter_with_custom_max_length(self):
        """Test adapter with custom max length."""
        adapter = XAdapter(max_length=200)
        assert adapter.max_length == 200

    def test_format_basic(self, sample_metadata):
        """Test basic formatting with sample data."""
        adapter = XAdapter()
        result = adapter.format(sample_metadata)

        assert "🧵 Weekly GitHub roundup!" in result
        assert "📊 5 repos" in result
        assert "2 new" in result
        assert "3 updated" in result
        assert (
            "⭐ 150 stars" in result
        )  # Note: not "total stars" in adapter output  # noqa: E501
        assert "#WiggumReport #GitHub #OpenSource" in result
        assert len(result) <= 280

    def test_format_with_new_repos(self, sample_metadata):
        """Test that new repositories are included."""
        adapter = XAdapter()
        result = adapter.format(sample_metadata)

        assert "🆕 New repos:" in result
        assert "`new-repo-1`" in result or "new-repo-1" in result
        assert "`new-repo-2`" in result or "new-repo-2" in result

    def test_format_with_trending(self, sample_metadata):
        """Test that trending/updated repositories are included."""
        adapter = XAdapter()
        result = adapter.format(sample_metadata)

        assert "🔥 Top updated:" in result
        assert "existing-repo-1" in result

    def test_truncation_when_over_limit(self):
        """Test that content is truncated when exceeding limit."""
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
            "updated_repositories": many_new_repos[:10],
        }
        adapter = XAdapter()
        result = adapter.format(metadata)
        assert len(result) <= 280

    def test_empty_metadata(self):
        """Test with empty metadata."""
        metadata = {
            "summary": {
                "total_repos_processed": 0,
                "new_repositories_count": 0,
                "updated_repositories_count": 0,
                "total_stars": 0,
            },
            "new_repositories": [],
            "updated_repositories": [],
        }
        adapter = XAdapter()
        result = adapter.format(metadata)

        assert "🧵 Weekly GitHub roundup!" in result
        assert "0 repos" in result
        assert len(result) <= 280

    def test_hashtags_included(self, sample_metadata):
        """Test that required hashtags are included."""
        adapter = XAdapter()
        result = adapter.format(sample_metadata)

        assert "#WiggumReport" in result
        assert "#GitHub" in result
        assert "#OpenSource" in result

    def test_repo_names_limited_to_top_3(self):
        """Test that only top 3 new repos are shown."""
        many_new_repos = [{"name": f"repo{i}"} for i in range(10)]
        metadata = {
            "summary": {
                "total_repos_processed": 10,
                "new_repositories_count": 10,
                "updated_repositories_count": 0,
                "total_stars": 100,
            },
            "new_repositories": many_new_repos,
            "updated_repositories": [],
        }
        adapter = XAdapter()
        result = adapter.format(metadata)

        # Should show first 3
        assert "repo0" in result or "`repo0`" in result
        assert "repo1" in result or "`repo1`" in result
        assert "repo2" in result or "`repo2`" in result
        # And mention there are more
        assert "+7 more" in result

    def test_updated_repos_limited_to_top_2(self):
        """Test that only top 2 updated repos are shown."""
        many_updated = [{"name": f"repo{i}", "stars": i * 10} for i in range(10, 0, -1)]
        metadata = {
            "summary": {
                "total_repos_processed": 10,
                "new_repositories_count": 0,
                "updated_repositories_count": 10,
                "total_stars": 100,
            },
            "new_repositories": [],
            "updated_repositories": many_updated,
        }
        adapter = XAdapter()
        result = adapter.format(metadata)

        # Should show top 2 by stars (repo10 and repo9 have highest stars in this dataset)
        assert "repo10" in result or "`repo10`" in result
        assert "repo9" in result or "`repo9`" in result
        # And mention there are more
        assert "+8 more" in result


class TestLinkedInAdapter:
    """Tests for LinkedIn adapter."""

    def test_adapter_properties(self):
        """Test adapter properties."""
        adapter = LinkedInAdapter()
        assert adapter.platform_name == "linkedin"
        assert adapter.max_length == 3000

    def test_adapter_with_custom_max_length(self):
        """Test adapter with custom max length."""
        adapter = LinkedInAdapter(max_length=2000)
        assert adapter.max_length == 2000

    def test_format_basic(self, sample_metadata):
        """Test basic formatting with sample data."""
        adapter = LinkedInAdapter()
        result = adapter.format(sample_metadata)

        assert "📢 Weekly GitHub Activity Update" in result
        assert "**Period**:" in result
        assert "• Total repositories processed: 5" in result
        assert "• New repositories: 2" in result
        assert "• Updated repositories: 3" in result
        assert "• Total stars earned: ⭐ 150" in result
        assert "#OpenSource #GitHub #SoftwareDevelopment #WiggumReport" in result
        assert len(result) <= 3000

    def test_format_includes_sections(self, sample_metadata):
        """Test that all expected sections are included."""
        adapter = LinkedInAdapter()
        result = adapter.format(sample_metadata)

        assert "### Summary" in result
        assert "### Languages Used" in result
        assert "### 🆕 New Repositories" in result
        assert "### 🔄 Notable Updates" in result
        assert "### 🚀 Call to Action" in result

    def test_format_with_new_repos(self, sample_metadata):
        """Test that new repositories are listed."""
        adapter = LinkedInAdapter()
        result = adapter.format(sample_metadata)

        assert "owner/new-repo-1" in result
        assert "owner/new-repo-2" in result
        assert "A new repository" in result or "Another new repository" in result

    def test_format_with_updated_repos(self, sample_metadata):
        """Test that updated repositories are listed."""
        adapter = LinkedInAdapter()
        result = adapter.format(sample_metadata)

        assert "owner/existing-repo-1" in result
        assert "An existing repository with updates" in result

    def test_languages_section(self, sample_metadata):
        """Test that languages are shown."""
        adapter = LinkedInAdapter()
        result = adapter.format(sample_metadata)

        assert "Python: 3" in result or "Python : 3" in result
        assert "JavaScript: 2" in result or "JavaScript : 2" in result

    def test_truncation_when_over_limit(self):
        """Test that content is truncated when exceeding limit."""
        # Create metadata with many repos to force truncation
        many_new_repos = [
            {
                "name": f"repo{i}",
                "full_name": f"owner/repo{i}",
                "description": f"Description for repo {i}" * 10,
                "html_url": f"https://github.com/owner/repo{i}",
                "stars": i,
                "language": "Python",
            }
            for i in range(50)
        ]
        metadata = {
            "summary": {
                "total_repos_processed": 50,
                "new_repositories_count": 50,
                "updated_repositories_count": 0,
                "total_stars": 1000,
                "languages": {"Python": 50},
            },
            "new_repositories": many_new_repos,
            "updated_repositories": [],
        }
        adapter = LinkedInAdapter(max_length=1000)  # Set smaller limit for test
        result = adapter.format(metadata)
        assert len(result) <= 1000
        # Should still contain key sections
        assert "📢 Weekly GitHub Activity Update" in result
        assert "### Summary" in result

    def test_repo_links_included(self, sample_metadata):
        """Test that repository URLs are properly formatted."""
        adapter = LinkedInAdapter()
        result = adapter.format(sample_metadata)

        # Should contain markdown links
        assert "[owner/new-repo-1](https://github.com/owner/new-repo-1)" in result
        assert "[owner/new-repo-2](https://github.com/owner/new-repo-2)" in result

    def test_call_to_action_included(self, sample_metadata):
        """Test that CTA is included."""
        adapter = LinkedInAdapter()
        result = adapter.format(sample_metadata)

        assert (
            "Explore these repositories" in result
            or "contribute to open source" in result
        )
        assert "**Wiggum Report**" in result

    def test_date_range_formatted(self, sample_metadata):
        """Test that date range is properly formatted."""
        adapter = LinkedInAdapter()
        result = adapter.format(sample_metadata)

        # Should contain a date range with month name
        assert (
            "January" in result
            or "February" in result
            or "March" in result
            or "April" in result
            or "May" in result
            or "June" in result
            or "July" in result
            or "August" in result
            or "September" in result
            or "October" in result
            or "November" in result
            or "December" in result
        )

    def test_limits_new_repos_to_five(self):
        """Test that only top 5 new repos are shown."""
        many_new = [
            {
                "name": f"repo{i}",
                "full_name": f"owner/repo{i}",
                "html_url": f"https://github.com/owner/repo{i}",
                "stars": i,
            }
            for i in range(10)
        ]
        metadata = {
            "summary": {
                "total_repos_processed": 10,
                "new_repositories_count": 10,
                "updated_repositories_count": 0,
                "total_stars": 100,
            },
            "new_repositories": many_new,
            "updated_repositories": [],
        }
        adapter = LinkedInAdapter()
        result = adapter.format(metadata)

        # Should list up to 5 repos
        repo_count = (
            result.count("1.")
            + result.count("2.")
            + result.count("3.")
            + result.count("4.")
            + result.count("5.")
        )
        assert repo_count <= 5

    def test_limits_updated_repos_to_five(self):
        """Test that only top 5 updated repos are shown."""
        many_updated = [
            {
                "name": f"repo{i}",
                "full_name": f"owner/repo{i}",
                "html_url": f"https://github.com/owner/repo{i}",
                "stars": i,
            }
            for i in range(10)
        ]
        metadata = {
            "summary": {
                "total_repos_processed": 10,
                "new_repositories_count": 0,
                "updated_repositories_count": 10,
                "total_stars": 100,
            },
            "new_repositories": [],
            "updated_repositories": many_updated,
        }
        adapter = LinkedInAdapter()
        result = adapter.format(metadata)

        # Should list up to 5 repos in notable updates section
        # Counting numbered items in "Notable Updates" section
        if "### 🔄 Notable Updates" in result:
            section = result.split("### 🔄 Notable Updates")[1].split("###")[0]
            repo_count = (
                section.count("1.")
                + section.count("2.")
                + section.count("3.")
                + section.count("4.")
                + section.count("5.")
            )
            assert repo_count <= 5
