FROM python:3.10-slim

COPY . /ikabotapi/
WORKDIR /ikabotapi

# Install Poetry
RUN pip install --no-cache-dir --upgrade pip && \
    pip install poetry

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only=main

# Install system dependencies and Xvfb for non-headless browser
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        curl \
        gnupg \
        ca-certificates \
        xvfb \
        xauth && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
# Install playwright browsers and dependencies in one command (best practice)
RUN python -m playwright install --with-deps chromium

# Use xvfb-run to provide virtual display for non-headless Playwright
CMD xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" uvicorn main:app --host 0.0.0.0 --port 5005 --workers 1 --access-log --log-level info
