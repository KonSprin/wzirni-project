from fastapi import FastAPI
import uvicorn

import os
import subprocess

app = FastAPI()

TLS_KEY = "key.pem"
TLS_CERT = "cert.pem"


def generate_certificates():
    """Generate self-signed certificates if they don't exist"""
    if not os.path.exists(TLS_CERT) or not os.path.exists(TLS_KEY):
        print("Generating self-signed certificates...")
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
        print("Certificates generated!")


@app.get("/")
async def root():
    return {"message": "Hello from HTTPS server!"}


@app.get("/data")
async def get_data():
    return {"status": "success", "data": [1, 2, 3, 4, 5]}


@app.post("/echo")
async def echo(data: dict):
    return {"received": data, "echo": True}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    generate_certificates()

    uvicorn.run(
        app, host="0.0.0.0", port=8443, ssl_keyfile=TLS_KEY, ssl_certfile=TLS_CERT
    )
