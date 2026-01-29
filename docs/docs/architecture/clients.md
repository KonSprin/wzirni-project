# Running Multiple Clients

This guide explains how to run multiple client instances to generate diverse traffic patterns.

## Overview

The project supports running 1-10 client instances simultaneously. Each client:

- Operates independently with unique `CLIENT_ID`
- Randomly selects from 6 different traffic patterns
- Generates varied flow characteristics for analysis
- Routes through PolarProxy independently

## Traffic Patterns

Each client randomly selects behavior patterns with different probabilities:

### Normal User (30% weight)

**Characteristics:**

- Regular browsing and messaging
- Mixed request sizes
- Moderate timing intervals

**Actions:**

- Connection tests
- Send messages
- Retrieve messages
- Search queries
- Small data retrieval

**Sleep Range:** 2-5 seconds

**CICFlowMeter Signature:**

- Medium `flow_iat_mean`
- Variable packet sizes
- Balanced forward/backward packets

### Heavy User (20% weight)

**Characteristics:**

- Large data downloads
- High throughput
- Frequent requests

**Actions:**

- Large dataset retrieval (`/data/large`)
- Many message retrievals (limit=20)
- Complex searches
- Download sessions (3 consecutive large requests)

**Sleep Range:** 1-3 seconds

**CICFlowMeter Signature:**

- High `totlen_bwd_pkts` (>2000 bytes)
- High `flow_byts_s`
- Classified as "Large Data Transfer"

### API Client (15% weight)

**Characteristics:**

- Periodic polling behavior
- Fixed intervals
- Small payloads

**Actions:**

- Rapid health checks
- Small data retrieval
- API polling (10 requests at 2s intervals)

**Sleep Range:** 0.5-2 seconds

**CICFlowMeter Signature:**

- Low `flow_iat_std` (<0.01)
- Constant `flow_iat_mean`
- **Detected as periodic traffic**
- Small packet sizes

### Interactive User (20% weight)

**Characteristics:**

- Human-like behavior
- Variable timing
- Mixed activities

**Actions:**

- Interactive sessions (3-7 random actions)
- Message bursts
- Mixed size uploads (tiny to large)

**Sleep Range:** 3-8 seconds

**CICFlowMeter Signature:**

- High `flow_iat_std`
- Variable packet sizes
- Medium duration flows
- Classified as "Interactive"

### Bursty User (10% weight)

**Characteristics:**

- Periods of intense activity
- Long idle periods
- High variability

**Actions:**

- Rapid message sending (5 messages)
- Streaming simulation (5 large requests)
- Multiple large POST requests

**Sleep Range:** 5-15 seconds

**CICFlowMeter Signature:**

- Very high `flow_iat_std`
- Traffic pattern: "Bursty"
- Large variation in packet timing

### Idle User (5% weight)

**Characteristics:**

- Minimal activity
- Very long pauses
- Only essential checks

**Actions:**

- Occasional health checks
- Rare connection tests

**Sleep Range:** 10-20 seconds

**CICFlowMeter Signature:**

- Very high `flow_iat_mean`
- Very low packet count
- Long flow duration with few packets

## Starting Multiple Clients

### Default (3 Clients)

```bash
docker compose up
```

This starts:

- `client-0` with ID `client_000`
- `client-1` with ID `client_001`
- `client-2` with ID `client_002`

## Monitoring Clients

### View All Client Logs

```bash
docker compose logs -f client-0 client-1 client-2
```

### View Specific Client

```bash
docker compose logs -f client-1
```

### Check Status

```bash
docker compose ps
```

Look for containers named `client-1`, `client-2`, etc.

## Impact on Analysis

### Flow Diversity

With multiple clients, CICFlowMeter will extract:

- **Periodic flows** from API clients (regular 2s intervals)
- **Large transfers** from heavy users (>2000 bytes)
- **Interactive flows** from normal users (varied timing)
- **Bursty patterns** from bursty users (high IAT std)

### Classification Distribution

Expected flow type distribution with 10 clients:

- **Quick Request**: ~20-30% (health checks, small GET)
- **Interactive**: ~15-25% (normal user activity)
- **Large Data**: ~15-20% (heavy user downloads)
- **Bulk Transfer**: ~10-15% (message bursts, streaming)
- **Other**: ~20-30% (mixed patterns)

### Periodic Detection

API clients create clear periodic patterns:

- Regular 2s intervals between requests
- Low IAT variance (<0.01)
- Small, consistent packet sizes
- **Clearly visible in `periodic_traffic.png`**

## Adding More Clients

To add clients beyond 10:

1. Edit `docker-compose.yaml`
2. Copy an existing client block
3. Update name and CLIENT_ID:

    ```yaml
    client-3:
        extends: client-0
        container_name: client-3
        environment:
        - CLIENT_ID=client_003
    client-4:
        extends: client-0
        container_name: client-4
        environment:
        - CLIENT_ID=client_004
    ```

4. Start with updated compose file:

```bash
docker compose -f docker-compose.yaml -f docker-compose.clients.yaml up
```

## Traffic Generation Duration

Recommended capture durations:

- **Quick test**: 1-2 minutes (50-100 flows)
- **Standard analysis**: 3-5 minutes (200-500 flows)
- **Comprehensive**: 10+ minutes (1000+ flows)

## Stopping Clients Selectively

```bash
# Stop specific client
docker compose stop client-1

# Restart specific client
docker compose restart client-1

# Remove specific client
docker compose rm -f client-1
```

## Troubleshooting

### Clients Not Generating Traffic

```bash
# Check if clients are running
docker compose ps

# View client logs
docker compose logs client-1

# Common issues:
# - Server not healthy: docker compose logs server
# - PolarProxy not ready: docker compose logs polarproxy
# - Certificate issues: docker compose logs cert-installer
```

### Identifying Client Traffic in Wireshark

While analyzing decrypted PCAP in Wireshark:

1. Look for username in HTTP requests
2. Each client uses different users (alice, bob, charlie, david, eve)
3. Filter by specific user: `http contains "alice"`

## Example Workflow

```bash
# 1. Start with 7 clients
docker compose -f docker-compose.yaml -f docker-compose.clients.yaml up -d

# 2. Monitor for 3 minutes
docker compose logs -f client-1
# Press Ctrl+C after 3 minutes

# 3. Run analysis
docker compose -f docker-compose.analysis.yaml run --rm cicflowmeter
docker compose -f docker-compose.analysis.yaml run --rm flow-analyzer

# 4. Check results
ls -lh ./cicflowmeter/output/analysis/

# 5. View in Wireshark
# Open http://localhost:3010

# 6. Stop services
docker compose down
```
