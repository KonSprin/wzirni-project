# Wireshark Analysis Guide

This guide covers analyzing both decrypted and encrypted traffic using Wireshark.

## Accessing Wireshark

1. Open your browser and navigate to `http://localhost:3010`
2. Log in (default password shown in container logs on first run)
3. Navigate to File → Open
4. Choose between:
    - `/pcaps` - Decrypted traffic from PolarProxy
    - `/encrypted-pcaps` - Encrypted traffic from sniffer

## Analyzing Decrypted Traffic

### What You Can See

When analyzing decrypted PCAP files from PolarProxy, you have full visibility into:

- Complete HTTP requests and responses
- All HTTP headers
- Authentication credentials (username, password)
- Session tokens
- JSON payloads
- API endpoints and query parameters
- User-Agent strings and cookies
- All application data

### Useful Filters

#### General HTTP Traffic

```text
http                                   # Show all HTTP traffic
http.request                           # Only HTTP requests
http.response                          # Only HTTP responses
```

#### Specific HTTP Methods

```text
http.request.method == "POST"          # POST requests
http.request.method == "GET"           # GET requests
http.request.method == "DELETE"        # DELETE requests
```

#### Authentication and Sessions

```text
http.request.uri contains "/login"     # Login requests
http contains "password"               # Packets containing passwords (!)
http contains "session_token"          # Packets with session tokens
http.authorization                     # Authentication headers
```

#### API Endpoints

```text
http.request.uri contains "/messages"  # Message-related requests
http.request.uri contains "/users"     # User-related requests
http.request.uri contains "/search"    # Search queries
http.request.uri contains "/data"      # Data retrieval
```

#### Response Status Codes

```text
http.response.code == 200              # Successful responses
http.response.code == 401              # Unauthorized
http.response.code == 404              # Not found
http.response.code == 409              # Conflict (user exists)
```

#### Content Type

```text
json                                   # Packets containing JSON
http.content_type contains "json"      # JSON content type
```

### Example: Following a User Session

1. Filter for login: `http.request.uri contains "/login"`
2. Find the POST request with credentials
3. Right-click → Follow → HTTP Stream
4. Observe the request body with username/password
5. Note the session_token in the response
6. Use filter: `http contains "SESSION_TOKEN_VALUE"`
7. See all subsequent requests using that session

### Example: Analyzing Message Content

1. Filter: `http.request.uri contains "/messages"`
2. Look for POST requests (sending messages)
3. Examine the request body
4. See message content in plain text
5. Compare with GET requests to see message retrieval

## Analyzing Encrypted Traffic

### What You Can See

When analyzing encrypted PCAP files from the sniffer:

- TLS handshake details
- Client Hello (TLS version, cipher suites, SNI)
- Server Hello (selected cipher, certificate)
- Key exchange messages
- Application Data (encrypted bytes only)
- Packet timing and sizes
- IP addresses and ports
- **No readable content**

### What You Cannot See

- HTTP methods or paths
- Request/response bodies
- Credentials or session tokens
- JSON payloads
- Any application layer data

### Useful Filters

#### TLS Handshake

```text
tls                                     # All TLS traffic
tls.handshake                          # Handshake messages only
tls.handshake.type == 1                # Client Hello
tls.handshake.type == 2                # Server Hello
tls.handshake.type == 11               # Certificate
tls.handshake.type == 16               # Client Key Exchange
```

#### SNI (Server Name Indication)

```text
tls.handshake.extensions_server_name   # See hostname being accessed
```

#### Application Data

```text
tls.record.content_type == 23          # Encrypted application data
```

#### Cipher Suites

```text
tls.handshake.ciphersuite              # Negotiated cipher suite
```

#### Certificate Information

```text
tls.handshake.certificate              # Server certificates
x509sat.CommonName                     # Certificate common name
```

### Example: Identifying Traffic Patterns

1. Filter: `tls.record.content_type == 23`
2. Use Statistics → IO Graph
3. Observe:
    - Regular intervals (polling)
    - Burst patterns (user activity)
    - Packet size distribution

### Example: Timing Analysis

