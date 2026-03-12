# Wiggum Report

**An automated weekly report generator for your GitHub repositories, posted to X (Twitter) and LinkedIn.**

## Mission

Wiggum Report runs indefinitely and checks your GitHub account every week for new repositories and significant updates. It generates a beautiful Markdown report and posts it to your social media accounts, keeping your network informed about your open source contributions.

## Technology Stack

- **Language**: Python 3.10+
- **GitHub API**: PyGithub
- **Social APIs**: tweepy (X/Twitter), linkedin-api (LinkedIn)
- **Scheduling**: schedule library
- **Data Persistence**: SQLite
- **Environment**: python-dotenv for secure credential management
- **Linting/Formatting**: Black, Flake8
- **Deployment**: Docker, Docker Compose, systemd, cron

## Project Structure

```
wiggum-report/
├── src/
│   ├── config/               # Configuration loading
│   │   └── settings.py       # Settings and environment variables
│   ├── content_optimizer.py  # Intelligent text truncation and summarization
│   ├── github_client.py      # GitHub API client using PyGithub
│   ├── metadata_collector.py # Repository metadata collection
│   ├── data_persistence.py   # SQLite persistence layer
│   ├── social_platforms/     # X and LinkedIn adapters
│   └── scripts/              # Markdown templates
├── tests/               # Unit tests
│   ├── test_config.py
│   ├── test_content_optimizer.py
│   ├── test_github_client.py
│   ├── test_metadata_collector.py
│   ├── test_data_persistence.py
│   ├── test_templates.py
│   └── test_social_platforms.py
├── logs/                # Log files
├── .env.example         # Environment variables template
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration (Black, Flake8)
└── README.md            # This file
```

## Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API credentials:
   - `GITHUB_TOKEN`: GitHub Personal Access Token
   - `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`: X/Twitter API credentials
   - `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`: LinkedIn API credentials
   - `SCHEDULE_CRON`: Cron expression (default: `0 9 * * 1` for Monday 9 AM)
   - `SCHEDULE_INTERVAL_HOURS`: Optional interval in hours (overrides cron)
   - `DATA_DIR`: Data storage directory (default: `./data`)

3. **Run the application:**
   ```bash
   python -m src.scheduler
   ```

   The scheduler will:
   - Run the report immediately on startup (can be disabled)
   - Then run weekly according to your `SCHEDULE_CRON` or `SCHEDULE_INTERVAL_HOURS` settings
   - Generate and save markdown reports to `./data/reports/`
   - Log all activity to console and rotating log files in `./logs/`

   To run once without scheduling:
   ```bash
   python -c "from src.scheduler import WiggumScheduler; from src.config.settings import load_settings; s = WiggumScheduler(load_settings()); s.run_weekly_report()"
   ```

   To run indefinitely as a daemon/service, see the Deployment section below.

## Logging

Wiggum Report uses Python's built-in logging module with centralized configuration. All log messages are prefixed with `[wiggum.*]` for easy filtering.

**Configuration via environment variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `LOG_DIR` | Directory to store log files | `./logs` |
| `LOG_FILE` | Log filename | `wiggum.log` |
| `LOG_MAX_SIZE_MB` | Maximum size per log file before rotation (MB) | `10` |
| `LOG_BACKUP_COUNT` | Number of rotated log files to keep | `5` |

**Log features:**
- Rotating file handler: logs are automatically rotated when they reach the configured size
- Console output: all logs are also printed to stdout/stderr
- Hierarchical loggers: each module gets its own logger namespace (e.g., `wiggum.github_client`, `wiggum.scheduler`)
- Structured format: `timestamp - logger_name - level - message`

**Example log entries:**
```
2024-01-15 10:30:00 - wiggum.scheduler - INFO - Starting weekly report generation
2024-01-15 10:30:05 - wiggum.github_client - DEBUG - Fetching commits for repo: owner/repo
2024-01-15 10:30:10 - wiggum.x_adapter - INFO - Successfully posted to X: tweet_id=12345
```

**Viewing logs:**
```bash
# Tail the log file
tail -f logs/wiggum.log

# Filter by log level
grep "ERROR" logs/wiggum.log

# Filter by module
grep "github_client" logs/wiggum.log
```

## Current Progress

**Phase 1: Planning & Setup** - Complete
- [x] Define project architecture and technology stack
- [x] Initialize project repository with requirements.txt and linting/formatting
- [x] Create project directory structure
- [x] Set up environment variables management

**Phase 2: GitHub Integration & Data Collection** - Complete
- [x] Implement GitHub API client
- [x] Create repository metadata collector
- [x] Build data persistence layer using SQLite to store weekly reports and track reported repos
- [x] Add date filtering logic to identify repos created or updated within the last 7 days

**Phase 3: Markdown Generation & Social Media Formatting** - Complete
- [x] Design Markdown template
- [x] Implement report generator
- [x] Create platform-specific adapters (X with 280-char limit and shortened links, LinkedIn with professional format)
- [x] Build content optimizer that truncates or summarizes long descriptions to fit platform constraints while maintaining key information

**Phase 4: Scheduling, Automation & Deployment** - In Progress
- [x] Implement weekly scheduler using Python `schedule` library with configurable timing (cron or interval-based)
- [x] Add actual social media posting integration with tweepy (X) and linkedin-api, including error handling and rate limit management
- [x] Create comprehensive logging system embedded in scheduler
- [ ] Build Dockerfile and docker-compose.yml for containerized deployment

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black .
```

Lint:
```bash
flake8
```

## Deployment

### Docker Deployment (Recommended)

Wiggum Report can be deployed using Docker for easy containerized operation:

1. **Prerequisites:**
   - Docker and Docker Compose installed
   - Your API credentials configured in `.env` file (see Setup section)

2. **Build and run:**
   ```bash
   # Build the Docker image
   docker-compose build

   # Start the service in detached mode
   docker-compose up -d

   # View logs
   docker-compose logs -f

   # Stop the service
   docker-compose down
   ```

3. **Data persistence:**
   - Reports are saved to `./data/reports/` on the host machine
   - Logs are saved to `./logs/wiggum.log` on the host machine
   - The service will automatically restart after system reboot (due to `restart: unless-stopped`)

4. **Configuration:**
   The `.env` file in the project root is automatically loaded by docker-compose. Ensure it contains all required API credentials before starting.

5. **Update:**
   ```bash
   # Pull latest code changes and rebuild
   git pull
   docker-compose build --no-cache
   docker-compose up -d
   ```

6. **Monitor:**
   ```bash
   # Check container status
   docker-compose ps

   # View recent logs
   docker-compose logs --tail=100

   # Execute a one-off command (e.g., test)
   docker-compose exec wiggum-report python -c "print('Hello')"
   ```

### Running as a Systemd Service

Create a systemd service file at `/etc/systemd/system/wiggum-report.service`:

```ini
[Unit]
Description=Wiggum Report Scheduler
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/wiggum-report
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 -m src.scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wiggum-report
sudo systemctl start wiggum-report
sudo systemctl status wiggum-report
```

## License

MIT
