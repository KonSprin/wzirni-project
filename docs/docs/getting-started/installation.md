# Installation Guide

This guide covers the complete installation process for the network traffic analysis system.

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher

### Optional (for local development)

- **Python**: 3.11 or higher
- **Poetry**: Python dependency management
- **Git**: Version control

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **Disk**: 5GB free space
- **Network**: Internet connection for initial setup

## Installation Steps

### 1. Install Docker

=== "Linux"

    ```bash
    # Ubuntu/Debian
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER

    # Log out and back in for group changes to take effect
    ```

=== "macOS"

    Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)

=== "Windows"

    1. Install [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install)
    2. Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

### 2. Install Docker Compose

Docker Compose v2 is included with Docker Desktop. For Linux:

```bash
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

Verify installation:

```bash
docker compose version
# Should output: Docker Compose version v2.x.x
```

### 3. Clone Repository

```bash
git clone https://github.com/KonSprin/wzirni-project.git
cd wzirni-project
```

### 4. Build and Start Services

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up
```

For background execution:

```bash
docker-compose up -d
```

### 5. Verify Installation

Check that all containers are running:

```bash
docker ps
```

You should see five containers:

- `server`
- `client`
- `polarproxy`
- `cert-installer` (will exit after completing)
- `wireshark`

Test server connectivity:

```bash
curl --insecure https://localhost:8443/health
```

Access Wireshark GUI:

```text
http://localhost:3010
```

## First-Time Setup

### Certificate Generation

On first run, certificates are automatically generated:

1. **Server certificates**: Self-signed TLS certificates in `server/certs/`
2. **PolarProxy CA**: Root CA certificate for MITM in `polar-proxy/home/`
3. **Client trust**: CA certificate copied to client container

These steps are automatic. No manual intervention required.

### Wireshark Configuration

To access Wireshark GUI navigate to `http://localhost:3010`

If the password authentication is configured:

1. Note the password displayed in container logs:

   ```bash
   docker logs wireshark
   ```

2. Log in with the displayed password
3. Configuration is saved in `./wireshark_config/`

## Optional: Local Development Setup

For developing without Docker:

### Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Install Dependencies

```bash
# Server dependencies
cd server
poetry install

# Client dependencies
cd ../client
poetry install

# Root project dependencies (for pre-commit hooks)
cd ..
poetry install
```

### Pre-commit Hooks

```bash
poetry run pre-commit install
```

## Uninstallation

### Stop Services

```bash
docker-compose down
```

### Remove Volumes and Data

```bash
# Stop and remove volumes
docker-compose down -v

# Remove generated certificates
rm -rf server/certs/ client/certs/ polar-proxy/home/

# Remove PCAP files
rm -rf polar-proxy/logs/*.pcap

# Remove Wireshark config
rm -rf wireshark_config/
```

### Remove Images

```bash
docker-compose down --rmi all
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Learn basic operations
