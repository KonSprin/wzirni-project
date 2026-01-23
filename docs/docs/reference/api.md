# API Reference

Complete reference for all server API endpoints.

## Base URL

```text
https://localhost:8443
```

!!! note
    Server uses self-signed certificate. Use `-k` flag with curl or accept certificate in browser.

## Authentication

Some endpoints require session tokens obtained via login.

### Session Token Usage

After login, include session token in subsequent requests:

```bash
# Not currently implemented in headers, but stored in server
# Future: Authorization: Bearer <session_token>
```

## Endpoints

### Root

#### GET /

Returns basic server information and available endpoints.

**Request**:

```bash
curl -k https://localhost:8443/
```

**Response**: `200 OK`

```json
{
  "message": "Hello from HTTPS server!",
  "version": "2.0",
  "endpoints": [
    "/health",
    "/users",
    "/login",
    "/messages",
    "/data",
    "/upload",
    "/search"
  ]
}
```

---

### Health Check

#### GET /health

Returns server health status.

**Request**:

```bash
curl -k https://localhost:8443/health
```

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "timestamp": 1706000000.123,
  "uptime_seconds": 3600,
  "active_sessions": 5
}
```

**Fields**:

- `status`: Server status (always "healthy" if responding)
- `timestamp`: Current server time (Unix timestamp)
- `uptime_seconds`: Time since server start
- `active_sessions`: Number of active user sessions

---

### User Management

#### POST /users/register

Register a new user.

**Request**:

```bash
curl -k -X POST https://localhost:8443/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "password123"
  }'
```

**Request Body**:

```json
{
  "username": "string (required)",
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response**: `201 Created` or `200 OK`

```json
{
  "status": "success",
  "message": "User registered successfully",
  "user_id": "alice"
}
```

**Error Response**: `409 Conflict`

```json
{
  "detail": "User already exists"
}
```

---

#### POST /users/login

Authenticate user and receive session token.

**Request**:

```bash
curl -k -X POST https://localhost:8443/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123"
  }'
```

**Request Body**:

```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Response**: `200 OK`

```json
{
  "status": "success",
  "session_token": "session_alice_1706000000",
  "username": "alice",
  "expires_in": 3600
}
```

**Error Response**: `401 Unauthorized`

```json
{
  "detail": "Invalid credentials"
}
```

---

#### GET /users/{username}

Retrieve user information.

**Request**:

```bash
curl -k https://localhost:8443/users/alice
```

**Response**: `200 OK`

```json
{
  "username": "alice",
  "data": {
    "email": "alice@example.com",
    "created_at": 1706000000.123,
    "last_login": 1706001000.456
  }
}
```

**Error Response**: `404 Not Found`

```json
{
  "detail": "User not found"
}
```

---

#### DELETE /users/{username}

Delete a user and their sessions.

**Request**:

```bash
curl -k -X DELETE https://localhost:8443/users/alice
```

**Response**: `200 OK`

```json
{
  "status": "success",
  "message": "User alice deleted"
}
```

**Error Response**: `404 Not Found`

```json
{
  "detail": "User not found"
}
```

---

### Messaging

#### POST /messages

Send a message.

**Request**:

```bash
curl -k -X POST https://localhost:8443/messages \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "content": "Hello, world!",
    "timestamp": 1706000000.123
  }'
