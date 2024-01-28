# Ikabot API

The Ikabot API is a RESTful service crafted to augment Ikabot's capabilities across various scenarios.

## Features

### 1. Login Captcha Resolution

Effortlessly handle login captchas with automatic resolution.

### 2. Captcha Resolution for Piracy

Automatically resolve captchas associated with piracy-related actions.

### 3. Blackbox Token Generation

Generate Blackbox tokens for streamlined authentication.

## Usage

### Accessing the Hosted API

The Ikabot API is hosted and publicly accessible. No installation is required; refer to the Wiki for details on available endpoints and their usage.

### Self-Hosting Instructions

#### Prerequisites

To host the API yourself, ensure Docker is installed. Follow the instructions based on your operating system:

- **Linux:**
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  ```

- **Windows:**
  Install Docker Desktop using the [Windows Installation Guide](https://docs.docker.com/desktop/install/windows-install/).

#### Launching the API

1. Download the source code from the repository (ZIP or Git clone).
2. Navigate to the downloaded source code directory.
3. Run the following Docker Compose command to build and launch the API:

   ```bash
   docker-compose up -d --build
   ```

   The default listening port is set to 80; you can adjust this in the Nginx configuration: `/nginx/app.conf`.