from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import subprocess
import time
from typing import Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

app = FastAPI()

CERTS_DIR = "/app/certs"
TLS_KEY = os.path.join(CERTS_DIR, "key.pem")
TLS_CERT = os.path.join(CERTS_DIR, "cert.pem")

# In-memory storage for demo purposes
users_db = {}
sessions_db = {}
messages_db = []


class User(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class Message(BaseModel):
    user_id: str
    content: str
    timestamp: Optional[float] = None


class FileMetadata(BaseModel):
    filename: str
    size: int
    content_type: str


def generate_certificates():
    """Generate self-signed certificates if they don't exist"""
    # Create certs directory if it doesn't exist
    os.makedirs(CERTS_DIR, exist_ok=True)

    if not os.path.exists(TLS_CERT) or not os.path.exists(TLS_KEY):
        logger.info("Generating self-signed certificates...")
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:4096",
                "-nodes",
                "-out",
                TLS_CERT,
                "-keyout",
                TLS_KEY,
                "-days",
                "365",
                "-subj",
                "/CN=localhost",
            ]
        )
        logger.info(f"Certificates generated in {CERTS_DIR}/ directory!")
    else:
        logger.info(f"Using existing certificates from {CERTS_DIR}/ directory")


@app.get("/")
async def root():
    return {
        "message": "Hello from HTTPS server!",
        "version": "2.0",
        "endpoints": [
            "/health",
            "/users",
            "/login",
            "/messages",
            "/data",
            "/upload",
            "/search",
        ],
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime_seconds": int(time.time()),
        "active_sessions": len(sessions_db),
    }


@app.post("/users/register")
async def register_user(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=409, detail="User already exists")

    users_db[user.username] = {
        "email": user.email,
        "password": user.password,
        "created_at": time.time(),
        "last_login": None,
    }

    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": user.username,
    }


@app.post("/users/login")
async def login(credentials: LoginRequest):
    if credentials.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = users_db[credentials.username]
    if user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create session token
    session_token = f"session_{credentials.username}_{int(time.time())}"
    sessions_db[session_token] = {
        "username": credentials.username,
        "created_at": time.time(),
    }

    user["last_login"] = time.time()

    return {
        "status": "success",
        "session_token": session_token,
        "username": credentials.username,
        "expires_in": 3600,
    }


@app.get("/users/{username}")
async def get_user(username: str):
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = users_db[username].copy()
    user_data.pop("password", None)  # Don't expose password

    return {"username": username, "data": user_data}


@app.post("/messages")
async def send_message(message: Message):
    message_data = {
        "id": len(messages_db) + 1,
        "user_id": message.user_id,
        "content": message.content,
        "timestamp": message.timestamp or time.time(),
    }
    messages_db.append(message_data)

    return {
        "status": "success",
        "message_id": message_data["id"],
        "timestamp": message_data["timestamp"],
    }


@app.get("/messages")
async def get_messages(limit: int = 10, offset: int = 0):
    return {
        "messages": messages_db[offset : offset + limit],
        "total": len(messages_db),
        "limit": limit,
        "offset": offset,
    }


@app.get("/data")
async def get_data():
    return {
        "status": "success",
        "data": [1, 2, 3, 4, 5],
        "metadata": {"count": 5, "type": "integers", "generated_at": time.time()},
    }


@app.get("/data/large")
async def get_large_data():
    # Generate larger payload for bandwidth testing
    return {
        "status": "success",
        "dataset": [
            {
                "id": i,
                "value": i * 2,
                "description": f"Record number {i} with some additional text to increase payload size",
                "metadata": {
                    "created": time.time(),
                    "tags": ["tag1", "tag2", "tag3"],
                    "nested": {"level1": {"level2": {"level3": f"data_{i}"}}},
                },
            }
            for i in range(100)
        ],
        "summary": {"total_records": 100, "generated_at": time.time()},
    }


@app.get("/search")
async def search(q: str, category: Optional[str] = None, limit: int = 10):
    # Simulate search functionality
    results = [
        {
            "id": i,
            "title": f"Result {i} matching '{q}'",
            "category": category or "general",
            "relevance_score": 0.95 - (i * 0.05),
            "snippet": f"This is a snippet containing {q}...",
        }
        for i in range(min(limit, 20))
    ]

    return {
        "query": q,
        "category": category,
        "results": results,
        "total_found": len(results),
        "search_time_ms": 42,
    }


@app.post("/upload/metadata")
async def upload_metadata(metadata: FileMetadata):
    return {
        "status": "success",
        "received": metadata.dict(),
        "upload_id": f"upload_{int(time.time())}",
    }


@app.post("/echo")
async def echo(data: dict):
    return {
        "received": data,
        "echo": True,
        "timestamp": time.time(),
        "server_info": {"version": "2.0", "processing_time_ms": 5},
    }


@app.delete("/users/{username}")
async def delete_user(username: str):
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    del users_db[username]

    # Clean up sessions
    sessions_to_remove = [
        token
        for token, session in sessions_db.items()
        if session["username"] == username
    ]
    for token in sessions_to_remove:
        del sessions_db[token]

    return {"status": "success", "message": f"User {username} deleted"}


if __name__ == "__main__":
    generate_certificates()

    uvicorn.run(
        app, host="0.0.0.0", port=8443, ssl_keyfile=TLS_KEY, ssl_certfile=TLS_CERT
    )
