"""GitHub API client for interacting with GitHub using PyGithub."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from github import Github, GithubException, Repository as PyGithubRepository
from src.config.settings import Settings


class GitHubClient:
    """Client for GitHub API operations using PyGithub."""

    def __init__(self, token: str):
        """
        Initialize GitHub client with authentication token.

        Args:
            token: GitHub Personal Access Token
        """
        self.token = token
        self.github = Github(token)

    def get_authenticated_user(self) -> Dict[str, Any]:
        """
        Get the authenticated user's information.

        Returns:
            Dictionary with user details (login, name, email, etc.)

        Raises:
            GithubException: If authentication fails
        """
        try:
            user = self.github.get_user()
            return {
                "login": user.login,
                "name": user.name,
                "email": user.email,
                "html_url": user.html_url,
                "avatar_url": user.avatar_url,
                "public_repos": user.public_repos,
                "total_private_repos": user.total_private_repos
                if user.type == "User"
                else None,
            }
        except GithubException as e:
            raise GithubException(f"Failed to authenticate: {e}")

    def get_repositories(
        self, include_private: bool = True
    ) -> List[PyGithubRepository.Repository]:
        """
        Fetch all repositories for the authenticated user.

        Args:
            include_private: Whether to include private repositories (default: True)

        Returns:
            List of PyGithub Repository objects
        """
        try:
            user = self.github.get_user()
            repos = user.get_repos()
            if not include_private:
                repos = [repo for repo in repos if not repo.private]
            return list(repos)
        except GithubException as e:
            raise GithubException(f"Failed to fetch repositories: {e}")

    def get_repository(self, full_name: str) -> Optional[PyGithubRepository.Repository]:
        """
        Get a specific repository by its full name (owner/repo).

        Args:
            full_name: Repository full name (e.g., "owner/repository")

        Returns:
            Repository object or None if not found
        """
        try:
            return self.github.get_repo(full_name)
        except GithubException:
            return None

    def get_repository_stats(
        self, repo: PyGithubRepository.Repository
    ) -> Dict[str, Any]:
        """
        Extract key statistics from a repository.

        Args:
            repo: PyGithub Repository object

        Returns:
            Dictionary with repository statistics
        """
        try:
            # Get commit count (may require additional API calls, approximate via default branch)
            commit_count = None
            try:
                if repo.default_branch:
                    commits = repo.get_commits(sha=repo.default_branch)
                    commit_count = commits.totalCount
            except:
                pass

            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "html_url": repo.html_url,
                "private": repo.private,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "topics": repo.get_topics() if hasattr(repo, "get_topics") else [],
                "size_kb": repo.size,
                "commit_count": commit_count,
                "has_wiki": repo.has_wiki,
                "has_pages": repo.has_pages,
                "is_archived": repo.archived,
                "is_disabled": repo.disabled,
            }
        except GithubException as e:
            raise GithubException(f"Failed to get stats for {repo.full_name}: {e}")

    def get_recent_commits(
        self,
        repo: PyGithubRepository.Repository,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get recent commits from a repository.

        Args:
            repo: PyGithub Repository object
            since: Only get commits after this datetime (default: None)
            limit: Maximum number of commits to return (default: 100)

        Returns:
            List of commit information dictionaries
        """
        try:
            commits = []
            try:
                commit_iter = repo.get_commits()
                if since:
                    commit_iter = commit_iter.since(since)

                for i, commit in enumerate(commit_iter):
                    if i >= limit:
                        break
                    commits.append(
                        {
                            "sha": commit.sha[:8],
                            "message": commit.commit.message,
                            "author": commit.commit.author.name
                            if commit.commit.author
                            else None,
                            "email": commit.commit.author.email
                            if commit.commit.author
                            else None,
                            "date": commit.commit.author.date.isoformat()
                            if commit.commit.author and commit.commit.author.date
                            else None,
                            "url": commit.html_url,
                        }
                    )
            except GithubException as e:
                if "Git Repository is empty" not in str(e):
                    raise

            return commits
        except Exception as e:
            raise GithubException(f"Failed to get commits for {repo.full_name}: {e}")

    def get_releases(
        self, repo: PyGithubRepository.Repository, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent releases from a repository.

        Args:
            repo: PyGithub Repository object
            limit: Maximum number of releases to return (default: 10)

        Returns:
            List of release information dictionaries
        """
        try:
            releases = []
            try:
                for release in repo.get_releases()[:limit]:
                    releases.append(
                        {
                            "tag_name": release.tag_name,
                            "name": release.name,
                            "body": release.body,
                            "draft": release.draft,
                            "prerelease": release.prerelease,
                            "created_at": release.created_at.isoformat()
                            if release.created_at
                            else None,
                            "published_at": release.published_at.isoformat()
                            if release.published_at
                            else None,
                            "html_url": release.html_url,
                            "assets_count": len(list(release.get_assets())),
                        }
                    )
            except GithubException as e:
                if "Git Repository is empty" not in str(e):
                    raise

            return releases
        except Exception as e:
            raise GithubException(f"Failed to get releases for {repo.full_name}: {e}")

    def get_readme(
        self, repo: PyGithubRepository.Repository
    ) -> Optional[Dict[str, Any]]:
        """
        Get repository README content and metadata.

        Args:
            repo: PyGithub Repository object

        Returns:
            Dictionary with README content and metadata, or None if not found
        """
        try:
            readme = repo.get_readme()
            return {
                "path": readme.path,
                "sha": readme.sha,
                "content": readme.decoded_content.decode("utf-8"),
                "size": readme.size,
                "download_url": readme.download_url,
            }
        except GithubException:
            # No README found
            return None

    def get_repositories_updated_since(
        self, since: datetime, include_private: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get repositories that have been updated since a specific date.

        Args:
            since: Datetime threshold for updates
            include_private: Whether to include private repositories

        Returns:
            List of repository info dictionaries
        """
        try:
            repos = self.get_repositories(include_private=include_private)
            updated_repos = []

            for repo in repos:
                # Check updated_at timestamp
                if repo.updated_at and repo.updated_at >= since:
                    stats = self.get_repository_stats(repo)
                    updated_repos.append(stats)

            return updated_repos
        except GithubException as e:
            raise GithubException(f"Failed to fetch updated repositories: {e}")

    def get_new_repositories(
        self, since: datetime, include_private: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get repositories created since a specific date.

        Args:
            since: Datetime threshold for creation
            include_private: Whether to include private repositories

        Returns:
            List of repository info dictionaries for newly created repos
        """
        try:
            repos = self.get_repositories(include_private=include_private)
            new_repos = []

            for repo in repos:
                # Check created_at timestamp
                if repo.created_at and repo.created_at >= since:
                    stats = self.get_repository_stats(repo)
                    new_repos.append(stats)

            return new_repos
        except GithubException as e:
            raise GithubException(f"Failed to fetch new repositories: {e}")

    def get_repository_detailed_info(
        self,
        repo: PyGithubRepository.Repository,
        include_commits: bool = True,
        include_releases: bool = True,
        include_readme: bool = True,
        commits_limit: int = 50,
        releases_limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get comprehensive information about a repository.

        Args:
            repo: PyGithub Repository object
            include_commits: Whether to fetch recent commits
            include_releases: Whether to fetch releases
            include_readme: Whether to fetch README
            commits_limit: Max recent commits to fetch
            releases_limit: Max releases to fetch

        Returns:
            Complete repository information dictionary
        """
        info = self.get_repository_stats(repo)

        if include_commits:
            info["recent_commits"] = self.get_recent_commits(repo, limit=commits_limit)

        if include_releases:
            info["releases"] = self.get_releases(repo, limit=releases_limit)

        if include_readme:
            info["readme"] = self.get_readme(repo)

        return info

    def close(self):
        """Close the GitHub client connection."""
        self.github.close()

    @classmethod
    def from_settings(cls, settings: Settings) -> "GitHubClient":
        """
        Create a GitHubClient from Settings object.

        Args:
            settings: Settings instance with GitHub token

        Returns:
            GitHubClient instance
        """
        return cls(token=settings.github_token)
