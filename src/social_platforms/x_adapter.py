"""X (Twitter) social media platform adapter."""

import time
from typing import Dict, Any
import tweepy
from tweepy.errors import TweepyException, TooManyRequests, Unauthorized, Forbidden
from .adapter import SocialMediaAdapter
from src.content_optimizer import ContentOptimizer


class XAdapter(SocialMediaAdapter):
    """Adapter for X (Twitter) platform with 280 character limit."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        max_length: int = 280,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
    ):
        """
        Initialize X adapter with API credentials.

        Args:
            api_key: X API key
            api_secret: X API secret
            access_token: X access token
            access_token_secret: X access token secret
            max_length: Maximum character length (default 280 for X)
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            max_backoff: Maximum backoff time in seconds
        """
        self._max_length = max_length
        self._optimizer = ContentOptimizer()
        self._max_retries = max_retries
        self._initial_backoff = initial_backoff
        self._max_backoff = max_backoff

        # Initialize Tweepy client with OAuth 1.0a user context
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=False,  # We handle rate limits manually
        )

        # Verify credentials on initialization
        self._verify_credentials()

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
            result = self._optimizer.optimize(body, max_body_len, platform="x")
            body = result.optimized_text

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

    def _verify_credentials(self) -> None:
        """
        Verify X API credentials are valid.

        Raises:
            Unauthorized: If credentials are invalid
            TweepyException: If verification fails for other reasons
        """
        try:
            # Get own user info to verify credentials
            response = self.client.get_me()
            if response.data:
                self.logger.info(
                    f"X API credentials verified for user: @{response.data.username}"
                )
            else:
                raise Unauthorized("Invalid X API credentials")
        except Unauthorized:
            raise
        except Exception as e:
            raise TweepyException(f"Failed to verify X credentials: {e}")

    def post(self, text: str) -> bool:
        """
        Post text to X (Twitter) with retry logic and rate limit handling.

        Args:
            text: The tweet text to post

        Returns:
            True if posting succeeded, False otherwise
        """
        for attempt in range(1, self._max_retries + 1):
            try:
                self.logger.info(
                    f"Posting to X (attempt {attempt}/{self._max_retries})"
                )
                response = self.client.create_tweet(text=text)

                if response.data:
                    tweet_id = response.data.get("id", "unknown")
                    self.logger.info(f"Successfully posted to X: tweet_id={tweet_id}")
                    return True
                else:
                    self.logger.error("X API returned no data after posting")
                    return False

            except TooManyRequests as e:
                # Check rate limit headers if available
                reset_time = getattr(e.response, "headers", {}).get(
                    "x-rate-limit-reset"
                )
                if reset_time:
                    wait_seconds = int(reset_time) - int(time.time())
                    wait_seconds = max(1, wait_seconds)
                else:
                    # Exponential backoff
                    wait_seconds = min(
                        self._initial_backoff * (2 ** (attempt - 1)), self._max_backoff
                    )

                self.logger.warning(
                    f"Rate limit hit. Waiting {wait_seconds:.1f}s before retry..."
                )
                time.sleep(wait_seconds)

            except Unauthorized as e:
                self.logger.error(f"X authentication failed: {e}")
                return False
            except Forbidden as e:
                self.logger.error(f"X posting forbidden: {e}")
                return False
            except TweepyException as e:
                if attempt < self._max_retries:
                    wait_seconds = min(
                        self._initial_backoff * (2 ** (attempt - 1)), self._max_backoff
                    )
                    self.logger.warning(
                        f"Tweepy error: {e}. Retrying in {wait_seconds:.1f}s..."
                    )
                    time.sleep(wait_seconds)
                else:
                    self.logger.error(f"Max retries exceeded for X: {e}")
                    return False
            except Exception as e:
                self.logger.error(f"Unexpected error posting to X: {e}", exc_info=True)
                return False

        self.logger.error("All retry attempts exhausted for X")
        return False
