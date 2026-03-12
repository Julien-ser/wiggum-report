"""X (Twitter) social media platform adapter."""

from typing import Dict, Any
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
            metadata: Dictionary from
                MetadataCollector.collect_weekly_metadata()

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

        # Build body content (without hashtags)
        parts = []

        # Header with emoji
        parts.append("🧵 Weekly GitHub roundup!\n")

        # Summary line
        summary_line = (
            f"📊 {total_repos} repos • {new_count} new • "
            f"{updated_count} updated • ⭐ {total_stars} stars"
        )
        parts.append(summary_line + "\n")

        # New repositories (top 3) with shortened links
        if new_repos:
            parts.append("🆕 New repos: ")
            repo_entries = []
            for repo in new_repos[:3]:
                name = repo.get("name", "")
                url = repo.get("html_url", "")
                if name:
                    short_url = self._shorten_url(url)
                    if short_url:
                        entry = f"`{name}`({short_url})"
                    else:
                        entry = f"`{name}`"
                    repo_entries.append(entry)
            parts.append(", ".join(repo_entries))

            if len(new_repos) > 3:
                parts.append(f" +{len(new_repos) - 3} more")
            parts.append("\n")

        # Trending updated repos (top 2 by stars) with shortened links
        if updated_repos and len(updated_repos) > 0:
            sorted_updated = sorted(
                updated_repos, key=lambda x: x.get("stars", 0), reverse=True
            )
            if sorted_updated:
                parts.append("🔥 Top updated: ")
                trending_entries = []
                for repo in sorted_updated[:2]:
                    name = repo.get("name", "")
                    url = repo.get("html_url", "")
                    if name:
                        short_url = self._shorten_url(url)
                        if short_url:
                            entry = f"`{name}`({short_url})"
                        else:
                            entry = f"`{name}`"
                        trending_entries.append(entry)
                parts.append(", ".join(trending_entries))
                if len(sorted_updated) > 2:
                    parts.append(f" +{len(sorted_updated) - 2} more")
                parts.append("\n")

        body = "".join(parts).rstrip()
        hashtags = "#WiggumReport #GitHub #OpenSource"

        total_length = len(body) + 1 + len(hashtags)
        if total_length > self.max_length:
            max_body_len = self.max_length - len(hashtags) - 1
            body = self._truncate_body(body, max_body_len)

        return body + "\n" + hashtags

    def _shorten_url(self, url: str) -> str:
        """
        Shorten a URL for inclusion in tweets.

        Currently strips protocol (https://) for brevity.
        Could be extended to use URL shorteners like bit.ly.

        Args:
            url: Full URL to shorten

        Returns:
            Shortened URL string
        """
        if not url:
            return ""
        # Strip protocol for brevity
        url = url.replace("https://", "").replace("http://", "")
        return url

    def _truncate_body(self, body: str, max_len: int) -> str:
        """
        Truncate body content to max_len, trying to preserve structure.

        Args:
            body: Body text to truncate
            max_len: Maximum allowed length

        Returns:
            Truncated body string
        """
        if len(body) <= max_len:
            return body

        truncated = body[:max_len]
        last_newline = truncated.rfind("\n")
        if last_newline > 0 and last_newline >= max_len * 0.5:
            return truncated[:last_newline].rstrip()
        else:
            return body[: max_len - 3].rstrip() + "..."
