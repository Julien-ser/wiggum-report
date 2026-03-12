"""Tests for the content optimizer module."""

import pytest
from src.content_optimizer import ContentOptimizer, OptimizationResult


class TestContentOptimizer:
    """Test suite for ContentOptimizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = ContentOptimizer()

    def test_no_optimization_needed(self):
        """Test that short text is returned unchanged."""
        text = "Short text."
        result = self.optimizer.optimize(text, 100)

        assert result.optimized_text == text
        assert result.original_length == len(text)
        assert result.optimized_length == len(text)
        assert result.method == "unchanged"

    def test_simple_truncation_within_half(self):
        """Test truncation when original is over limit."""
        text = (
            "This is a very long text that exceeds the limit and should be truncated."
        )
        max_len = 40
        result = self.optimizer.optimize(text, max_len)

        assert result.optimized_length <= max_len
        assert result.method == "truncated"
        assert result.optimized_text.endswith("...")

    def test_sentence_boundary_preservation(self):
        """Test that complete sentences are preserved when possible."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        # max_length includes first sentence + part of second but second sentence complete would exceed
        max_len = 45  # "First sentence. Second" would be 23, second complete would be 33 total
        result = self.optimizer.optimize(text, max_len)

        # Should preserve at least first complete sentence
        assert "First sentence" in result.optimized_text
        # Should not cut mid-sentence if we can avoid it
        assert not result.optimized_text.rstrip().endswith(("sentence", "sentence,"))

    def test_summarization_for_long_text(self):
        """Test that summarization is attempted for multi-sentence text."""
        text = (
            "First sentence with important keywords like API and test. "
            "Second sentence with more details about implementation. "
            "Third sentence mentioning security and performance improvements. "
            "Fourth sentence with additional context and documentation updates. "
            "Fifth sentence with some filler content that is less important."
        )
        max_len = 100
        result = self.optimizer.optimize(text, max_len)

        # Should be shorter than original
        assert result.optimized_length < len(text)
        assert result.optimized_length <= max_len
        # Should contain some of the important sentences
        assert len(result.optimized_text) > 0

    def test_keyword_prioritization(self):
        """Test that sentences with keywords score higher."""
        text = (
            "This sentence has no keywords at all. "
            "But this one mentions API and test and security. "
            "Another sentence without special words. "
            "Performance improvements and bug fix included here."
        )

        # Extract sentences and score them
        sentences = self.optimizer._split_into_sentences(text)
        scores = []
        for i, sent in enumerate(sentences):
            score = self.optimizer._score_sentence(sent, i, len(sentences))
            scores.append((score, sent))

        # Verify keyword sentences have higher scores
        scores.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s for _, s in scores[:2]]

        # Top sentences should contain keywords
        assert any("API" in s or "test" in s or "security" in s for s in top_sentences)
        assert any(
            "performance" in s or "bug" in s or "fix" in s for s in top_sentences
        )

    def test_position_bonus_in_scoring(self):
        """Test that first sentence gets a position bonus."""
        sentences = ["First sentence.", "Second sentence.", "Third sentence."]
        scores = []
        for i, sent in enumerate(sentences):
            score = self.optimizer._score_sentence(sent, i, len(sentences))
            scores.append(score)

        # First sentence should have highest score (10 point bonus)
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_repository_description_with_name(self):
        """Test optimizing repo description when name should be included."""
        description = "This is a very long repository description that exceeds the maximum length limit and needs to be shortened significantly."
        name = "my-repo"
        max_len = 50  # `my-repo`: takes ~9 chars, leaves ~41 for description

        result = self.optimizer.optimize_repository_description(
            description, max_len, include_name=True, name=name
        )

        assert len(result.optimized_text) <= max_len
        assert "my-repo" in result.optimized_text
        assert "`" in result.optimized_text  # Name should be code-formatted

    def test_repository_description_without_name(self):
        """Test optimizing repo description without name."""
        description = (
            "This is a very long repository description that exceeds the limit."
        )
        max_len = 40

        result = self.optimizer.optimize_repository_description(
            description, max_len, include_name=False
        )

        assert len(result.optimized_text) <= max_len
        assert result.optimized_text != description  # Should be truncated

    def test_empty_description(self):
        """Test handling of empty description."""
        result = self.optimizer.optimize_repository_description("", 100)
        assert result.optimized_text == ""
        assert result.method == "unchanged"

    def test_very_short_max_length(self):
        """Test truncation when max_length is very small."""
        text = "This text is definitely too long for the limit."
        max_len = 10
        result = self.optimizer.optimize(text, max_len)

        assert result.optimized_length <= max_len
        assert result.method == "truncated"

    def test_whitespace_handling(self):
        """Test that whitespace is handled properly."""
        text = "   Extra   whitespace   here.   More   whitespace.   "
        max_len = 30
        result = self.optimizer.optimize(text, max_len)

        # Should not have excessive whitespace
        assert "  " not in result.optimized_text.strip()
        assert result.optimized_text.strip() == result.optimized_text

    def test_multiple_sentence_structures(self):
        """Test with various sentence termination patterns."""
        texts = [
            "First sentence! Second sentence? Third sentence.",
            "Line one\nLine two\nLine three",
            "Item one. Item two; item three. Item four!",
        ]
        for text in texts:
            result = self.optimizer.optimize(text, 50)
            assert result.optimized_text is not None
            assert len(result.optimized_text) <= 50

    def test_optimization_result_attributes(self):
        """Test that OptimizationResult has correct attributes."""
        text = "x" * 200
        result = self.optimizer.optimize(text, 50)

        assert hasattr(result, "optimized_text")
        assert hasattr(result, "original_length")
        assert hasattr(result, "optimized_length")
        assert hasattr(result, "method")
        assert result.original_length == 200
        assert result.optimized_length <= 50
        assert result.method in ("truncated", "summarized", "unchanged")


