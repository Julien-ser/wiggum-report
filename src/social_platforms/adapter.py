"""Social media platform adapters for formatting GitHub reports."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class SocialMediaAdapter(ABC):
    """Abstract base class for social media platform adapters."""

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
