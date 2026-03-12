"""Markdown templates for weekly Wiggum Reports."""

from datetime import datetime
from typing import Dict, List, Any


def format_date_range(week_start: datetime, collection_date: datetime) -> str:
    """Format the date range for the report header."""
    end_date = collection_date - timedelta(days=1)
    return f"{week_start.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"


def generate_summary_statistics_section(summary: Dict[str, Any]) -> str:
    """Generate the Summary Statistics section."""
    total_repos = summary.get("total_repos_processed", 0)
    new_count = summary.get("new_repositories_count", 0)
    updated_count = summary.get("updated_repositories_count", 0)
    total_stars = summary.get("total_stars", 0)
    total_forks = summary.get("total_forks", 0)
    languages = summary.get("languages", {})
    commits_count = summary.get("recent_commits_count", 0)
    releases_count = summary.get("releases_count", 0)

    # Sort languages by count
    sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)

    markdown = "## 📊 Summary Statistics\n\n"
    markdown += "| Metric | Count |\n"
    markdown += "|--------|-------|\n"
    markdown += f"| Total Repositories | {total_repos} |\n"
    markdown += f"| New Repositories | 🆕 {new_count} |\n"
    markdown += f"| Updated Repositories | 🔄 {updated_count} |\n"
    markdown += f"| Total Stars | ⭐ {total_stars} |\n"
    markdown += f"| Total Forks | 🍴 {total_forks} |\n"
    markdown += f"| Recent Commits | 💻 {commits_count} |\n"
    markdown += f"| Releases | 📦 {releases_count} |\n"

    if sorted_languages:
        markdown += "\n### Languages Used\n\n"
        markdown += "| Language | Repository Count |\n"
        markdown += "|----------|------------------|\n"
        for lang, count in sorted_languages[:10]:  # Top 10
            markdown += f"| {lang} | {count} |\n"

    return markdown


def generate_repository_card(
    repo: Dict[str, Any], show_description: bool = True
) -> str:
    """Generate a formatted card for a single repository."""
    name = repo.get("name", "Unknown")
    full_name = repo.get("full_name", "Unknown")
    description = repo.get("description", "")
    url = repo.get("html_url", "#")
    stars = repo.get("stars", 0)
    forks = repo.get("forks", 0)
    language = repo.get("language", "None")
    created_at = repo.get("created_at", "")
    updated_at = repo.get("updated_at", "")

    card = f"### [{full_name}]({url})\n\n"

    if show_description and description:
        card += f"> {description}\n\n"

    card += "**Stats:** "
    card += f"⭐ {stars} | 🍴 {forks}"

    if language:
        card += f" | 💻 {language}"

    card += "\n\n"

    # Show latest commits if available
    recent_commits = repo.get("recent_commits", [])
    if recent_commits:
        card += "**Recent Commits:**\n"
        for commit in recent_commits[:3]:  # Show top 3
            commit_msg = commit.get("commit", {}).get("message", "No message")
            commit_author = (
                commit.get("commit", {}).get("author", {}).get("name", "Unknown")
            )
            commit_date = commit.get("commit", {}).get("author", {}).get("date", "")
            if commit_date:
                try:
                    dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                    date_str = dt.strftime("%m-%d")
                except:
                    date_str = commit_date[:10]
            else:
                date_str = ""

            # Truncate long commit messages
            if len(commit_msg) > 60:
                commit_msg = commit_msg[:57] + "..."

            card += f"- `{commit_msg}` - *{commit_author}* ({date_str})\n"
        card += "\n"

    # Show releases if available
    releases = repo.get("releases", [])
    if releases:
        card += "**Recent Releases:**\n"
        for release in releases[:2]:  # Show top 2
            tag = release.get("tag_name", "Unknown")
            name = release.get("name", tag)
            published_at = release.get("published_at", "")
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    date_str = dt.strftime("%m-%d")
                except:
                    date_str = published_at[:10]
            else:
                date_str = ""

            card += f"- v{tag} (*{name}*) - {date_str}\n"
        card += "\n"

    return card


def generate_new_repositories_section(new_repos: List[Dict[str, Any]]) -> str:
    """Generate the New Repositories section."""
    markdown = "## 🆕 New Repositories\n\n"

    if not new_repos:
        markdown += "*No new repositories this week.*\n\n"
        return markdown

    markdown += f"Found **{len(new_repos)}** new repository"
    if len(new_repos) != 1:
        markdown += "ies"
    markdown += ":\n\n"

    for repo in new_repos:
        markdown += generate_repository_card(repo)
        markdown += "---\n\n"

    return markdown


def generate_notable_updates_section(updated_repos: List[Dict[str, Any]]) -> str:
    """Generate the Notable Updates section with most starred or active repos."""
    markdown = "## 🔄 Notable Updates\n\n"

    if not updated_repos:
        markdown += "*No significant updates this week.*\n\n"
        return markdown

    # Sort by stars (descending) to show most popular first
    sorted_repos = sorted(updated_repos, key=lambda x: x.get("stars", 0), reverse=True)

    # Limit to top repos (configurable, showing top 10)
    top_repos = sorted_repos[:10]
    markdown += (
        f"Showing top **{len(top_repos)}** most starred updated repositories:\n\n"
    )

    for repo in top_repos:
        markdown += generate_repository_card(repo, show_description=True)
        markdown += "---\n\n"

    return markdown


