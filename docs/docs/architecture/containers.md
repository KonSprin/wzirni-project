# Container Architecture

The project consists of six Docker containers working together to capture and analyze network traffic.

## Server Container

**Purpose**: FastAPI HTTPS server simulating a real application

- **Port**: 8443 (HTTPS)
- **Image**: Custom (Python 3.11-slim + FastAPI)
- **Key Features**:
  - Realistic API endpoints (users, messages, search, data)
  - Auto-generated self-signed certificates
  - Session management and authentication
  - Variable payload sizes for analysis

**Endpoints**:

- `POST /users/register` - User registration
- `POST /users/login` - Authentication with session tokens
- `GET /users/{username}` - User information
- `POST /messages` - Send messages
- `GET /messages` - Retrieve messages
- `GET /data` - Small dataset
- `GET /data/large` - Large dataset (100 records)
- `GET /search` - Search with parameters
- `POST /upload/metadata` - File upload metadata
- `POST /echo` - Echo test endpoint

**Healthcheck**: Regular checks on `/health` endpoint to ensure server is ready

## PolarProxy Container

**Purpose**: Transparent TLS proxy for traffic decryption

- **Ports**:
  - 10443: Transparent proxy
  - 1080: HTTP CONNECT proxy (used by client)
  - 10080: Certificate download endpoint
  - 57012: PCAP-over-IP listener
- **Image**: mcr.microsoft.com/dotnet/runtime:8.0 + PolarProxy
- **Key Features**:
  - Man-in-the-middle TLS decryption
  - Generates CA certificate
  - Saves decrypted traffic to PCAP files
  - Signs leaf certificates on-the-fly

**Command Flags**:

```bash
-v                        # Verbose logging
-p 10443,80,443          # Listen on 10443, forward to 80, simulate 443
-o /var/log/PolarProxy/  # Output directory for PCAP files
--certhttp 10080         # Certificate download port
--pcapoverip 0.0.0.0:57012  # PCAP streaming
--httpconnect 1080       # HTTP CONNECT proxy port
--leafcert sign          # Sign all leaf certificates
```

**Output**: `proxy-YYYYMMDD-HHMMSS.pcap` files in `./polar-proxy/logs/`

## Cert-installer Container

**Purpose**: Download and distribute PolarProxy CA certificate

- **Lifecycle**: Runs once and exits
- **Image**: alpine:latest
- **Key Features**:
  - Checks if certificate already exists
  - Downloads CA from PolarProxy
  - Places certificate in shared volume
  - Sets proper file permissions

**Workflow**:

1. Wait for PolarProxy to start
2. Check if certificate exists in shared volume
3. If not, download from `http://polarproxy:10080/polarproxy.cer`
4. Save as `polarproxy.crt` with 644 permissions
5. Exit successfully

## Client Container

**Purpose**: Simulate realistic user traffic

- **Image**: Custom (Python 3.11-slim + requests)
- **Key Features**:
  - Installs PolarProxy CA certificate in trust store
  - Routes all HTTPS traffic through PolarProxy
  - Generates varied traffic patterns
  - Simulates multiple user workflows

**Environment**:

- `HTTPS_PROXY=http://polarproxy:1080` - Routes traffic through proxy

**Traffic Patterns**:

- Main workflow (every 5 cycles):
  - User registration/login
  - Send 1-3 messages
  - Check messages
  - Search queries
  - Data retrieval
  - File uploads
  - Echo tests

- Light polling (between workflows):
  - Random single actions
  - 3-7 second delays

**Dependencies**:

- Waits for server healthcheck
- Waits for PolarProxy startup
- Waits for cert-installer completion

## Sniffer Container

**Purpose**: Capture encrypted traffic as seen by network observer

- **Image**: nicolaka/netshoot
- **Network Mode**: `service:server` (shares server's network stack)
- **Capabilities**: NET_ADMIN, NET_RAW
- **Key Features**:
  - Captures traffic at server level
  - No access to TLS keys
  - Shows what passive attacker sees
  - Uses tcpdump for capture

**Command**:

```bash
tcpdump -i any -w /captures/encrypted-traffic.pcap 'tcp port 8443'
```

**Output**: `encrypted-traffic.pcap` in `./sniffer/captures/`

## Wireshark Container

**Purpose**: Web-based Wireshark GUI for traffic analysis

- **Ports**:
  - 3010: HTTP web interface
  - 3001: HTTPS interface
- **Image**: lscr.io/linuxserver/wireshark:latest
- **Key Features**:
  - Full Wireshark functionality in browser
  - Access to both encrypted and decrypted PCAPs
  - Persistent configuration
  - No local installation required

**Mounted Volumes**:

- `/pcaps` → `./polar-proxy/logs/` (decrypted traffic, read-only)
- `/encrypted-pcaps` → `./sniffer/captures/` (encrypted traffic, read-only)
- `/config` → `./wireshark_config/` (persistent settings)

**Access**: Navigate to `http://localhost:3010` in browser

## Container Dependencies

```text
cert-installer → depends on → polarproxy
       ↓
    client → depends on → [server (healthy), polarproxy, cert-installer (completed)]
       ↓
   sniffer → network_mode → server
```

## Volumes

### Named Volumes

- `polarproxy-certs`: Shared volume for CA certificate
  - Mounted in cert-installer (read-write)
  - Mounted in client (read-only)
  - Binds to `./client/certs/`

### Bind Mounts

- `./server/certs` → `/app/certs` in server
- `./polar-proxy/logs` → `/var/log/PolarProxy/` in polarproxy
- `./polar-proxy/home` → `/home/polarproxy/` in polarproxy
- `./sniffer/captures` → `/captures` in sniffer
- `./wireshark_config` → `/config` in wireshark

## Network

All containers (except sniffer) communicate through `app_network` (bridge driver).

Sniffer uses `network_mode: "service:server"` to share server's network namespace.
