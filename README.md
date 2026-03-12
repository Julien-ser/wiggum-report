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
   - `DATA_DIR`: Data storage directory (default: `./data`)

3. **Run the application:**
   ```bash
   python -m src.scheduler
   ```

   The scheduler will:
   - Run the report immediately on startup (can be disabled)
   - Then run weekly according to your `SCHEDULE_CRON` or `SCHEDULE_INTERVAL_HOURS` settings
   - Generate and save markdown reports to `./data/reports/`
   - Log all activity to console (can be extended to file logging)

   To run once without scheduling:
   ```bash
   python -c "from src.scheduler import WiggumScheduler; from src.config.settings import load_settings; s = WiggumScheduler(load_settings()); s.run_weekly_report()"
   ```

   To run indefinitely as a daemon/service, see the Deployment section below.

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
- [ ] Add actual social media posting integration (adapters format content, but API posting not yet implemented)
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
Environment="PATH=/path/to/venv/bin"
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

### Running with Cron (Alternative)

If you prefer cron over the built-in scheduler, you can run the report once on a schedule:

```bash
# Edit crontab
crontab -e

# Add this line to run every Monday at 9 AM
0 9 * * 1 cd /path/to/wiggum-report && /usr/bin/python3 -m src.scheduler --run-once
```

Note: The `--run-once` flag can be added to the scheduler (future enhancement) to run once and exit, suitable for cron jobs.

### Docker Deployment (Future)

A Dockerfile and docker-compose.yml will be provided in a future update for containerized deployment.

## License

MIT
