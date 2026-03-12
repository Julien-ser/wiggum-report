# wiggum-report
**Mission:** Create a system that runs indefinitely and every week checks my github for every new repo and writes an MD script for that week to post on x and linkedin with the repo updates. Call it the wiggum report

## Phase 1: Planning & Setup
- [x] Define project architecture and technology stack (Node.js/Python, schedule library, GitHub API, social media APIs)
- [x] Initialize project repository with package.json/requirements.txt and configure linting/formatting (ESLint/Prettier or Black/Flake8)
- [x] Create project directory structure: `/src` for core logic, `/config` for API keys/secrets, `/scripts` for Markdown templates, `/tests` for unit tests
- [x] Set up environment variables management using python-dotenv or dotenv to securely store GitHub token, X API credentials, LinkedIn API credentials

## Phase 2: GitHub Integration & Data Collection
- [x] Implement GitHub API client using Octokit (Node.js) or PyGithub (Python) to fetch authenticated user's repositories
- [x] Create repository metadata collector to gather repo name, description, stars, forks, recent commits, README updates, and release notes from the past week
- [x] Build data persistence layer using SQLite or JSON file to store weekly report history and track already-reported repos to avoid duplicates
- [x] Add date filtering logic to identify repos created or significantly updated within the last 7 days using GitHub's `created_at` and `updated_at` timestamps

## Phase 3: Markdown Generation & Social Media Formatting
- [x] Design Markdown template for weekly reports with sections: Summary Statistics, New Repositories, Notable Updates, Trending Repos, and Call-to-Action
- [ ] Implement report generator that transforms collected GitHub data into formatted Markdown with proper headings, emojis, links, and statistics tables
- [ ] Create platform-specific adapters: one for X (280 chars with shortened links and hashtags like #GitHub #OpenSource) and one for LinkedIn (longer professional format with bullet points)
- [ ] Build content optimizer that truncates or summarizes long descriptions to fit platform constraints while maintaining key information

## Phase 4: Scheduling, Automation & Deployment
- [ ] Implement weekly scheduler using node-cron (Node.js) or schedule library (Python) to run every Monday at 9 AM with configurable timing
- [ ] Add social media posting integration using X API v2 (tweepy/twitter-api-v2) and LinkedIn API (linkedin-api-rest-client) with error handling and rate limit management
- [ ] Create comprehensive logging system with Winston (Node.js) or logging module (Python) to track execution, errors, and posting results to log files
- [ ] Build Dockerfile and docker-compose.yml for containerized deployment, plus documentation for running as systemd service or cron job for indefinite operation
