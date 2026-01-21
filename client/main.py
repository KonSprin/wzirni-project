import requests
import urllib3
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

logging.getLogger("urllib3").setLevel(logging.INFO)

# Disable SSL warnings for self-signed certificates (for development only!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://server:8443"


def test_connection():
    """Test basic GET request"""
    try:
        response = requests.get(
            f"{BASE_URL}/",
            verify=False,  # Skip SSL verification for self-signed certs
        )
        logger.info(f"Connection test - Status: {response.status_code}")
        logger.info(f"Connection test - Response: {response.json()}")
    except Exception as e:
        logger.error(f"Connection test failed: {e}", exc_info=True)


def get_data():
    """Test GET request with data"""
    try:
        response = requests.get(f"{BASE_URL}/data", verify=False)
        logger.info(f"GET /data - Status: {response.status_code}")
        logger.debug(f"GET /data - Response: {response.json()}")
    except Exception as e:
        logger.error(f"GET /data failed: {e}", exc_info=True)


def post_data():
    """Test POST request"""
    try:
        payload = {"name": "test", "value": 42}
        response = requests.post(f"{BASE_URL}/echo", json=payload, verify=False)
        logger.info(f"POST /echo - Status: {response.status_code}")
        logger.debug(f"POST /echo - Response: {response.json()}")
    except Exception as e:
        logger.error(f"POST /echo failed: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("Starting HTTPS client-server communication tests")
    test_connection()
    get_data()
    post_data()

    logger.info("Entering polling loop - requesting /data every 5 seconds")
    while True:
        time.sleep(5)
        get_data()
