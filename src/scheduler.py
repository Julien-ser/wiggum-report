"""Scheduler for running weekly Wiggum reports."""

import logging
import signal
import sys
import time
from datetime import datetime
from typing import Optional

import schedule

from src.config.settings import load_settings
from src.data_persistence import DataPersistence
from src.github_client import GitHubClient
from src.metadata_collector import MetadataCollector
from src.scripts.templates import generate_full_report, generate_social_media_summary
from src.social_platforms.x_adapter import XAdapter
from src.social_platforms.linkedin_adapter import LinkedInAdapter


class WiggumScheduler:
    """Handles scheduling and execution of weekly GitHub reports."""

    def __init__(self, settings):
        """
        Initialize WiggumScheduler with settings.

        Args:
            settings: Settings instance with configuration
        """
        self.settings = settings
        self.logger = self._setup_logging()
        self.running = False

        # Initialize components
        self.github_client = GitHubClient.from_settings(settings)
        self.data_persistence = DataPersistence.from_settings(settings)
        self.metadata_collector = MetadataCollector(
            github_client=self.github_client, data_persistence=self.data_persistence
        )

        # Initialize social media adapters with credentials from settings
        self.x_adapter = XAdapter(
            api_key=settings.x_api_key,
            api_secret=settings.x_api_secret,
            access_token=settings.x_access_token,
            access_token_secret=settings.x_access_token_secret,
        )
        self.linkedin_adapter = LinkedInAdapter(
            client_id=settings.linkedin_client_id,
            client_secret=settings.linkedin_client_secret,
            access_token=settings.linkedin_access_token,
        )

        self.logger.info("WiggumScheduler initialized successfully")

    def _setup_logging(self) -> logging.Logger:
        """
        Configure logging for the scheduler.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("wiggum_scheduler")
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        # Avoid adding handler multiple times
        if not logger.handlers:
            logger.addHandler(console_handler)

        return logger

    def run_weekly_report(self) -> None:
        """
        Execute the weekly report generation and social media posting.

        This is the main job that runs on the configured schedule.
        """
        self.logger.info("Starting weekly report generation")

        try:
            # Collect metadata and persist to database
            self.logger.info("Collecting repository metadata")
            metadata = self.metadata_collector.collect_and_persist(
                include_private=True,
                max_repos_per_category=None,
                commits_limit=50,
                releases_limit=10,
            )

            summary = metadata["summary"]
            self.logger.info(
                f"Collection complete: {summary['total_repos_processed']} repos, "
                f"{summary['new_repositories_count']} new, "
                f"{summary['updated_repositories_count']} updated"
            )

            # Generate markdown report
            self.logger.info("Generating markdown report")
            report = generate_full_report(metadata)

            # Save report to file (optional - could be stored in data dir)
            report_path = self._save_report_to_file(report, metadata)
            self.logger.info(f"Markdown report saved to {report_path}")

            # Generate and post to social media
            self._post_to_social_media(metadata)

            self.logger.info("Weekly report job completed successfully")

        except Exception as e:
            self.logger.error(
                f"Error during weekly report generation: {e}", exc_info=True
            )
            raise

    def _save_report_to_file(self, report: str, metadata: dict) -> str:
        """
        Save markdown report to a file with week-based naming.

        Args:
            report: Markdown report content
            metadata: Metadata dict with week_start

        Returns:
            Path to saved file
        """
        from datetime import datetime
        import os

        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(self.settings.data_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        # Generate filename from week start date
        week_start_str = metadata.get("week_start", datetime.now().isoformat())
        try:
            week_start = datetime.fromisoformat(week_start_str.replace("Z", "+00:00"))
            filename = f"wiggum_report_{week_start.strftime('%Y-%m-%d')}.md"
        except:
            filename = f"wiggum_report_{datetime.now().strftime('%Y-%m-%d')}.md"

        filepath = os.path.join(reports_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        return filepath

    def _post_to_social_media(self, metadata: dict) -> None:
        """
        Post report summaries to configured social media platforms.

        Args:
            metadata: Collected metadata to format for posting
        """
        platforms = [("X", self.x_adapter), ("LinkedIn", self.linkedin_adapter)]

        for platform_name, adapter in platforms:
            try:
                self.logger.info(f"Generating {platform_name} post")
                post_text = adapter.format(metadata)
                self.logger.info(
                    f"{platform_name} post prepared ({len(post_text)} chars):"
                )

                # Post to the platform
                success = adapter.post(post_text)

                if success:
                    self.logger.info(f"Successfully posted to {platform_name}")
                else:
                    self.logger.error(f"Failed to post to {platform_name}")

            except Exception as e:
                self.logger.error(
                    f"Error during {platform_name} posting: {e}", exc_info=True
                )

    def _setup_schedule(self) -> None:
        """Configure the schedule based on settings."""
        if self.settings.schedule_interval_hours:
            # Interval-based scheduling
            interval = self.settings.schedule_interval_hours
            schedule.every(interval).hours.do(self.run_weekly_report)
            self.logger.info(f"Scheduled to run every {interval} hour(s)")
        else:
            # Cron-based scheduling (default: Monday 9 AM)
            cron_expr = self.settings.schedule_cron
            # schedule library uses a different format: minute hour day month day_of_week
            parts = cron_expr.split()
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                schedule.every().day.at(f"{hour.zfill(2)}:{minute.zfill(2)}").do(
                    self.run_weekly_report
                )
                self.logger.info(f"Scheduled using cron: {cron_expr} (every week)")
            else:
                self.logger.warning(
                    f"Invalid cron expression: {cron_expr}. Falling back to Monday 9 AM"
                )
                schedule.every().monday.at("09:00").do(self.run_weekly_report)

    def start(self, run_immediately: bool = False) -> None:
        """
        Start the scheduler.

        Args:
            run_immediately: If True, run the job immediately before scheduling
        """
        self.logger.info("Starting WiggumScheduler")
        self.running = True

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Configure schedule
        self._setup_schedule()

        # Run immediately if requested
        if run_immediately:
            self.logger.info("Running report immediately (run_immediately=True)")
            try:
                self.run_weekly_report()
            except Exception as e:
                self.logger.error(f"Immediate run failed: {e}")

        # Main scheduling loop
        self.logger.info("Entering scheduler loop")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait before retrying

    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        self.logger.info("Stopping WiggumScheduler")
        self.running = False

    def _handle_shutdown(self, signum, frame) -> None:
        """
        Handle shutdown signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received shutdown signal {signum}, stopping...")
        self.stop()


def main():
    """Main entry point for running the wiggum-report scheduler."""
    try:
        # Load settings
        settings = load_settings()

        # Create and start scheduler
        scheduler = WiggumScheduler(settings)

        # Run immediately and then schedule weekly
        # For production indefinite running, set run_immediately=False
        run_immediately = True  # Could be made configurable
        scheduler.start(run_immediately=run_immediately)

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nScheduler interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
