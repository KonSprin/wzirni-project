# Troubleshooting Guide

Common issues and their solutions.

## Container Issues

### Server Won't Start

**Symptoms**: Server container exits immediately or shows errors in logs

**Solutions**:

1. Check if certificates can be generated:

    ```bash
    docker logs server
    ```

2. Verify OpenSSL is available in container:

    ```bash
    docker exec server which openssl
    ```

3. Manually create certificate directory:

    ```bash
    mkdir -p ./server/certs
    chmod 755 ./server/certs
    ```

4. Remove old certificates and restart:

    ```bash
    rm -rf ./server/certs/*
    docker-compose restart server
    ```

### Client Can't Connect to Server

**Symptoms**: Client logs show connection errors or SSL errors

**Solutions**:

1. Verify server is healthy:

    ```bash
    docker ps  # Server should show "healthy"
    docker logs server
    ```

2. Check if PolarProxy is running:

    ```bash
    docker ps | grep polarproxy
    ```

3. Verify certificate installation:

    ```bash
    docker logs cert-installer
    docker exec client ls -la /usr/local/share/ca-certificates/
    ```

4. Test direct connection to server:

    ```bash
    docker exec client curl -k https://server:8443/health
    ```

5. Full reset:

    ```bash
    docker-compose down -v
    rm -rf ./client/certs ./server/certs
    docker-compose up --build
    ```

### PolarProxy Not Capturing Traffic

**Symptoms**: No PCAP files in `./polar-proxy/logs/`

**Solutions**:

1. Check PolarProxy logs:

  ```bash
  docker logs polarproxy
  ```

1. Verify directory permissions:

```bash
ls -la ./polar-proxy/logs/
chmod 755 ./polar-proxy/logs/
```

1. Ensure client is routing through proxy:

```bash
docker exec client env | grep PROXY
# Should show: HTTPS_PROXY=http://polarproxy:1080
```

1. Test PolarProxy connectivity:

```bash
docker exec client curl http://polarproxy:10080
```

1. Restart with verbose logging:

```bash
docker-compose restart polarproxy
docker logs -f polarproxy
```

### Sniffer Not Capturing

**Symptoms**: No files in `./sniffer/captures/` or file size not increasing

**Solutions**:

1. Check sniffer logs:

```bash
docker logs sniffer
```

1. Verify network mode:

```bash
docker inspect sniffer | grep NetworkMode
# Should show: "service:server"
```

1. Check if traffic is flowing:

```bash
docker exec client curl -k https://server:8443/
docker logs sniffer
```

1. Verify capabilities:

```bash
docker inspect sniffer | grep -A5 CapAdd
# Should show NET_ADMIN and NET_RAW
```

1. Recreate with proper permissions:

```bash
docker-compose down
rm -rf ./sniffer/captures/*
docker-compose up -d
```

### Cert-installer Fails

**Symptoms**: Cert-installer shows error or doesn't complete

**Solutions**:

1. Check logs:

```bash
docker logs cert-installer
```

1. Verify PolarProxy is running first:

```bash
docker ps | grep polarproxy
```

1. Test certificate endpoint:

```bash
docker run --rm --network wzirni-project_app_network alpine \
  sh -c "apk add curl && curl -I http://polarproxy:10080/polarproxy.cer"
```

1. Manual certificate download:

```bash
docker run --rm --network wzirni-project_app_network -v ./client/certs:/certs alpine \
  sh -c "apk add curl && curl -o /certs/polarproxy.crt http://polarproxy:10080/polarproxy.cer"
```

## Wireshark Issues

### Can't Access Wireshark GUI

**Symptoms**: Browser shows connection refused at `localhost:3010`

**Solutions**:

1. Verify container is running:

```bash
docker ps | grep wireshark
```

1. Check logs for errors:

```bash
docker logs wireshark
```

1. Try alternate port mapping:

```yaml
# In docker-compose.yaml
ports:
  - 8080:3000  # Change from 3010:3000
```

1. Access via container IP:

```bash
docker inspect wireshark | grep IPAddress
# Use http://<IP>:3000
```

### No PCAP Files Visible in Wireshark

**Symptoms**: Directories `/pcaps` or `/encrypted-pcaps` are empty

**Solutions**:

1. Verify files exist on host:

```bash
ls -lh ./polar-proxy/logs/
ls -lh ./sniffer/captures/
```

1. Check volume mounts:

```bash
docker inspect wireshark | grep -A10 Mounts
```

1. Generate traffic to create files:

```bash
docker logs client --follow
# Wait for some activity
```

1. Restart Wireshark:

```bash
docker-compose restart wireshark
```

1. Refresh file browser in Wireshark GUI

### Wireshark is Slow or Unresponsive

**Solutions**:

1. Increase shared memory:

```yaml
# In docker-compose.yaml
shm_size: "2gb"  # Increase from 1gb
```

1. Close unused files in Wireshark

2. Reduce PCAP file size by rotating:

```bash
# Manually rotate large files
cd ./polar-proxy/logs
mv proxy-*.pcap archive/
```

## Certificate Issues

### Self-Signed Certificate Errors

**Symptoms**: Browser or client complains about certificate

**Solutions**:

This is expected behavior. For the server:

```bash
# Access with -k flag
curl -k https://localhost:8443/

# In browser: click "Advanced" → "Proceed anyway"
```

For the client, ensure PolarProxy CA is installed:

```bash
docker exec client cat /usr/local/share/ca-certificates/polarproxy.crt
```

### Certificate Not Trusted by Client

**Symptoms**: Client shows SSL verification errors

**Solutions**:

1. Check if cert-installer completed:

```bash
docker logs cert-installer
```

1. Verify certificate exists:

```bash
docker exec client ls -la /usr/local/share/ca-certificates/
```

