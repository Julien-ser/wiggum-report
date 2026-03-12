"""Repository metadata collector for gathering weekly GitHub data."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.github_client import GitHubClient
from src.data_persistence import DataPersistence


class MetadataCollector:
    """Collects repository metadata for weekly reports."""

    def __init__(
        self,
        github_client: GitHubClient,
        data_persistence: Optional[DataPersistence] = None,
    ):
        """
        Initialize metadata collector.

        Args:
            github_client: Authenticated GitHubClient instance
            data_persistence: Optional DataPersistence instance for storing reports
        """
        self.github_client = github_client
        self.data_persistence = data_persistence

    def collect_weekly_metadata(
        self,
        include_private: bool = True,
        max_repos_per_category: Optional[int] = None,
        commits_limit: int = 50,
        releases_limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Collect metadata for all repositories updated in the last week.

        Args:
            include_private: Whether to include private repositories
            max_repos_per_category: Optional limit on number of repos to process
                                   (for testing or rate limiting)
            commits_limit: Maximum recent commits to fetch per repository
            releases_limit: Maximum releases to fetch per repository

        Returns:
            Dictionary containing collected metadata with structure:
            {
                "collection_date": "2024-01-15T10:30:00",
                "week_start": "2024-01-08T00:00:00",
                "summary": {
                    "total_repos_processed": 10,
                    "new_repositories_count": 2,
                    "updated_repositories_count": 8,
                    "total_stars": 150,
                    "total_forks": 45,
                    "languages": {"Python": 5, "JavaScript": 3, ...},
                    "recent_commits_count": 25,
                    "releases_count": 3
                },
                "new_repositories": [...],
                "updated_repositories": [...]
            }
        """
        # Calculate date range (last 7 days)
        now = datetime.now()
        week_start = now - timedelta(days=7)

        # Get new and updated repositories
        new_repos_data = self.github_client.get_new_repositories(
            since=week_start, include_private=include_private
        )
        updated_repos_data = self.github_client.get_repositories_updated_since(
            since=week_start, include_private=include_private
        )

        # Remove new repos from updated list to avoid duplication
        new_full_names = {repo["full_name"] for repo in new_repos_data}
        truly_updated_repos = [
            repo
            for repo in updated_repos_data
            if repo["full_name"] not in new_full_names
        ]

        # Apply limits if specified
        if max_repos_per_category:
            new_repos_data = new_repos_data[:max_repos_per_category]
            truly_updated_repos = truly_updated_repos[:max_repos_per_category]

        # Get full repository objects for detailed info
        new_repos_full = []
        for repo_stats in new_repos_data:
            try:
                repo_obj = self.github_client.get_repository(repo_stats["full_name"])
                if repo_obj:
                    detailed_info = self.github_client.get_repository_detailed_info(
                        repo_obj,
                        include_commits=True,
                        include_releases=True,
                        include_readme=True,
                        commits_limit=commits_limit,
                        releases_limit=releases_limit,
                    )
                    new_repos_full.append(detailed_info)
            except Exception as e:
                # Log error but continue collecting other repos
                print(f"Error collecting details for {repo_stats['full_name']}: {e}")
                continue

        updated_repos_full = []
        for repo_stats in truly_updated_repos:
            try:
                repo_obj = self.github_client.get_repository(repo_stats["full_name"])
                if repo_obj:
                    detailed_info = self.github_client.get_repository_detailed_info(
                        repo_obj,
                        include_commits=True,
                        include_releases=True,
                        include_readme=True,
                        commits_limit=commits_limit,
                        releases_limit=releases_limit,
                    )
                    updated_repos_full.append(detailed_info)
            except Exception as e:
                print(f"Error collecting details for {repo_stats['full_name']}: {e}")
                continue

        # Calculate summary statistics
        all_repos = new_repos_full + updated_repos_full
        total_stars = sum(repo.get("stars", 0) for repo in all_repos)
        total_forks = sum(repo.get("forks", 0) for repo in all_repos)

        # Count languages
        languages: Dict[str, int] = {}
        for repo in all_repos:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        # Count recent commits and releases
        recent_commits_count = sum(
            len(repo.get("recent_commits", [])) for repo in all_repos
        )
        releases_count = sum(len(repo.get("releases", [])) for repo in all_repos)

        summary = {
            "total_repos_processed": len(all_repos),
            "new_repositories_count": len(new_repos_full),
            "updated_repositories_count": len(updated_repos_full),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "languages": languages,
            "recent_commits_count": recent_commits_count,
            "releases_count": releases_count,
        }

        return {
            "collection_date": now.isoformat(),
            "week_start": week_start.isoformat(),
            "summary": summary,
            "new_repositories": new_repos_full,
            "updated_repositories": updated_repos_full,
        }

    def collect_and_persist(
        self,
        include_private: bool = True,
        max_repos_per_category: Optional[int] = None,
        commits_limit: int = 50,
        releases_limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Collect metadata and persist to database if DataPersistence is configured.

        This is a convenience method that calls collect_weekly_metadata and
        automatically saves the results to the data persistence layer.

        Args:
            include_private: Whether to include private repositories
            max_repos_per_category: Optional limit on number of repos to process
            commits_limit: Maximum recent commits to fetch per repository
            releases_limit: Maximum releases to fetch per repository

        Returns:
            Dictionary containing collected metadata (same as collect_weekly_metadata)

        Raises:
            RuntimeError: If DataPersistence is not configured
        """
        if not self.data_persistence:
            raise RuntimeError(
                "DataPersistence not configured. Set data_persistence in constructor."
            )

        # Collect metadata
        metadata = self.collect_weekly_metadata(
            include_private=include_private,
            max_repos_per_category=max_repos_per_category,
            commits_limit=commits_limit,
            releases_limit=releases_limit,
        )

        # Persist to database
        now = datetime.now()
        week_start = datetime.fromisoformat(metadata["week_start"])
        collection_date = datetime.fromisoformat(metadata["collection_date"])

        self.data_persistence.save_weekly_report(
            week_start=week_start,
            collection_date=collection_date,
            summary=metadata["summary"],
            new_repos=metadata["new_repositories"],
            updated_repos=metadata["updated_repositories"],
        )

        return metadata

    def filter_recent_readme_updates(
        self, repos: List[Dict[str, Any]], since: datetime
    ) -> List[Dict[str, Any]]:
        """
        Filter repositories that have had README updates since a given date.

        Note: This is a simplified implementation that checks repository
        pushed_at date as a proxy for README updates. For more accurate
        detection, you'd need to check commit history for README changes.

        Args:
            repos: List of repository info dictionaries (must include 'pushed_at')
            since: Datetime threshold for updates

        Returns:
            List of repositories with README updates
        """
        repos_with_readme_updates = []

        for repo in repos:
            pushed_at = repo.get("pushed_at")
            if pushed_at:
                pushed_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                if pushed_dt >= since:
                    repos_with_readme_updates.append(repo)

        return repos_with_readme_updates