def generate_trending_repos_section(
    new_repos: List[Dict[str, Any]], updated_repos: List[Dict[str, Any]], limit: int = 5
) -> str:
    """Generate the Trending Repos section based on star velocity."""
    markdown = "## 📈 Trending Repositories\n\n"

    all_repos = new_repos + updated_repos

    if not all_repos:
        markdown += "*No trending data available.*\n\n"
        return markdown

    # Simple trending metric: repos with high star-to-age ratio
    # For new repos, use stars directly; for existing repos, use recent star gain approximation
    trending_scores = []
    for repo in all_repos:
        stars = repo.get("stars", 0)
        created_at = repo.get("created_at", "")
        updated_at = repo.get("updated_at", "")

        # Calculate simple score: stars weighted by recency
        score = stars

        # Boost new repos slightly
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            days_old = (datetime.now() - created_dt).days
            if days_old < 30:
                score = stars * 1.5  # Boost new repos
        except:
            pass

        trending_scores.append((score, repo))

    # Sort by score descending
    trending_scores.sort(key=lambda x: x[0], reverse=True)
    trending_repos = [repo for _, repo in trending_scores[:limit]]

    markdown += f"Top **{len(trending_repos)}** trending repositories this week:\n\n"

    for repo in trending_repos:
        markdown += generate_repository_card(repo, show_description=True)
        markdown += "---\n\n"

    return markdown


def generate_call_to_action_section() -> str:
    """Generate the Call-to-Action section."""
    markdown = "## 🚀 Call to Action\n\n"
    markdown += "Check out these awesome repositories and get involved!\n\n"
    markdown += "- **Star** repos you find interesting\n"
    markdown += "- **Fork** and contribute to projects\n"
    markdown += "- **Share** this report to spread the word\n"
    markdown += "- **Follow** me on GitHub for more updates\n\n"
    markdown += "Got questions or want to collaborate? Feel free to reach out!\n\n"
    markdown += "---\n\n"
    markdown += "*This report was automatically generated by **Wiggum Report**. "
    markdown += (
        "See the [source code](https://github.com/yourusername/wiggum-report).*\n"
    )

    return markdown


def generate_full_report(metadata: Dict[str, Any]) -> str:
    """
    Generate a complete weekly markdown report from collected metadata.

    Args:
        metadata: Dictionary from MetadataCollector.collect_weekly_metadata()

    Returns:
        Complete markdown report as a string
    """
    collection_date_str = metadata.get("collection_date", "")
    week_start_str = metadata.get("week_start", "")

    try:
        collection_date = datetime.fromisoformat(
            collection_date_str.replace("Z", "+00:00")
        )
        week_start = datetime.fromisoformat(week_start_str.replace("Z", "+00:00"))
    except:
        collection_date = datetime.now()
        week_start = collection_date - timedelta(days=7)

    summary = metadata.get("summary", {})
    new_repos = metadata.get("new_repositories", [])
    updated_repos = metadata.get("updated_repositories", [])

    # Build the complete report
    report = ""

    # Header
    report += f"# 📰 Wiggum Weekly Report\n\n"
    report += f"**{format_date_range(week_start, collection_date)}**\n\n"
    report += "---\n\n"

    # Sections in order
    report += generate_summary_statistics_section(summary)
    report += "\n"
    report += generate_new_repositories_section(new_repos)
    report += generate_notable_updates_section(updated_repos)
    report += generate_trending_repos_section(new_repos, updated_repos)
    report += generate_call_to_action_section()

    return report


def generate_social_media_summary(metadata: Dict[str, Any], platform: str = "x") -> str:
    """
    Generate a short summary suitable for social media platforms.

    Args:
        metadata: Dictionary from MetadataCollector.collect_weekly_metadata()
        platform: 'x' (280 chars) or 'linkedin' (longer but still concise)

    Returns:
        Short summary text optimized for the platform
    """
    summary = metadata.get("summary", {})
    total_repos = summary.get("total_repos_processed", 0)
    new_count = summary.get("new_repositories_count", 0)
    updated_count = summary.get("updated_repositories_count", 0)
    total_stars = summary.get("total_stars", 0)

    new_repos = metadata.get("new_repositories", [])
    # Get names of first few new repos
    new_repo_names = []
    for repo in new_repos[:3]:
        name = repo.get("name", "")
        if name:
            new_repo_names.append(name)

    if platform == "x":
        # X/Twitter: 280 characters, use hashtags
        text = f"🧵 Weekly GitHub roundup!\n\n"
        text += f"📊 {total_repos} repos • {new_count} new • {updated_count} updated • ⭐ {total_stars} total stars\n\n"

        if new_repo_names:
            text += "🆕 New: "
            text += ", ".join([f"`{name}`" for name in new_repo_names])
            if len(new_repos) > 3:
                text += f" +{len(new_repos) - 3} more"
            text += "\n\n"

        text += "#WiggumReport #GitHub #OpenSource"
        return text[:280]  # Ensure it fits

    else:  # LinkedIn
        # LinkedIn: longer but still professional
        text = f"📢 Weekly GitHub Activity Update\n\n"
        text += f"Summary for the past week:\n"
        text += f"• Total repositories: {total_repos}\n"
        text += f"• New repositories: {new_count}\n"
        text += f"• Updated repositories: {updated_count}\n"
        text += f"• Total stars earned: ⭐ {total_stars}\n"

        if new_repo_names:
            text += f"\n🆕 New repositories this week:\n"
            for name in new_repo_names:
                text += f"• {name}\n"
            if len(new_repos) > 3:
                text += f"• ...and {len(new_repos) - 3} more\n"

        text += "\n#OpenSource #GitHub #WiggumReport #SoftwareDevelopment"
        return text
