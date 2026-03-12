"""Social media platform adapters for formatting and posting GitHub reports."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class SocialMediaAdapter(ABC):
    """Abstract base class for social media platform adapters."""

    def __init__(self, logger=None):
        """
        Initialize adapter with optional logger.

        Args:
            logger: Logger instance for logging posting activities
        """
        self.logger = logger or logging.getLogger(__name__)

    @abstractmethod
    def format(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata into platform-specific post text.

        Args:
            metadata: Dictionary from MetadataCollector.collect_weekly_metadata()

        Returns:
            Formatted string suitable for the platform
        """
        pass

    @abstractmethod
    def post(self, text: str) -> bool:
        """
        Post formatted text to the social media platform.

        Args:
            text: The formatted post text to publish

        Returns:
            True if posting succeeded, False otherwise
        """
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name (e.g., 'x', 'linkedin')."""
        pass

    @property
    @abstractmethod
    def max_length(self) -> int:
        """Return the maximum character length for this platform."""
        pass
