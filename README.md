# Ikabot API

The Ikabot API is a RESTful service crafted to augment Ikabot's capabilities across various scenarios.

## Features

### 1. Login Captcha Resolution

Effortlessly handle login captchas with automatic resolution.

### 2. Captcha Resolution for Piracy

Automatically resolve captchas associated with piracy-related actions.

### 3. Blackbox Token Generation

Generate Blackbox tokens for streamlined authentication.

## Accessing the Hosted API

The Ikabot API is hosted and publicly accessible. No installation is required; refer to the Wiki for details on available endpoints and their usage.

## Self-Hosting Instructions for Production

### Prerequisites

To host the API yourself, ensure Docker is installed. Follow the instructions based on your operating system:

- **Linux:**
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  ```

- **Windows:**
  Install Docker Desktop using the [Windows Installation Guide](https://docs.docker.com/desktop/install/windows-install/).

### Run the API

1. Download the source code from the repository (ZIP or Git clone).
2. Navigate to the downloaded source code directory.
3. Run the following Docker Compose command to build and launch the API:

   ```bash
   docker-compose up -d --build
   ```

   The default listening port is set to 80; you can adjust this in the Nginx configuration: `/nginx/app.conf`.

## Development Instructions

### Prerequisites

Before setting up and launching the API, make sure to have the following prerequisites installed:
1. **Python 3.10**: Ensure that Python 3.10 is installed on your system.
2. **pip**: The Python package installer. Make sure it is installed as it is necessary for managing the project dependencies.

### Setting Up the Environment

Once the prerequisites are in place, follow these steps to set up your development environment:
1. Download the source code from the repository (ZIP or Git clone).
2. Navigate to the downloaded source code directory.
3. Install the project dependencies by running:

  ```bash
  pip install -r requirements.txt
  ```
4. Install Playwright (the automation library for browser testing and web scraping used in the project):
  ```bash
  python -m playwright install
  ```

### Launch the API

Once the environment is set up, you can proceed to launch the API using the following command:
  ```bash
  python run.py
  ```

The API will be accessible at http://localhost:5000.

### Running Tests

To ensure the reliability and correctness of the codebase, you can run the provided tests within the project.

1. Install the required test dependencies with the following commands:
  ```bash
  pip install pytest
  pip install pytest-mock
  ```
2. Execute the tests by running:
  ```bash
  python -m pytest tests
  ```

NOTE: For enhanced testing convenience, you can configure tests within your IDE. In Visual Studio Code, for instance, follow these steps:
1. Open the command palette using Ctrl+Shift+P.
2. Select "Python: Configure Tests."
3. Choose "pytest" as the testing framework.
   
After configuration, you can easily run tests by navigating to the test explorer.
