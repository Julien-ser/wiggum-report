"""LinkedIn social media platform adapter."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from .adapter import SocialMediaAdapter


class LinkedInAdapter(SocialMediaAdapter):
    """Adapter for LinkedIn platform with professional format."""

    def __init__(self, max_length: int = 3000):
        """
        Initialize LinkedIn adapter.

        Args:
            max_length: Maximum character length (LinkedIn allows ~3000 chars for posts)
        """
        self._max_length = max_length

    @property
    def platform_name(self) -> str:
        """Return platform name."""
        return "linkedin"

    @property
    def max_length(self) -> int:
        """Return maximum character length."""
        return self._max_length

    def format(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata into a LinkedIn post.

        Args:
            metadata: Dictionary from MetadataCollector.collect_weekly_metadata()

        Returns:
            Formatted LinkedIn post text
        """
        summary = metadata.get("summary", {})
        collection_date = metadata.get("collection_date", "")
        week_start = metadata.get("week_start", "")

        # Format date range
        date_range = self._format_date_range(week_start, collection_date)

        total_repos = summary.get("total_repos_processed", 0)
        new_count = summary.get("new_repositories_count", 0)
        updated_count = summary.get("updated_repositories_count", 0)
        total_stars = summary.get("total_stars", 0)
        total_forks = summary.get("total_forks", 0)
        languages = summary.get("languages", {})

        new_repos = metadata.get("new_repositories", [])
        updated_repos = metadata.get("updated_repositories", [])

        # Build LinkedIn post
        parts = []

        # Header
        parts.append(f"📢 Weekly GitHub Activity Update\n")
        parts.append(f"**Period**: {date_range}\n")

        # Summary section
        parts.append("### Summary\n\n")
        parts.append(f"• Total repositories processed: {total_repos}\n")
        parts.append(f"• New repositories: {new_count}\n")
        parts.append(f"• Updated repositories: {updated_count}\n")
        parts.append(f"• Total stars earned: ⭐ {total_stars}\n")
        parts.append(f"• Total forks: 🍴 {total_forks}\n")

        # Languages section (if available)
        if languages:
            parts.append("\n### Languages Used\n\n")
            sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
            for lang, count in sorted_langs[:5]:
                parts.append(f"• {lang}: {count} repositories\n")

        # New repositories section
        if new_repos:
            parts.append("\n### 🆕 New Repositories\n\n")
            for i, repo in enumerate(new_repos[:5], 1):
                name = repo.get("full_name", repo.get("name", "Unknown"))
                url = repo.get("html_url", "#")
                description = repo.get("description", "")
                stars = repo.get("stars", 0)
                language = repo.get("language", "")

                parts.append(f"{i}. **[{name}]({url})**\n")
                if description:
                    parts.append(f"   > {description}\n")
                parts.append(f"   ⭐ {stars} stars")
                if language:
                    parts.append(f" | 💻 {language}")
                parts.append("\n\n")

            if len(new_repos) > 5:
                parts.append(
                    f"_...and {len(new_repos) - 5} more new repositories._\n\n"
                )

        # Notable updates section
        if updated_repos:
            # Sort by stars to show most popular
            sorted_updated = sorted(
                updated_repos, key=lambda x: x.get("stars", 0), reverse=True
            )
            top_updated = sorted_updated[:5]

            parts.append("### 🔄 Notable Updates\n\n")
            for i, repo in enumerate(top_updated, 1):
                name = repo.get("full_name", repo.get("name", "Unknown"))
                url = repo.get("html_url", "#")
                description = repo.get("description", "")
                stars = repo.get("stars", 0)
                recent_commits = repo.get("recent_commits", [])

                parts.append(f"{i}. **[{name}]({url})**\n")
                if description:
                    parts.append(f"   > {description}\n")
                parts.append(f"   ⭐ {stars} stars")

                if recent_commits:
                    parts.append(f"\n   Recent activity: {len(recent_commits)} commits")
                    # Show most recent commit message
                    if recent_commits[0].get("message"):
                        msg = recent_commits[0]["message"][:100]
                        if len(recent_commits[0]["message"]) > 100:
                            msg += "..."
                        parts.append(f"\n   Latest: `{msg}`")
                parts.append("\n\n")

            if len(updated_repos) > 5:
                parts.append(
                    f"_...and {len(updated_repos) - 5} more updated repositories._\n\n"
                )

        # Call to action
        parts.append("### 🚀 Call to Action\n\n")
        parts.append(
            "Explore these repositories and consider contributing to open source! "
        )
        parts.append("Your contributions help drive innovation in our community.\n\n")
        parts.append("---\n\n")
        parts.append(
            "*This weekly update is automatically generated by **Wiggum Report**. "
        )
        parts.append(
            "[Check out the project](https://github.com/yourusername/wiggum-report)*\n\n"
        )
        parts.append("#OpenSource #GitHub #SoftwareDevelopment #WiggumReport")

        # Join and ensure within limit
        post = "".join(parts)

        if len(post) > self.max_length:
            post = self._truncate_for_linkedin(post)

        return post[: self.max_length]

    def _format_date_range(self, week_start: str, collection_date: str) -> str:
        """Format the date range for the post."""
        try:
            start = datetime.fromisoformat(week_start.replace("Z", "+00:00"))
            end = datetime.fromisoformat(collection_date.replace("Z", "+00:00"))
            end = end - timedelta(days=1)  # Collection is day after week ends
            return f"{start.strftime('%B %d, %Y')} - {end.strftime('%B %d, %Y')}"
        except:
            return "Last 7 days"

    def _truncate_for_linkedin(self, content: str) -> str:
        """
        Truncate content to fit LinkedIn's limit while preserving structure.

        Args:
            content: Full post content

        Returns:
            Truncated content within limit
        """
        if len(content) <= self.max_length:
            return content

        # Strategy: preserve first sections, truncate repository lists
        sections = content.split("###")

        # Always keep header and summary
        if len(sections) <= 2:
            return content[: self.max_length - 100] + "\n\n*(post truncated)*"

        header_and_summary = sections[0] + "###" + sections[1]

        # Calculate remaining space
        remaining = self.max_length - len(header_and_summary) - 100

        if remaining <= 0:
            # Even header+summary is too long, truncate it
            return content[: self.max_length - 100] + "\n\n*(post truncated)*"

        # Keep first few repos from new and updated sections, truncate rest
        new_repos_section = ""
        updated_repos_section = ""

        # Find new repos section
        for section in sections[2:]:
            if "New Repositories" in section:
                new_repos_section = "###" + section
                break

        # Find notable updates section
        for section in sections[2:]:
            if "Notable Updates" in section:
                updated_repos_section = "###" + section
                break

        cta_and_hashtags = ""
        # Find CTA and hashtags
        for section in sections:
            if "Call to Action" in section:
                cta_and_hashtags = "###" + section
                break

        # Reconstruct limited version
        result = header_and_summary + "\n\n"

        if new_repos_section:
            result += self._limit_repo_list(new_repos_section, remaining // 2) + "\n\n"
        if updated_repos_section:
            result += (
                self._limit_repo_list(updated_repos_section, remaining // 2) + "\n\n"
            )
        if cta_and_hashtags:
            result += cta_and_hashtags

        return result[: self.max_length]

    def _limit_repo_list(self, section: str, max_chars: int) -> str:
        """Limit a repository list section to max_chars."""
        if len(section) <= max_chars:
            return section

        # Split by lines and keep header, then as many repos as fit
        lines = section.split("\n")
        header = ""
        repos_lines = []
        in_repo = False

        for line in lines:
            if line.strip().startswith("###"):
                header = line + "\n"
            elif line.strip().startswith(
                ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")
            ):
                repos_lines.append(line)
                in_repo = True
            elif in_repo and line.strip().startswith(("_...", "...", "and ")):
                repos_lines.append(line)
            elif in_repo and not line.strip():
                repos_lines.append(line)

        result = header
        used_chars = len(header)

        for line in repos_lines:
            if used_chars + len(line) + 1 <= max_chars:
                result += line + "\n"
                used_chars += len(line) + 1
            else:
                result += f"_...and more repositories truncated for length._\n"
                break

        return result