class TestContentOptimizerIntegration:
    """Integration-style tests for realistic scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = ContentOptimizer()

    def test_x_platform_description(self):
        """Test optimizing description for X (280 char limit)."""
        long_desc = (
            "This repository implements a comprehensive solution for processing "
            "large datasets using advanced machine learning algorithms. Features include "
            "data validation, transformation pipelines, model training, evaluation "
            "metrics, and deployment utilities. Perfect for production environments "
            "requiring robust ML workflows. Supports TensorFlow, PyTorch, and scikit-learn."
        )

        result = self.optimizer.optimize_repository_description(
            long_desc,
            280 - 50,
            include_name=False,  # Reserve space for other tweet parts
        )

        assert result.optimized_length < 280
        # Should still contain key concepts
        assert any(
            word in result.optimized_text.lower()
            for word in ["repository", "machine learning", "data"]
        )

    def test_linkedin_platform_description(self):
        """Test optimizing description for LinkedIn (3000 char limit)."""
        # Longer description, though well under 3000
        long_desc = (
            "This comprehensive repository provides enterprise-grade tools for "
            "continuous integration and deployment. Key features:\n\n"
            "• Automated testing with multiple frameworks\n"
            "• Containerized deployment using Docker\n"
            "• Monitoring and logging integration\n"
            "• Secure credential management\n"
            "• Scalable architecture design\n\n"
            "The project follows best practices for code quality, including "
            "extensive test coverage, code review processes, and comprehensive "
            "documentation. Ideal for teams looking to modernize their DevOps practices."
        )

        max_len = 3000 - 1000  # Reserve space for other LinkedIn post parts
        result = self.optimizer.optimize_repository_description(
            long_desc, max_len, include_name=False
        )

        assert result.optimized_length <= max_len
        # Should maintain key sections
        assert (
            "automated testing" in result.optimized_text.lower()
            or "testing" in result.optimized_text.lower()
        )

    def test_optimize_multiple_descriptions(self):
        """Test optimizing multiple descriptions for a weekly report."""
        descriptions = [
            "Short description.",
            "This is a medium length description that might need some optimization.",
            "This is an extremely long description that goes on and on with many details about the implementation, the technology stack, the use cases, and everything else you might want to know about this repository but we don't have space for all of it in a social media post so we need to truncate or summarize it intelligently.",
        ]

        optimized = []
        for desc in descriptions:
            result = self.optimizer.optimize_repository_description(desc, 100)
            optimized.append(result.optimized_text)

        # All should fit within limit
        assert all(len(o) <= 100 for o in optimized)
        # Shorter ones should remain relatively intact
        assert len(optimized[0]) > 5  # Not truncated to minimal
