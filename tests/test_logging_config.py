"""Tests for the logging configuration module."""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config.settings import Settings
from src.logging_config import get_logger, setup_logging, LoggerMixin


class TestSetupLogging:
    """Test the setup_logging function."""

    def test_setup_logging_defaults(self):
        """Test setup_logging with default parameters."""
        logger = setup_logging()
        assert logger is not None
        assert logger.level == logging.INFO
        assert logger.name == "wiggum"
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom log level."""
        logger = setup_logging(log_level="DEBUG")
        assert logger.level == logging.DEBUG
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_setup_logging_with_settings(self, tmp_path):
        """Test setup_logging with Settings object."""
        log_dir = tmp_path / "logs"
        settings = Settings(
            github_token="test_token",
            x_api_key="test",
            x_api_secret="test",
            x_access_token="test",
            x_access_token_secret="test",
            linkedin_client_id="test",
            linkedin_client_secret="test",
            linkedin_access_token="test",
            log_level="WARNING",
            log_dir=str(log_dir),
            log_file="test.log",
            log_max_size_mb=5,
            log_backup_count=3,
        )
        logger = setup_logging(settings)
        assert logger is not None
        assert logger.level == logging.WARNING
        assert log_dir.exists()
        assert (log_dir / "test.log").exists()
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_setup_logging_creates_log_dir(self, tmp_path):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        log_dir = tmp_path / "new_logs"
        assert not log_dir.exists()
        setup_logging(log_dir=str(log_dir))
        assert log_dir.exists()
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_setup_logging_console_handler(self):
        """Test that console handler is added by default."""
        logger = setup_logging()
        console_handlers = [
            h for h in logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) >= 1
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_setup_logging_no_console(self):
        """Test setup_logging with console_output=False."""
        logger = setup_logging(console_output=False)
        console_handlers = [
            h for h in logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) == 0
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_setup_logging_file_handler_rotation(self, tmp_path):
        """Test that rotating file handler is configured correctly."""
        log_dir = tmp_path / "logs"
        log_file = log_dir / "test_rotation.log"
        max_size = 1024  # 1 KB for testing
        backup_count = 2

        logger = setup_logging(
            log_dir=str(log_dir),
            log_file="test_rotation.log",
            max_bytes=max_size,
            backup_count=backup_count,
        )

        file_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(file_handlers) == 1
        handler = file_handlers[0]
        assert handler.maxBytes == max_size
        assert handler.backupCount == backup_count
        assert handler.baseFilename == str(log_file)
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_setup_logging_handles_file_error(self, tmp_path, monkeypatch):
        """Test that file handler errors are handled gracefully."""
        # Make log_dir read-only to trigger permission error
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_dir.chmod(0o444)  # Read-only

        try:
            # Should fall back to console-only logging
            logger = setup_logging(log_dir=str(log_dir))
            # Should still have console handler
            console_handlers = [
                h for h in logger.handlers if isinstance(h, logging.StreamHandler)
            ]
            assert len(console_handlers) >= 1
            # Cleanup
            logging.getLogger("wiggum").handlers.clear()
        finally:
            # Restore permissions for cleanup
            log_dir.chmod(0o755)

    def test_setup_logging_handles_invalid_level(self):
        """Test that invalid log level defaults to INFO."""
        logger = setup_logging(log_level="INVALID_LEVEL")
        assert logger.level == logging.INFO
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_setup_logging_idempotent(self):
        """Test that calling setup_logging multiple times doesn't add duplicate handlers."""
        logger1 = setup_logging()
        initial_handler_count = len(logger1.handlers)
        logger2 = setup_logging()
        # Should return the same logger with same number of handlers
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handler_count
        # Cleanup
        logging.getLogger("wiggum").handlers.clear()


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_namespacing(self):
        """Test that get_logger adds 'wiggum.' prefix."""
        logger = get_logger("module.submodule")
        assert logger.name == "wiggum.module.submodule"

    def test_get_logger_root_namespace(self):
        """Test that get_logger works with empty or simple names."""
        logger1 = get_logger("")
        assert logger1.name == "wiggum."

        logger2 = get_logger("simple")
        assert logger2.name == "wiggum.simple"

    def test_get_logger_same_call_returns_same_logger(self):
        """Test that get_logger returns the same logger instance for same name."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is logger2


class TestLoggerMixin:
    """Test the LoggerMixin class."""

    def test_logger_mixin_creates_logger(self):
        """Test that LoggerMixin creates a logger on initialization."""

        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        assert hasattr(obj, "logger")
        assert isinstance(obj.logger, logging.Logger)
        expected_name = f"src.logging_config.TestClass.{obj.__class__.__module__}.{obj.__class__.__name__}"
        # Cleanup
        logging.getLogger(obj.logger.name).handlers.clear()

    def test_logger_mixin_inheritance(self):
        """Test that LoggerMixin works with class inheritance."""

        class BaseClass(LoggerMixin):
            pass

        class DerivedClass(BaseClass):
            pass

        derived = DerivedClass()
        assert hasattr(derived, "logger")
        assert isinstance(derived.logger, logging.Logger)
        # Cleanup
        logging.getLogger(derived.logger.name).handlers.clear()


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_log_message_output(self, tmp_path, caplog):
        """Test that log messages are captured correctly."""
        log_dir = tmp_path / "logs"
        logger = setup_logging(
            log_dir=str(log_dir), console_output=False, log_level="DEBUG"
        )

        test_message = "Test log message"
        logger.info(test_message)

        # Check that the message was logged
        assert any(test_message in record.message for record in caplog.records)

        # Cleanup
        logging.getLogger("wiggum").handlers.clear()

    def test_multiple_modules_get_different_loggers(self):
        """Test that different modules get different logger names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1.name != logger2.name
        assert logger1.name == "wiggum.module1"
        assert logger2.name == "wiggum.module2"
        # Cleanup
        logging.getLogger(logger1.name).handlers.clear()
        logging.getLogger(logger2.name).handlers.clear()


class TestSettingsIntegration:
    """Test logging integration with Settings."""

    def test_settings_logging_defaults(self):
        """Test that Settings has sensible logging defaults."""
        settings = Settings(
            github_token="test",
            x_api_key="test",
            x_api_secret="test",
            x_access_token="test",
            x_access_token_secret="test",
            linkedin_client_id="test",
            linkedin_client_secret="test",
            linkedin_access_token="test",
        )
        assert settings.log_level == "INFO"
        assert settings.log_dir == "./logs"
        assert settings.log_file == "wiggum.log"
        assert settings.log_max_size_mb == 10
        assert settings.log_backup_count == 5

    def test_settings_custom_logging(self):
        """Test Settings with custom logging configuration."""
        settings = Settings(
            github_token="test",
            x_api_key="test",
            x_api_secret="test",
            x_access_token="test",
            x_access_token_secret="test",
            linkedin_client_id="test",
            linkedin_client_secret="test",
            linkedin_access_token="test",
            log_level="DEBUG",
            log_dir="/custom/logs",
            log_file="custom.log",
            log_max_size_mb=20,
            log_backup_count=10,
        )
        assert settings.log_level == "DEBUG"
        assert settings.log_dir == "/custom/logs"
        assert settings.log_file == "custom.log"
        assert settings.log_max_size_mb == 20
        assert settings.log_backup_count == 10