1. Filter: `tls`
2. Note timestamps of handshakes (new connections)
3. Measure intervals between Application Data packets
4. Compare with known client behavior
5. Infer possible user actions from timing

## Comparison Analysis

### Side-by-Side Comparison

1. Open decrypted PCAP in one Wireshark instance
2. Open encrypted PCAP in another (or use File → Merge)
3. Synchronize timestamps
4. Compare the same communication:
    - Decrypted: `POST /users/login HTTP/1.1 ... {"username":"alice","password":"password123"}`
    - Encrypted: `Application Data` with random bytes

### Packet Size Analysis

Both PCAPs show similar packet sizes, but:

**Decrypted**:

- Can correlate size with content
- Large packets → `/data/large` endpoint
- Small packets → health checks or simple GET requests

**Encrypted**:

- Size patterns visible but content unknown
- Can only guess based on size
- Additional TLS overhead visible

### Timing Correlation

1. Use Statistics → Flow Graph on both PCAPs
2. Compare request-response patterns
3. Both show same timing but different content visibility

## Advanced Features

### Statistics

#### IO Graphs

1. Statistics → IO Graph
2. Add filters for different traffic types
3. Visualize traffic over time
4. Compare encrypted vs decrypted patterns

#### Protocol Hierarchy

1. Statistics → Protocol Hierarchy
2. See breakdown of protocols
3. Decrypted shows HTTP, encrypted shows only TLS

#### Conversations

1. Statistics → Conversations
2. View all TCP/IP conversations
3. Sort by packets, bytes, duration
4. Identify most active connections

### Follow Stream

For decrypted traffic:

1. Right-click on packet
2. Follow → HTTP Stream
3. See complete request/response exchange in readable format

For encrypted traffic:

1. Right-click on packet
2. Follow → TCP Stream
3. See encrypted bytes (not readable)

### Export Objects

For decrypted traffic:

1. File → Export Objects → HTTP
2. Extract transmitted files or data
3. Save JSON responses, etc.

## Common Analysis Tasks

### Task 1: Find All Credentials

**Decrypted PCAP**:

```text
http contains "password"
```

Then examine each packet for plaintext credentials.

### Task 2: Identify User Activity

**Decrypted PCAP**:

```text
http.request.method == "POST" && http.request.uri contains "/messages"
```

**Encrypted PCAP**:

Use packet timing and size patterns to guess activity.

### Task 3: Extract Session Tokens

**Decrypted PCAP**:

1. Find login response
2. Extract session_token from JSON
3. Filter: `http contains "SESSION_TOKEN_VALUE"`
4. See all activity for that session

**Encrypted PCAP**:

Cannot extract or identify session tokens.

### Task 4: Analyze Data Transfer Volume

Both PCAPs:

1. Statistics → Capture File Properties
2. Compare average packet size
3. Use IO Graph for throughput over time
4. Filter for large packets: `tcp.len > 1000`

## Tips and Best Practices

### Performance

- Use display filters instead of capture filters when analyzing saved files
- Close unused columns to improve rendering
- Use "Find Packet" for quick navigation
- Enable "Auto Scroll in Live Capture" only when needed

### Analysis Workflow

1. **Start broad**: Look at Protocol Hierarchy and Conversations
2. **Identify patterns**: Use IO Graphs to spot interesting periods
3. **Drill down**: Apply specific filters to examine details
4. **Follow streams**: Use HTTP/TCP stream following for context
5. **Export findings**: Save filtered packets or export objects

### Common Pitfalls

- Don't confuse TLS record size with application payload size
- Remember decrypted traffic has less overhead visible
- Timestamps may differ slightly between PCAPs due to proxy delay
- Not all packets will have Application Data (handshake, acks, etc.)

## Keyboard Shortcuts

- `Ctrl+F`: Find packet
- `Ctrl+G`: Go to packet number
- `Ctrl+→`: Next packet
- `Ctrl+←`: Previous packet
- `Ctrl+W`: Close current capture
- `Ctrl+E`: Export packet dissection
- `Ctrl+Shift+A`: Apply as filter

## Further Reading

- [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/)
- [Display Filter Reference](https://www.wireshark.org/docs/dfref/)
- [TLS Analysis](https://wiki.wireshark.org/TLS)
