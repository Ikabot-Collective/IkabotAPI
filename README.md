# Ikabot API

The **Ikabot API** is a RESTful service built with **FastAPI**, designed to enhance Ikabot's capabilities across various scenarios.

## Features

### 1. Login Captcha Resolution

Effortlessly handle login captchas with automatic resolution.

### 2. Captcha Resolution for Piracy

Automatically resolve captchas associated with piracy-related actions.

### 3. Blackbox Token Generation

Generate Blackbox tokens for streamlined authentication.

---

## Accessing the Hosted API

The Ikabot API is hosted and publicly accessible. No installation is required; refer to the Wiki for details on available endpoints and their usage.

When self-hosting locally:

* Swagger UI → `http://localhost:5000/docs` (development) or `http://localhost:5005/docs` (production-like)
* ReDoc → `http://localhost:5000/redoc` / `http://localhost:5005/redoc`

---

## Self-Hosting Instructions for Production

### Prerequisites

* **Docker** installed on your Linux server.

### Run the API

You can launch the API using one of the following methods, depending on whether you want to use Nginx or an existing reverse proxy.

#### Method 1: Using Docker with Nginx

```bash
docker-compose up -d --build
```

* Default port: **80** (configurable in `/nginx/app.conf`).

#### Method 2: Without Nginx (Using an Existing Reverse Proxy)

```bash
docker build -t ikabotapi .
docker run -d -p 5005:5005 ikabotapi
```

> Need a different host port?

```bash
docker run -d -p 8000:5005 ikabotapi
```

---

## Development Instructions

### Prerequisites

* **Python 3.10**
* **Poetry**
* **Playwright** (browsers required at runtime)

### Setup (local development)

```bash
git clone <repo_url>
cd ikabotapi

# Install all dependencies (main + dev groups from pyproject.toml)
poetry install

# Install Playwright browsers (Chromium)
# On Linux: --with-deps is recommended; on macOS/Windows, omit if not needed
poetry run playwright install --with-deps chromium
```

### Run (development, with auto-reload)

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

* API: `http://localhost:5000`
* Docs: `http://localhost:5000/docs`

### Run (production-like, mirrors Docker)

```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 5005 --workers 1 --access-log --log-level info
```

---

## Running Tests

Test dependencies are already declared under `[tool.poetry.group.dev.dependencies]` in `pyproject.toml`.

Run the test suite:

```bash
poetry run pytest tests
```

---

## Configuration

The API can be configured with environment variables.

### Discord Logging (optional)

You can enable logging to a Discord channel by setting the `LOGS_WEBHOOK_URL` environment variable.

Example `.env.example`:

```env
# The Webhook URL of a Discord channel for logs (optional)
LOGS_WEBHOOK_URL=
```

Options to set it:

* Create a local `.env` file (loaded automatically by `python-dotenv`).
* Or pass it as an environment variable in Docker:

  ```bash
  docker run -d -p 5005:5005 -e LOGS_WEBHOOK_URL="https://discord.com/api/webhooks/xxxx" ikabotapi
  ```

---

## Quick Start (API check)

* Open Swagger UI:

  * Dev mode → [http://localhost:5000/docs](http://localhost:5000/docs)
  * Prod mode → [http://localhost:5005/docs](http://localhost:5005/docs)

* Or test an endpoint with `curl` (replace `<path>` with one of your endpoints):

```bash
curl -X GET "http://localhost:5000/<path>" -H "accept: application/json"
```
