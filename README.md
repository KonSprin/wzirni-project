# Network Traffic Analysis Project

Analyze encrypted network traffic using PolarProxy, Wireshark, CICFlowMeter, and a Python-based client-server setup.

## Quick Start

```bash
# Clone and start
git clone https://github.com/KonSprin/wzirni-project.git
cd wzirni-project

# Start all services (3 clients)
docker compose up --build
```

**Access:**

- Wireshark: `http://localhost:3010`
- Documentation: `http://localhost:8000`

## What This Does

- **Server**: FastAPI HTTPS API with realistic endpoints
- **Clients**: Generate diverse traffic patterns (polling, downloads, bursts, interactive)
- **PolarProxy**: Decrypts TLS traffic to PCAP
- **Sniffer**: Captures encrypted traffic for comparison
- **Wireshark**: Web GUI for packet analysis
- **CICFlowMeter**: Extracts 83 statistical features from flows
- **Flow Analyzer**: Generates visualizations and classifications

## Analysis Workflow

```bash
# 1. Generate traffic (wait 2-3 minutes)
docker compose up -d
docker compose logs -f client-1

# 2. Extract flow features
docker compose -f docker-compose.analysis.yaml run --rm cicflowmeter

# 3. Analyze patterns
docker compose -f docker-compose.analysis.yaml run --rm flow-analyzer

# 4. View results in ./cicflowmeter/output/analysis/
```

## Documentation

Complete documentation at `http://localhost:8000` includes:

- Architecture and container details
- Traffic analysis guides
- API reference
- Troubleshooting

## Output Files

- `./polar-proxy/logs/` - Decrypted PCAP
- `./sniffer/captures/` - Encrypted PCAP
- `./cicflowmeter/output/` - Flow CSVs
- `./cicflowmeter/output/analysis/` - Visualizations

## Requirements

- Docker
- Docker Compose

## Traffic Analysis Workflow

1. **Capture Traffic**

   ```bash
   docker compose up server client sniffer polarproxy
   ```

2. **Analyze in Wireshark**
   - Open `http://localhost:3010`
   - Compare encrypted (`/encrypted-pcaps`) vs decrypted (`/pcaps`) traffic

3. **Extract Flow Features**

   ```bash
   docker compose run --rm cicflowmeter
   ```

4. **Analyze Flow Statistics**

   ```bash
   poetry run python flow_analyzer.py
   ```

   Results saved to `./cicflowmeter/output/analysis/`

## Authors

- Konrad Springer - `konrad.springer@student.pk.edu.pl`
- Adam Tylec - `example@student.pk.edu.pl`

## License

Academic project for network traffic analysis research.