1. Re-run update-ca-certificates:

```bash
docker exec client update-ca-certificates
```

1. Full certificate reset:

```bash
docker-compose down -v
rm -rf ./client/certs ./polar-proxy/home
docker-compose up --build
```

## Network Issues

### Containers Can't Communicate

**Symptoms**: Client can't reach server or PolarProxy

**Solutions**:

1. Verify all containers are on same network:

```bash
docker network inspect wzirni-project_app_network
```

1. Test connectivity:

```bash
docker exec client ping -c 3 server
docker exec client ping -c 3 polarproxy
```

1. Check DNS resolution:

```bash
docker exec client nslookup server
docker exec client nslookup polarproxy
```

1. Recreate network:

```bash
docker-compose down
docker network rm wzirni-project_app_network
docker-compose up
```

### Port Conflicts

**Symptoms**: "port is already allocated" error

**Solutions**:

1. Find what's using the port:

```bash
sudo lsof -i :8443
sudo lsof -i :3010
sudo lsof -i :8000
```

1. Stop conflicting service or change port mapping in `docker-compose.yaml`

2. Use different ports:

```yaml
ports:
  - 8444:8443  # Change external port
```

## Traffic Analysis Issues

### No Traffic in PCAP Files

**Symptoms**: PCAP files exist but are empty or very small

**Solutions**:

1. Verify client is actually running:

```bash
docker logs client --tail 50
```

1. Check if client is generating traffic:

```bash
docker logs client --follow
# Should see regular activity
```

1. Manually trigger traffic:

```bash
docker exec client python -c "import requests; requests.get('https://server:8443/', verify=False)"
```

1. Restart client:

```bash
docker-compose restart client
```

### Can't See Decrypted HTTP in Wireshark

**Symptoms**: PolarProxy PCAP still shows encrypted data

**Solutions**:

1. Verify you're opening the correct file:
    - `/pcaps/` = decrypted (from PolarProxy)
    - `/encrypted-pcaps/` = encrypted (from sniffer)

2. Check PolarProxy is actually decrypting:

```bash
docker logs polarproxy | grep -i decrypt
```

1. Verify HTTP CONNECT mode is enabled:

```bash
docker logs polarproxy | grep "HTTP CONNECT"
```

1. Check if server is actually using HTTPS:

```bash
docker logs server | grep 443
```

### Traffic Timestamps Don't Match

**Symptoms**: Decrypted and encrypted PCAPs show different timestamps

**Solutions**:

This is expected due to proxy overhead. Timestamps will differ by a few milliseconds.

For better correlation:

1. Use relative timing in Wireshark:
    - View → Time Display Format → Seconds Since Previous Captured Packet

2. Match by packet size and patterns rather than exact timestamps

## Performance Issues

### High CPU Usage

**Symptoms**: Docker consuming excessive CPU

**Solutions**:

1. Reduce client traffic frequency:

```python
# In client/main.py, increase sleep time
time.sleep(random.uniform(5, 10))  # Instead of (3, 7)
```

1. Stop Wireshark container when not needed:

```bash
docker-compose stop wireshark
```

1. Limit PolarProxy verbosity:

```yaml
# In docker-compose.yaml, remove -v flag
command: -p 10443,80,443 -o /var/log/PolarProxy/ --certhttp 10080 --httpconnect 1080 --leafcert sign
```

### High Disk Usage

**Symptoms**: PCAP files growing too large

**Solutions**:

1. Rotate PCAP files regularly:

```bash
# Create archive directory
mkdir -p ./polar-proxy/logs/archive
mv ./polar-proxy/logs/proxy-*.pcap ./polar-proxy/logs/archive/
```

1. Use tcpdump rotation in sniffer:

```yaml
# In docker-compose.yaml, modify sniffer command
command: >
  sh -c "
  tcpdump -i any -C 100 -W 5 -w /captures/encrypted-%Y%m%d-%H%M%S.pcap 'tcp port 8443'
  "
# -C 100: rotate at 100MB
# -W 5: keep only 5 files
```

1. Periodically clean old files:

```bash
find ./polar-proxy/logs -name "*.pcap" -mtime +7 -delete
find ./sniffer/captures -name "*.pcap" -mtime +7 -delete
```

## Documentation Issues

### Can't Access Documentation

**Symptoms**: `http://localhost:8000` doesn't load

**Solutions**:

1. Check docs container:

```bash
docker ps | grep docs
docker logs docs
```

1. Verify port is available:

```bash
sudo lsof -i :8000
```

1. Rebuild docs container:

```bash
docker-compose up -d --build docs
```

1. Access via container IP:

```bash
docker inspect docs | grep IPAddress
```

## Complete Reset

If all else fails, perform a complete reset:

```bash
# Stop everything
docker-compose down -v

# Remove all generated files
rm -rf ./server/certs
rm -rf ./client/certs
rm -rf ./polar-proxy/logs/*
rm -rf ./polar-proxy/home/*
rm -rf ./sniffer/captures/*
rm -rf ./wireshark_config

# Remove Docker images
docker-compose rm -f
docker image prune -a

# Rebuild and restart
docker-compose up --build
```

## Getting Detailed Logs

For debugging, enable verbose logging:

```bash
# All containers
docker-compose logs --follow

# Specific container with timestamps
docker logs --follow --timestamps server

# Last N lines
docker logs --tail 100 client

# Since specific time
docker logs --since 2024-01-23T10:00:00 polarproxy
```

## Reporting Issues

When reporting issues, include:

1. Output of `docker --version` and `docker-compose --version`
2. Output of `docker ps -a`
3. Relevant container logs: `docker logs <container_name>`
4. Your `docker-compose.yaml` if modified
5. Steps to reproduce the issue
