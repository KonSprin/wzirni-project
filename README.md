# Network Traffic Analysis Project

Project for analyzing encrypted network traffic using PolarProxy, Wireshark, and a Python-based client-server setup.

## Quick Start

```bash
# Clone and start
git clone https://github.com/KonSprin/wzirni-project.git
cd wzirni-project
docker-compose up --build
```

### Access services

- Wireshark GUI: `http://localhost:3010`
- Documentation: `http://localhost:8000`

## What This Does

- **Server**: FastAPI HTTPS server with realistic API endpoints
- **Client**: Simulates user activity (login, messages, searches, data transfers)
- **PolarProxy**: Decrypts TLS traffic and saves to PCAP files
- **Sniffer**: Captures encrypted traffic for comparison
- **Wireshark**: Web-based GUI for analyzing both encrypted and decrypted traffic
- **Docs**: Complete documentation served via MkDocs

## Documentation

Full documentation is available at `http://localhost:8000` after running `docker-compose up`.
Run `docker compose up docs` or `poetry run mkdocs serve` for documentation site only.

Topics covered:

- Architecture and container details
- Traffic analysis techniques
- Configuration options
- Troubleshooting guide
- Analysis scenarios and examples

## Requirements

- Docker
- Docker Compose

## Project Structure

```text
├── client/              # HTTPS client simulator
├── server/              # FastAPI HTTPS server
├── polar-proxy/         # PolarProxy TLS decryption
├── sniffer/             # Encrypted traffic capture
├── docs/                # MkDocs documentation
└── docker-compose.yaml  # Container orchestration
```

## Output Files

- `./polar-proxy/logs/` - Decrypted PCAP files
- `./sniffer/captures/` - Encrypted PCAP files
- `./server/certs/` - Server certificates (auto-generated)
- `./client/certs/` - PolarProxy CA certificate (auto-generated)

## Stopping

```bash
docker-compose down
```

## Authors

- Konrad Springer - `konrad.springer@student.pk.edu.pl`
- Adam Tylec - `example@student.pk.edu.pl`

## License

Academic project for network traffic analysis research.
