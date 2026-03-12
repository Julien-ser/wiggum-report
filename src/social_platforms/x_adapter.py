"""X (Twitter) social media platform adapter."""

from typing import Dict, Any, List
from .adapter import SocialMediaAdapter


class XAdapter(SocialMediaAdapter):
    """Adapter for X (Twitter) platform with 280 character limit."""

    def __init__(self, max_length: int = 280):
        """
        Initialize X adapter.

        Args:
            max_length: Maximum character length (default 280 for X)
        """
        self._max_length = max_length

    @property
    def platform_name(self) -> str:
        """Return platform name."""
        return "x"

    @property
    def max_length(self) -> int:
        """Return maximum character length."""
        return self._max_length

    def format(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata into a tweet.

        Args:
            metadata: Dictionary from MetadataCollector.collect_weekly_metadata()

        Returns:
            Formatted tweet text (max 280 chars)
        """
        summary = metadata.get("summary", {})
        total_repos = summary.get("total_repos_processed", 0)
        new_count = summary.get("new_repositories_count", 0)
        updated_count = summary.get("updated_repositories_count", 0)
        total_stars = summary.get("total_stars", 0)

        new_repos = metadata.get("new_repositories", [])
        updated_repos = metadata.get("updated_repositories", [])

        # Start building tweet
        parts = []

        # Header with emoji
        parts.append("🧵 Weekly GitHub roundup!\n")

        # Summary line
        summary_line = f"📊 {total_repos} repos • {new_count} new • {updated_count} updated • ⭐ {total_stars} stars"
        parts.append(summary_line + "\n")

        # New repositories (top 3)
        if new_repos:
            parts.append("🆕 New repos: ")
            repo_names = []
            for repo in new_repos[:3]:
                name = repo.get("name", "")
                if name:
                    repo_names.append(f"`{name}`")
            parts.append(", ".join(repo_names))

            if len(new_repos) > 3:
                parts.append(f" +{len(new_repos) - 3} more")
            parts.append("\n")

        # Trending updated repos (top 2 by stars)
        if updated_repos and len(updated_repos) > 0:
            sorted_updated = sorted(
                updated_repos, key=lambda x: x.get("stars", 0), reverse=True
            )
            if sorted_updated:
                parts.append("🔥 Top updated: ")
                trending_names = []
                for repo in sorted_updated[:2]:
                    name = repo.get("name", "")
                    if name:
                        trending_names.append(f"`{name}`")
                parts.append(", ".join(trending_names))
                if len(sorted_updated) > 2:
                    parts.append(f" +{len(sorted_updated) - 2} more")
                parts.append("\n")

        # Hashtags
        parts.append("#WiggumReport #GitHub #OpenSource")

        # Join and ensure within limit
        tweet = "".join(parts)

        # If still too long, truncate summary line
        if len(tweet) > self.max_length:
            tweet = self._truncate_content(tweet)

        return tweet[: self.max_length]

    def _truncate_content(self, content: str) -> str:
        """
        Truncate content to fit within max_length, preserving hashtags.

        Args:
            content: Full content to truncate

        Returns:
            Truncated content
        """
        hashtags = "#WiggumReport #GitHub #OpenSource"
        max_content = self.max_length - len(hashtags) - 1  # -1 for space/newline

        if len(content) > max_content:
            # Try to preserve the header and truncate the middle
            lines = content.split("\n")
            header = lines[0] if lines else ""  # Keep header line
            rest = "\n".join(lines[1:-1]) if len(lines) > 2 else ""

            if len(header) + len(rest) > max_content:
                # Need to truncate rest significantly
                rest = rest[: max_content - len(header) - 3] + "..."
                content = header + "\n" + rest + "\n" + hashtags
            else:
                content = header + "\n" + rest + "\n" + hashtags
        else:
            content = content + "\n" + hashtags

        return content[: self.max_length]