```

**Request Body**:

```json
{
  "user_id": "string (required)",
  "content": "string (required)",
  "timestamp": "float (optional)"
}
```

**Response**: `200 OK`

```json
{
  "status": "success",
  "message_id": 42,
  "timestamp": 1706000000.123
}
```

---

#### GET /messages

Retrieve messages with pagination.

**Request**:

```bash
curl -k "https://localhost:8443/messages?limit=10&offset=0"
```

**Query Parameters**:

- `limit`: Maximum messages to return (default: 10)
- `offset`: Number of messages to skip (default: 0)

**Response**: `200 OK`

```json
{
  "messages": [
    {
      "id": 1,
      "user_id": "alice",
      "content": "Hello, world!",
      "timestamp": 1706000000.123
    },
    {
      "id": 2,
      "user_id": "bob",
      "content": "Hi Alice!",
      "timestamp": 1706000010.456
    }
  ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

---

### Data Retrieval

#### GET /data

Retrieve small dataset.

**Request**:

```bash
curl -k https://localhost:8443/data
```

**Response**: `200 OK`

```json
{
  "status": "success",
  "data": [1, 2, 3, 4, 5],
  "metadata": {
    "count": 5,
    "type": "integers",
    "generated_at": 1706000000.123
  }
}
```

---

#### GET /data/large

Retrieve large dataset (100 records).

**Request**:

```bash
curl -k https://localhost:8443/data/large
```

**Response**: `200 OK`

```json
{
  "status": "success",
  "dataset": [
    {
      "id": 0,
      "value": 0,
      "description": "Record number 0 with some additional text to increase payload size",
      "metadata": {
        "created": 1706000000.123,
        "tags": ["tag1", "tag2", "tag3"],
        "nested": {
          "level1": {
            "level2": {
              "level3": "data_0"
            }
          }
        }
      }
    },
    // ... 99 more records
  ],
  "summary": {
    "total_records": 100,
    "generated_at": 1706000000.123
  }
}
```

---

### Search

#### GET /search

Search with query parameters.

**Request**:

```bash
curl -k "https://localhost:8443/search?q=network&category=tech&limit=10"
```

**Query Parameters**:

- `q`: Search query (required)
- `category`: Filter by category (optional)
- `limit`: Max results (default: 10, max: 20)

**Response**: `200 OK`

```json
{
  "query": "network",
  "category": "tech",
  "results": [
    {
      "id": 0,
      "title": "Result 0 matching 'network'",
      "category": "tech",
      "relevance_score": 0.95,
      "snippet": "This is a snippet containing network..."
    },
    {
      "id": 1,
      "title": "Result 1 matching 'network'",
      "category": "tech",
      "relevance_score": 0.90,
      "snippet": "This is a snippet containing network..."
    }
  ],
  "total_found": 10,
  "search_time_ms": 42
}
```

---

### File Upload

#### POST /upload/metadata

Upload file metadata (not actual file).

**Request**:

```bash
curl -k -X POST https://localhost:8443/upload/metadata \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "document.pdf",
    "size": 1024000,
    "content_type": "application/pdf"
  }'
```

**Request Body**:

```json
{
  "filename": "string (required)",
  "size": "integer (required)",
  "content_type": "string (required)"
}
```

**Response**: `200 OK`

```json
{
  "status": "success",
  "received": {
    "filename": "document.pdf",
    "size": 1024000,
    "content_type": "application/pdf"
  },
  "upload_id": "upload_1706000000"
}
```

---

### Testing

#### POST /echo

Echo back request data for testing.

**Request**:

```bash
curl -k -X POST https://localhost:8443/echo \
  -H "Content-Type: application/json" \
  -d '{
    "test": "value",
    "number": 42
  }'
```

**Request Body**: Any valid JSON

**Response**: `200 OK`

```json
{
  "received": {
    "test": "value",
    "number": 42
  },
  "echo": true,
  "timestamp": 1706000000.123,
  "server_info": {
    "version": "2.0",
    "processing_time_ms": 5
  }
}
```

---

## Error Responses

All endpoints may return standard HTTP error codes:

### 400 Bad Request

```json
{
  "detail": "Invalid request format"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid credentials"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 409 Conflict

```json
{
  "detail": "Resource already exists"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## Usage Examples

### Complete User Workflow

```bash
# 1. Register user
curl -k -X POST https://localhost:8443/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "secret"}'

# 2. Login
curl -k -X POST https://localhost:8443/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}'
# Save session_token from response

# 3. Send message
curl -k -X POST https://localhost:8443/messages \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "content": "Hello!"}'

# 4. Get messages
curl -k "https://localhost:8443/messages?limit=5"

# 5. Search
curl -k "https://localhost:8443/search?q=test&category=tech"

# 6. Get user info
curl -k https://localhost:8443/users/alice
```

### Python Example

```python
import requests
import urllib3

# Disable SSL warnings for self-signed cert
urllib3.disable_warnings()

BASE_URL = "https://localhost:8443"

# Register
response = requests.post(
    f"{BASE_URL}/users/register",
    json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret"
    },
    verify=False
)
print(response.json())

# Login
response = requests.post(
    f"{BASE_URL}/users/login",
    json={"username": "alice", "password": "secret"},
    verify=False
)
session_token = response.json()["session_token"]
print(f"Session token: {session_token}")

# Send message
response = requests.post(
    f"{BASE_URL}/messages",
    json={
        "user_id": "alice",
        "content": "Hello from Python!"
    },
    verify=False
)
print(response.json())
```

---

## Rate Limiting

Currently not implemented. All endpoints accept unlimited requests.

## Data Persistence

All data is stored in-memory and lost on server restart. This is intentional for demo purposes.
