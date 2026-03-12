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
│   ├── config/          # Configuration loading
│   ├── social_platforms/  # X and LinkedIn adapters
│   └── scripts/         # Markdown templates
├── tests/               # Unit tests
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
   python -m src.main
   ```

## Current Progress

**Phase 1: Planning & Setup** - In Progress
- [x] Define project architecture and technology stack
- [x] Initialize project repository with requirements.txt and linting/formatting
- [x] Create project directory structure
- [ ] Set up environment variables management

**Phase 2: GitHub Integration & Data Collection** - Pending
- [ ] Implement GitHub API client
- [ ] Create repository metadata collector
- [ ] Build data persistence layer (SQLite)
- [ ] Add date filtering logic

**Phase 3: Markdown Generation & Social Media Formatting** - Pending
- [ ] Design Markdown template
- [ ] Implement report generator
- [ ] Create platform-specific adapters (X, LinkedIn)
- [ ] Build content optimizer

**Phase 4: Scheduling, Automation & Deployment** - Pending
- [ ] Implement weekly scheduler
- [ ] Add social media posting integration
- [ ] Create logging system
- [ ] Build Dockerfile and docker-compose.yml

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

## License

MIT
