# Architecture Overview

This document provides a high-level overview of the system architecture and how components interact.

## System Architecture

The project consists of six Docker containers orchestrated by Docker Compose:

```text
┌────────────────────────────────────────────────────────────┐
│                     Docker Environment                     │
│                                                            │
│  ┌──────────┐                                              │
│  │  Client  │─────HTTPS (via proxy)─────┐                  │
│  └──────────┘                           │                  │
│       │                                 │                  │
│       │ HTTP CONNECT                    │                  │
│       │ (port 1080)                     │                  │
│       ↓                                 ↓                  │
│  ┌──────────────┐                  ┌──────────┐            │
│  │  PolarProxy  │──────HTTPS───────│  Server  │            │
│  │              │                  │          │            │
│  │ - Decrypts   │                  │ Port 8443│            │
│  │ - Saves PCAP │                  └──────────┘            │
│  └──────────────┘                        │                 │
│       │                                  │                 │
│       │ Decrypted                        │ Encrypted       │
│       │ Traffic                          │ Traffic         │
│       ↓                                  ↓                 │
│  ./polar-proxy/logs/             ┌──────────┐              │
│  (Decrypted PCAP)                │  Sniffer │              │
│                                  │          │              │
│                                  └──────────┘              │
│                                       │                    │
│                                       ↓                    │
│                               ./sniffer/captures/          │
│                               (Encrypted PCAP)             │
│                                                            │
│  ┌──────────────┐                                          │
│  │  Wireshark   │◄─────Accesses both PCAP locations        │
│  │  (Web GUI)   │                                          │
│  └──────────────┘                                          │
│    Port 3010                                               │
│                                                            │
│  ┌──────────────┐                                          │
│  │     Docs     │                                          │
│  │  (MkDocs)    │                                          │
│  └──────────────┘                                          │
│    Port 8000                                               │
└────────────────────────────────────────────────────────────┘
```

## Component Roles

### Client

- **Purpose**: Traffic generator
- **Simulates**: Real user behavior
- **Generates**: Varied HTTPS requests
- **Routes through**: PolarProxy (transparent to application)

### Server

- **Purpose**: Application endpoint
- **Provides**: RESTful API with multiple endpoints
- **Uses**: FastAPI with self-signed TLS certificates
- **Serves**: Realistic application responses

### PolarProxy

- **Purpose**: TLS interception and decryption
- **Method**: Man-in-the-Middle (MITM)
- **Captures**: Decrypted traffic to PCAP
- **Provides**: CA certificate for client trust

### Sniffer

- **Purpose**: Passive network observation
- **Captures**: Encrypted traffic as-is
- **Shows**: What network observer sees without keys
- **Uses**: tcpdump for packet capture

### Wireshark

- **Purpose**: Traffic analysis interface
- **Provides**: Web-based GUI
- **Accesses**: Both encrypted and decrypted PCAPs
- **Enables**: Side-by-side comparison

### Docs

- **Purpose**: Documentation server
- **Provides**: Complete project documentation
- **Uses**: MkDocs with Material theme
- **Accessible**: Via web browser

## Data Flow

### Normal HTTPS Flow (Without Interception)

```text
Client ──[TLS]──► Server
       encrypted
```

Content is encrypted end-to-end. Network observers see only encrypted bytes.

### Intercepted Flow (With PolarProxy)

```text
Client ──[TLS]──► PolarProxy ──[TLS]──► Server
       (encrypted)           (encrypted)
           │
           │ [Decrypts]
           ↓
       PCAP File
     (plaintext HTTP)
```

PolarProxy acts as intermediary:

1. Client establishes TLS with PolarProxy (thinks it's the server)
2. PolarProxy establishes separate TLS with actual server
3. PolarProxy decrypts traffic from client
4. PolarProxy saves decrypted content to PCAP
5. PolarProxy re-encrypts and forwards to server

### Sniffer Perspective

```text
       ┌─[TLS]──► Server
       │  encrypted
Client ┤
       │  [Sniffer captures]
       └──►  PCAP File
            (encrypted TLS)
```

Sniffer sees the same encrypted traffic but cannot decrypt it.

## Certificate Chain

### Server Certificate

```text
Server generates ──► Self-signed cert ──► Used for TLS
                     (./server/certs/)
```

### PolarProxy CA Certificate

```text
PolarProxy generates ──► CA cert ──► Downloaded by ──► Installed in
                         (on startup)  cert-installer    client trust store

Client trusts ──► PolarProxy signs ──► Leaf certs
PolarProxy CA     server certificates  on-the-fly
```

This allows PolarProxy to MITM any connection.

## Network Configuration

### Docker Networks

- **app_network**: Bridge network connecting all containers (except sniffer)
- **Sniffer network mode**: Shares server's network namespace

### DNS Resolution

Containers resolve each other by service name:

- `client` → `server:8443`
- `client` → `polarproxy:1080`
- `cert-installer` → `polarproxy:10080`

### Port Mapping

External (host) → Internal (container):

- `8443 → server:8443` - HTTPS API
- `3010 → wireshark:3000` - Wireshark GUI
- `8000 → docs:8000` - Documentation
- `1080 → polarproxy:1080` - Proxy (internal only)
- `10080 → polarproxy:10080` - Cert download (internal only)

## Storage

### Volumes

**Named Volume**: `polarproxy-certs`

- Shared between cert-installer and client
- Stores PolarProxy CA certificate
- Binds to `./client/certs/`

### Bind Mounts

- `./server/certs` - Server TLS certificates
- `./polar-proxy/logs` - Decrypted PCAP files
- `./polar-proxy/home` - PolarProxy state
- `./sniffer/captures` - Encrypted PCAP files
- `./wireshark_config` - Wireshark settings
- `./docs` - Documentation source

## Startup Sequence

1. **Network creation**: Docker creates `app_network`
2. **Server start**: Generates certificates, starts HTTPS server
3. **PolarProxy start**: Launches proxy, generates CA cert
4. **Cert-installer**: Downloads PolarProxy CA, places in shared volume, exits
5. **Sniffer start**: Begins capturing encrypted traffic
6. **Wireshark start**: Mounts PCAP directories, serves GUI
7. **Docs start**: Serves documentation
8. **Client start** (waits for dependencies):
    - Server healthcheck passes
    - PolarProxy running
    - Cert-installer completed
    - Installs CA cert, begins generating traffic

## Traffic Types Generated

### Authentication Flow

```text
POST /users/register → 201 Created
POST /users/login → 200 OK (session_token)
GET /users/{username} → 200 OK
```

### Messaging

```text
POST /messages → 200 OK
GET /messages?limit=5&offset=0 → 200 OK
```

### Data Retrieval

```text
GET /data → 200 OK (small dataset)
GET /data/large → 200 OK (large dataset)
```

### Search

```text
GET /search?q=query&category=tech&limit=10 → 200 OK
```

### File Operations

```text
POST /upload/metadata → 200 OK
```

### Testing

```text
POST /echo → 200 OK (echoes request)
GET /health → 200 OK (health status)
```

## Technology Stack

- **Python 3.11**: Client and server applications
- **FastAPI**: Modern async web framework
- **Uvicorn**: ASGI server
- **PolarProxy**: .NET-based TLS proxy
- **tcpdump**: Packet capture
- **Wireshark**: Packet analysis
- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **MkDocs**: Documentation

## Design Principles

1. **Isolation**: Each component in separate container
2. **Reproducibility**: Fully automated setup
3. **Observability**: Multiple analysis perspectives
4. **Realism**: Traffic patterns mimic real usage
5. **Education**: Clear comparison of encrypted vs decrypted
