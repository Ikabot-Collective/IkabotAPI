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

* **Docker** installed on your Linux server, with the **Docker Compose** plugin if using Nginx.

### Build from source (default)

Clone this repository and run the following commands from its root directory. The supplied `docker-compose.yml` builds the API locally by default; no configuration changes are needed.

#### With Nginx (Docker Compose)

```bash
docker compose up -d --build
```

The API is accessible through Nginx on port **80**, with Swagger UI at `http://localhost/docs`.

#### Without Nginx (using an existing reverse proxy)

```bash
docker build -t ikabotapi .
docker run -d -p 5005:5005 ikabotapi
```

Swagger UI is available at `http://localhost:5005/docs`. To use a different host port, replace `-p 5005:5005` with, for example, `-p 8000:5005`.

### Alternative: use a prebuilt release image

If you prefer to skip the local build, release images are also published to GitHub Container Registry (GHCR). Images become available after the first successful release; the package must be public for downloads without authentication.

Choose a published version from the [releases page](https://github.com/Ikabot-Collective/IkabotAPI/releases). Before using the examples below, replace `<VERSION>` with the chosen version number in `MAJOR.MINOR.PATCH` format, without the `v` prefix (already included in the image tags). Use a version tag to keep deployments reproducible. The separate `latest` tag points to the most recently published release.

#### With Nginx (Docker Compose)

Clone this repository, or copy `docker-compose.yml` and the `nginx/` directory to your server. In `docker-compose.yml`, replace `build: .` under the `app` service with:

```yaml
    image: "ghcr.io/ikabot-collective/ikabotapi:v<VERSION>"
```

Keep all other service settings, including `container_name: ikabotapi`, the network, the health check, and the Nginx service. No changes to `nginx/app.conf` are needed: the API still listens on port `5005`.

From the directory containing `docker-compose.yml`, run:

```bash
docker compose pull
docker compose up -d
```

The API is accessible through Nginx on port **80**, with Swagger UI at `http://localhost/docs`. To upgrade, change the image tag to another published version and run these commands again. Using `latest` also requires pulling the image and recreating the container; it does not update a running container automatically.

#### Without Nginx (using an existing reverse proxy)

```bash
docker pull "ghcr.io/ikabot-collective/ikabotapi:v<VERSION>"
docker run -d --name ikabotapi --restart always -p 5005:5005 "ghcr.io/ikabot-collective/ikabotapi:v<VERSION>"
```

Swagger UI is available at `http://localhost:5005/docs`. To use a different host port, replace `-p 5005:5005` with, for example, `-p 8000:5005`.

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

## Publishing a release

Releases follow the same milestone-based process as the Ikabot client:

1. Choose the next stable version in `MAJOR.MINOR.PATCH` format, represented below by `<VERSION>`. Create an open GitHub milestone whose title is that version number (without `v`), and assign the relevant issues and pull requests.
2. Merge the changes to `main`.
3. Open **Actions → Publish Release → Run workflow**, select `main`, and enter the milestone title.

Pull requests targeting `main` and pushes to `main` run the Python tests and a **Docker Build & Smoke Test** check in parallel. The Docker check builds without publishing, starts the container with its default command, and checks that `/health` reports a healthy status and the expected application version. Making these checks required in branch protection also requires an appropriate release bot bypass or a release flow through pull requests: the current direct version push cannot satisfy required GitHub checks on a commit that has not yet been pushed.

The release workflow updates `apps/__init__.py` and the Poetry version in `pyproject.toml` and creates a local commit as `github-actions[bot]`. It runs the Python tests and the same Docker build and smoke test against that commit, with the new version already included. Only after these checks succeed and the validated image is saved as a workflow artifact does it push the version commit to `main`. A test or build failure therefore leaves `main` unchanged. If `main` advances in the meantime, the push fails instead of silently including untested changes; start a new release run from the updated `main` in that case.

The application uses `apps.__version__` for its OpenAPI schema, health response, and home page. Tests, release notes, the release tag, and the Docker image all refer to the resulting commit SHA, including the version bump.

Release notes use GitHub's generated changelog and the same `Keboo/GitHubHelper@master` contributor section as Ikabot. Contributors are selected by milestone; the generated changelog describes changes since the previous release, with categories configured in `.github/release.yml`.

After the version commit is pushed and release notes are generated, the workflow publishes the validated Docker image to GitHub Container Registry (GHCR). It downloads the saved image and verifies the archive checksum, commit SHA, and version before publishing, without rebuilding:

```text
ghcr.io/ikabot-collective/ikabotapi:v<VERSION>
ghcr.io/ikabot-collective/ikabotapi:latest
```

It then creates the GitHub release `v<VERSION>` as a draft, publishes it automatically, and closes the milestone. This workflow only publishes releases and images; it does not update a running server.

The workflow uses the built-in `GITHUB_TOKEN`; no Docker Hub or PyPI credentials are needed. Repository/organization policies must allow GitHub Actions to push the version commit to `main` and publish packages. If `main` is protected against direct bot pushes, that policy must be addressed before running a release. For anonymous image downloads, set the GHCR package visibility to public after its first publication.

Only one release runs at a time. Invalid version titles, version downgrades, missing open milestones, and existing release tags are rejected. If a publication job fails, use **Re-run failed jobs** on the original run to keep using the same validated version commit and image; the image artifact is retained for seven days. A failure after validation can leave the version commit on `main`, an uploaded image, or a draft release; the milestone closes only after the release is published.

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

### Token Generation

Blackbox tokens are generated fresh for every request. Playwright calls are serialized with a threading lock.
The `/v1/token` route accepts optional `user_agent`, `locale`, and `timezone_id` query parameters.
When omitted, `locale` defaults to `en-GB` and `timezone_id` defaults to `Europe/London`.

---

## Quick Start (API check)

* Open Swagger UI:

  * Dev mode → [http://localhost:5000/docs](http://localhost:5000/docs)
  * Prod mode → [http://localhost:5005/docs](http://localhost:5005/docs)

* Or test an endpoint with `curl` (replace `<path>` with one of your endpoints):

```bash
curl -X GET "http://localhost:5000/<path>" -H "accept: application/json"
```
