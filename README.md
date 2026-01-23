# Network Traffic Analysis Project

Project for analyzing encrypted network traffic using
PolarProxy,Wireshark, CICFlowMeter, and a Python-based client-server setup.

## Quick Start

```bash
# Clone and start
git clone https://github.com/KonSprin/wzirni-project.git
cd wzirni-project
docker compose up --build
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
- **CICFlowMeter**: Extracts statistical features from network flows
- **Flow Analyzer**: Analyzes flow features and generates visualizations
- **Docs**: Complete documentation served via MkDocs

## Documentation

Full documentation is available at `http://localhost:8000` after running `docker compose up`.
Run `docker compose up docs` or `poetry run mkdocs serve` for documentation site only.

Topics covered:

- Architecture and container details
- Traffic analysis with Wireshark
- Flow analysis with CICFlowMeter
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
├── cicflowmeter/        # Flow feature extraction
├── docs/                # MkDocs documentation
├── flow_analyzer.py     # Flow analysis script
└── docker-compose.yaml  # Container orchestration
```

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

## Output Files

- `./polar-proxy/logs/` - Decrypted PCAP files
- `./sniffer/captures/` - Encrypted PCAP files
- `./cicflowmeter/output/` - Flow feature CSVs
- `./cicflowmeter/output/analysis/` - Analysis results and visualizations
- `./server/certs/` - Server certificates (auto-generated)
- `./client/certs/` - PolarProxy CA certificate (auto-generated)

## Key Features

### Statistical Analysis Without Decryption

CICFlowMeter extracts 83 features from network flows, enabling:

- Traffic classification (even when encrypted)
- Application fingerprinting
- Anomaly detection
- Behavioral pattern analysis

### Comprehensive Visualizations

The flow analyzer generates:

- Flow type distribution charts
- Timing pattern analysis
- Packet size statistics
- Periodic traffic detection
- Feature correlation heatmaps
- Time series traffic timelines

### Educational Value

Compare the same traffic:

- **Decrypted**: See HTTP methods, headers, payloads
- **Encrypted**: See only TLS handshake and encrypted data
- **Statistical**: Reveal patterns visible in both

**Key Insight**: Even encrypted traffic reveals behavioral patterns through timing, packet sizes, and flow characteristics.

## Stopping

```bash
docker compose down
```

## Authors

- Konrad Springer - `konrad.springer@student.pk.edu.pl`
- Adam Tylec - `example@student.pk.edu.pl`

## License

Academic project for network traffic analysis research.
