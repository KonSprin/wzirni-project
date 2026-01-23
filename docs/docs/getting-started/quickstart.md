# Quick Start Guide

Get up and running with the network traffic analysis environment in minutes.

## Prerequisites

Ensure you have installed:

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

Check your versions:

```bash
docker --version
docker-compose --version
```

## Step 1: Clone the Repository

```bash
git clone https://github.com/KonSprin/wzirni-project.git
cd wzirni-project
```

## Step 2: Start All Services

```bash
docker-compose up --build
```

This command will:

1. Build all Docker images
2. Generate server certificates automatically
3. Start PolarProxy and download its CA certificate
4. Start the client to generate traffic
5. Begin capturing encrypted and decrypted traffic
6. Launch Wireshark GUI
7. Serve documentation

!!! note "First Run"
    The first run takes longer as Docker builds images and generates certificates. Subsequent runs are much faster.

## Step 3: Verify Everything is Running

Check container status:

```bash
docker ps
```

You should see all containers running:

- `server` - Status: healthy
- `client` - Status: up
- `polarproxy` - Status: up
- `sniffer` - Status: up
- `wireshark` - Status: up
- `docs` - Status: up
- `cert-installer` - Status: exited (0)

## Step 4: Access Services

Open these URLs in your browser:

- **Wireshark GUI**: [http://localhost:3010](http://localhost:3010)
- **Documentation**: [http://localhost:8000](http://localhost:8000)
- **Server API**: [https://localhost:8443](https://localhost:8443) (accepts self-signed cert)

## Step 5: View Captured Traffic

### In Wireshark (Browser)

1. Navigate to `http://localhost:3010`
2. Log in with credentials shown in container logs (first run only)
3. Click File → Open
4. Navigate to:
    - `/pcaps/` for decrypted traffic
    - `/encrypted-pcaps/` for encrypted traffic
5. Open any `.pcap` file

### On Your Host

PCAP files are also available directly on your filesystem:

```bash
# Decrypted traffic
ls -lh ./polar-proxy/logs/

# Encrypted traffic
ls -lh ./sniffer/captures/
```

Open with Wireshark desktop application (if installed):

```bash
wireshark ./polar-proxy/logs/proxy-*.pcap
```

## Step 6: Monitor Client Activity

Watch the client generate traffic in real-time:

```bash
docker logs client --follow
```

You should see:

```text
INFO - Starting enhanced HTTPS client-server communication
INFO - === Starting workflow ===
INFO - Connection test - Status: 200
INFO - User registered: alice
INFO - Logged in as alice, token: session_alice_1234...
INFO - Message sent: Hello, this is a test message...
INFO - Search 'network security' - Found 10 results
```

## Step 7: Check Generated Files

Verify files are being created:

```bash
# Server certificates
ls -lh ./server/certs/

# PolarProxy decrypted captures
ls -lh ./polar-proxy/logs/

# Sniffer encrypted captures
ls -lh ./sniffer/captures/

# Client certificates
ls -lh ./client/certs/
```

## Next Steps

Now that everything is running:

1. **Analyze Traffic**: Follow the [Wireshark Analysis Guide](../analysis/wireshark.md)
2. **Understand Architecture**: Read about [container architecture](../architecture/containers.md)

## Common First-Run Issues

### Port Already in Use

If you see `port is already allocated`:

```bash
# Check what's using the port
sudo lsof -i :8443  # or :3010, :8000, etc.

# Either stop the conflicting service or change ports in docker-compose.yaml
```

### Containers Won't Start

Check logs for specific container:

```bash
docker logs server
docker logs polarproxy
docker logs client
```

### No Traffic Being Captured

1. Ensure client is running: `docker ps | grep client`
2. Check client logs: `docker logs client`
3. Verify PolarProxy is running: `docker ps | grep polarproxy`
4. Check sniffer logs: `docker logs sniffer`

### Certificate Issues

If client can't connect due to certificate errors:

```bash
# Remove certificates and restart
docker-compose down -v
rm -rf ./server/certs ./client/certs ./polar-proxy/home
docker-compose up --build
```

## Stopping the Environment

### Stop All Containers

```bash
docker-compose down
```

### Stop and Remove Volumes

This removes all certificates and configuration:

```bash
docker-compose down -v
```

### Clean Everything

Remove all generated files:

```bash
docker-compose down -v
rm -rf ./server/certs ./client/certs ./polar-proxy/logs/* ./polar-proxy/home/* ./sniffer/captures/* ./wireshark_config
```

## Quick Reference

### Useful Commands

```bash
# View all container logs
docker-compose logs

# Follow specific container
docker logs -f client

# Restart specific container
docker-compose restart server

# Rebuild specific container
docker-compose up -d --build client

# Check container health
docker inspect server --format='{{.State.Health.Status}}'
```

### File Locations

| Content | Location |
| --------- | ---------- |
| Decrypted PCAP | `./polar-proxy/logs/` |
| Encrypted PCAP | `./sniffer/captures/` |
| Server certificates | `./server/certs/` |
| PolarProxy CA cert | `./client/certs/` |
| Wireshark config | `./wireshark_config/` |

### Port Mapping

| Service | Port | Purpose |
| --------- | ------ | --------- |
| Server | 8443 | HTTPS API |
| PolarProxy | 10443 | Transparent proxy |
| PolarProxy | 1080 | HTTP CONNECT proxy |
| PolarProxy | 10080 | Cert download |
| Wireshark | 3010 | Web GUI |
| Docs | 8000 | Documentation |

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](../troubleshooting.md)
2. Review container logs: `docker logs <container_name>`
3. Verify all dependencies are met
4. Ensure Docker has sufficient resources allocated
