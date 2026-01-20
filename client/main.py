import requests
import urllib3
import time

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
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def get_data():
    """Test GET request with data"""
    try:
        response = requests.get(f"{BASE_URL}/data", verify=False)
        print(f"Status: {response.status_code}")
        print(f"Data: {response.json()}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def post_data():
    """Test POST request"""
    try:
        payload = {"name": "test", "value": 42}
        response = requests.post(f"{BASE_URL}/echo", json=payload, verify=False)
        print(f"Status: {response.status_code}")
        print(f"Echo response: {response.json()}\n")
    except Exception as e:
        print(f"Error: {e}\n")


if __name__ == "__main__":
    print("Testing HTTPS client-server communication...\n")
    test_connection()
    get_data()
    post_data()

    while True:
        time.sleep(2)
        get_data()
