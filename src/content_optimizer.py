"""Content optimizer for truncating and summarizing text to fit platform constraints."""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """Result of content optimization."""

    optimized_text: str
    original_length: int
    optimized_length: int
    method: str  # 'truncated', 'summarized', or 'unchanged'


class ContentOptimizer:
    """
    Optimizes content to fit within character limits while preserving key information.

    Features:
    - Intelligent truncation at sentence boundaries
    - Extractive summarization for longer texts
    - Preservation of important keywords and phrases
    """

    def __init__(self, preserve_keywords: Optional[List[str]] = None):
        """
        Initialize optimizer.

        Args:
            preserve_keywords: List of keywords to prioritize when truncating
        """
        self.preserve_keywords = preserve_keywords or [
            "api",
            "cli",
            "ui",
            "ux",
            "test",
            "doc",
            "fix",
            "feat",
            "add",
            "update",
            "improve",
            "refactor",
            "security",
            "performance",
            "bug",
            "issue",
        ]

    def optimize(
        self, text: str, max_length: int, platform: str = "generic"
    ) -> OptimizationResult:
        """
        Optimize text to fit within max_length.

        Args:
            text: Original text to optimize
            max_length: Maximum allowed characters
            platform: Target platform ('x', 'linkedin', 'generic') for platform-specific tuning

        Returns:
            OptimizationResult with optimized text and metadata
        """
        original_length = len(text)

        if len(text) <= max_length:
            return OptimizationResult(
                optimized_text=text,
                original_length=original_length,
                optimized_length=len(text),
                method="unchanged",
            )

        # Try different optimization strategies
        result = self._truncate_at_sentence(text, max_length)
        if result:
            return result

        result = self._summarize_extractive(text, max_length)
        if result:
            return result

        # Fallback: hard truncation with ellipsis
        return self._hard_truncate(text, max_length)

    def _truncate_at_sentence(
        self, text: str, max_length: int
    ) -> OptimizationResult | None:
        """
        Truncate at the last complete sentence that fits.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            OptimizationResult or None if no sentence boundary found
        """
        if len(text) <= max_length:
            return OptimizationResult(text, len(text), len(text), "unchanged")

        # Split into sentences (simple regex-based splitting)
        sentences = self._split_into_sentences(text)

        if len(sentences) <= 1:
            return None

        # Accumulate sentences until we exceed limit
        accumulated = ""
        last_complete_idx = -1

        for i, sentence in enumerate(sentences):
            test_text = accumulated + sentence if accumulated else sentence
            if len(test_text) <= max_length:
                accumulated = test_text
                last_complete_idx = i
            else:
                break

        if last_complete_idx >= 0:
            optimized = "".join(sentences[: last_complete_idx + 1]).rstrip()
            return OptimizationResult(
                optimized_text=optimized,
                original_length=len(text),
                optimized_length=len(optimized),
                method="truncated",
            )

        return None

    def _summarize_extractive(
        self, text: str, max_length: int
    ) -> OptimizationResult | None:
        """
        Perform extractive summarization by selecting important sentences.

        Prioritizes sentences that:
        - Contain preserve_keywords
        - Are at the beginning (usually more important)
        - Are medium-length (avoid very short or very long)

        Args:
            text: Text to summarize
            max_length: Maximum length

        Returns:
            OptimizationResult or None if summarization not possible
        """
        sentences = self._split_into_sentences(text)

        if len(sentences) <= 1:
            return None

        # Score sentences
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, i, len(sentences))
            scored_sentences.append((score, sentence))

        # Sort by score descending
        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        # Try to fit highest-scoring sentences within limit
        result_sentences = []
        current_length = 0

        for score, sentence in scored_sentences:
            # Add sentence if it fits (with space for ellipsis if needed)
            tentative_length = (
                current_length + len(sentence) + (3 if result_sentences else 0)
            )
            if tentative_length <= max_length:
                result_sentences.append(sentence)
                current_length = tentative_length

        if result_sentences:
            # Sort selected sentences by original order
            original_indices = []
            for rs in result_sentences:
                idx = sentences.index(rs)
                original_indices.append((idx, rs))
            original_indices.sort(key=lambda x: x[0])
            ordered_sentences = [rs[1] for rs in original_indices]

            optimized = " ".join(ordered_sentences)
            if len(optimized) < len(text) and current_length < max_length:
                optimized = optimized.rstrip() + " [...]"

            return OptimizationResult(
                optimized_text=optimized[:max_length],
                original_length=len(text),
                optimized_length=len(optimized[:max_length]),
                method="summarized",
            )

        return None

    def _score_sentence(self, sentence: str, index: int, total_sentences: int) -> float:
        """
        Score a sentence for importance in summarization.

        Higher score = more important to keep
        """
        score = 0.0

        # Position bonus: first and last sentences often important
        if index == 0:
            score += 10.0
        elif index == total_sentences - 1:
            score += 5.0
        else:
            score += 2.0  # Middle sentences get some baseline

        # Keyword bonus
        lower_sentence = sentence.lower()
        for keyword in self.preserve_keywords:
            if keyword.lower() in lower_sentence:
                score += 3.0

        # Length penalty: very short or very long sentences are less ideal
        length = len(sentence)
        if 50 <= length <= 200:
            score += 5.0
        elif length < 30:
            score -= 2.0
        elif length > 300:
            score -= 3.0

        # Question/exclamation emphasis
        if "?" in sentence or "!" in sentence:
            score += 2.0

        # Contains numbers/statistics (often important)
        if re.search(r"\d+", sentence):
            score += 1.5

        return score

    def _hard_truncate(self, text: str, max_length: int) -> OptimizationResult:
        """
        Truncate at word boundary, falling back to mid-word if necessary.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            OptimizationResult
        """
        if len(text) <= max_length:
            return OptimizationResult(text, len(text), len(text), "unchanged")

        # Try to truncate at a word boundary
        truncated = text[: max_length - 3]

        # Find last space
        last_space = truncated.rfind(" ")
        if last_space > max_length * 0.5:  # If we can keep at least half the text
            truncated = truncated[:last_space]

        truncated = truncated.rstrip() + "..."

        return OptimizationResult(
            optimized_text=truncated,
            original_length=len(text),
            optimized_length=len(truncated),
            method="truncated",
        )

    def optimize_repository_description(
        self,
        description: str,
        max_length: int,
        include_name: bool = False,
        name: str = "",
    ) -> OptimizationResult:
        """
        Optimize a repository description, potentially including the repo name.

        Args:
            description: Repository description text
            max_length: Maximum allowed characters
            include_name: Whether to include the repo name in the output
            name: Repository name (if include_name is True)

        Returns:
            OptimizationResult with optimized description
        """
        if not description:
            return OptimizationResult(
                optimized_text="",
                original_length=0,
                optimized_length=0,
                method="unchanged",
            )

        text = description
        if include_name and name:
            # If including name, need to reserve space for it
            name_with_parens = f"`{name}`"
            available_for_desc = (
                max_length - len(name_with_parens) - 2
            )  # 2 for space and colon
            if available_for_desc <= 0:
                # Not enough space, just truncate name
                return OptimizationResult(
                    optimized_text=name_with_parens[:max_length],
                    original_length=len(description),
                    optimized_length=min(len(name_with_parens), max_length),
                    method="truncated",
                )
            result = self.optimize(description, available_for_desc)
            optimized = f"{name_with_parens}: {result.optimized_text}"
            return OptimizationResult(
                optimized_text=optimized[:max_length],
                original_length=len(description),
                optimized_length=len(optimized[:max_length]),
                method=result.method,
            )
        else:
            return self.optimize(description, max_length)

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using basic rules.

        Args:
            text: Text to split

        Returns:
            List of sentence strings (with trailing spaces where appropriate)
        """
        if not text:
            return []

        # Clean up whitespace first - normalize to single spaces
        text = " ".join(text.split())

        # Pattern: split on sentence terminators (., !, ?) followed by space or newline
        # But keep the terminator with the sentence
        pattern = r"(?<=[.!?])\s+"
        sentences = re.split(pattern, text)

        # If splitting didn't produce much, try alternative: split on newlines too
        if len(sentences) <= 1 and "\n" in text:
            sentences = [s.strip() for s in text.split("\n") if s.strip()]

        # Ensure each sentence ends with its terminator if it had one
        result = []
        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if sent and not sent[-1] in ".!?":
                # Add period if missing, unless it's the last sentence
                if i < len(sentences) - 1:
                    sent += "."
            result.append(sent + " ")

        return [s for s in result if s.strip()]
