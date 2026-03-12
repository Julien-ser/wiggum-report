# Dockerfile for Wiggum Report
# Build: docker build -t wiggum-report .
# Run: docker-compose up -d

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Expose no ports (this is a scheduled background service)

# Run the scheduler
CMD ["python", "-m", "src.scheduler"]
