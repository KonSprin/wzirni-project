import requests
import urllib3
import time
import logging
import random
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://server:8443"
session_token = None
current_user = None


def test_connection():
    """Test basic GET request"""
    try:
        response = requests.get(f"{BASE_URL}/", verify=False)
        logger.info(f"Connection test - Status: {response.status_code}")
        logger.info(f"Available endpoints: {response.json().get('endpoints', [])}")
    except Exception as e:
        logger.error(f"Connection test failed: {e}")


def register_user(username: str, email: str, password: str):
    """Register a new user"""
    try:
        payload = {"username": username, "email": email, "password": password}
        response = requests.post(
            f"{BASE_URL}/users/register", json=payload, verify=False
        )

        if response.status_code == 201 or response.status_code == 200:
            logger.info(f"User registered: {username}")
            return True
        elif response.status_code == 409:
            logger.info(f"User {username} already exists")
            return True
        else:
            logger.error(f"Registration failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return False


def login_user(username: str, password: str):
    """Login user and get session token"""
    global session_token, current_user

    try:
        payload = {"username": username, "password": password}
        response = requests.post(f"{BASE_URL}/users/login", json=payload, verify=False)

        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            current_user = username
            logger.info(f"Logged in as {username}, token: {session_token[:20]}...")
            return True
        else:
            logger.error(f"Login failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return False


def get_user_info(username: str):
    """Get user information"""
    try:
        response = requests.get(f"{BASE_URL}/users/{username}", verify=False)

        if response.status_code == 200:
            logger.info(f"User info retrieved: {response.json()}")
        else:
            logger.warning(f"Failed to get user info: {response.status_code}")
    except Exception as e:
        logger.error(f"Get user info failed: {e}")


def send_message(content: str):
    """Send a message"""
    if not current_user:
        logger.warning("Cannot send message: not logged in")
        return

    try:
        payload = {
            "user_id": current_user,
            "content": content,
            "timestamp": time.time(),
        }
        response = requests.post(f"{BASE_URL}/messages", json=payload, verify=False)

        if response.status_code == 200:
            logger.info(f"Message sent: {content[:50]}...")
        else:
            logger.error(f"Send message failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Send message failed: {e}")


def get_messages():
    """Retrieve messages"""
    try:
        response = requests.get(
            f"{BASE_URL}/messages", params={"limit": 5, "offset": 0}, verify=False
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Retrieved {len(data.get('messages', []))} messages")
        else:
            logger.error(f"Get messages failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Get messages failed: {e}")


def get_data():
    """Test GET request with data"""
    try:
        response = requests.get(f"{BASE_URL}/data", verify=False)

        if response.status_code == 200:
            logger.info(
                f"GET /data - Retrieved {len(response.json().get('data', []))} items"
            )
    except Exception as e:
        logger.error(f"GET /data failed: {e}")


def get_large_data():
    """Get large dataset"""
    try:
        response = requests.get(f"{BASE_URL}/data/large", verify=False)

        if response.status_code == 200:
            data = response.json()
            logger.info(
                f"GET /data/large - Retrieved {len(data.get('dataset', []))} records"
            )
    except Exception as e:
        logger.error(f"GET /data/large failed: {e}")


def search_query(query: str):
    """Perform search"""
    try:
        params = {
            "q": query,
            "category": random.choice(["tech", "science", "news", None]),
            "limit": random.randint(5, 15),
        }
        response = requests.get(f"{BASE_URL}/search", params=params, verify=False)

        if response.status_code == 200:
            data = response.json()
            logger.info(
                f"Search '{query}' - Found {data.get('total_found', 0)} results"
            )
    except Exception as e:
        logger.error(f"Search failed: {e}")


def upload_file_metadata():
    """Upload file metadata"""
    try:
        payload = {
            "filename": f"document_{random.randint(1, 100)}.pdf",
            "size": random.randint(1024, 1024000),
            "content_type": "application/pdf",
        }
        response = requests.post(
            f"{BASE_URL}/upload/metadata", json=payload, verify=False
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"File metadata uploaded: {data.get('upload_id')}")
    except Exception as e:
        logger.error(f"Upload metadata failed: {e}")


def post_echo():
    """Test POST request"""
    try:
        payload = {
            "name": "test",
            "value": random.randint(1, 100),
            "timestamp": time.time(),
            "data": {"nested": "value", "array": [1, 2, 3, 4, 5]},
        }
        response = requests.post(f"{BASE_URL}/echo", json=payload, verify=False)

        if response.status_code == 200:
            logger.info("POST /echo - Success")
    except Exception as e:
        logger.error(f"POST /echo failed: {e}")


def run_workflow():
    """Run a complete workflow simulating real usage"""
    users = [
        ("alice", "alice@example.com", "password123"),
        ("bob", "bob@example.com", "secret456"),
        ("charlie", "charlie@example.com", "pass789"),
    ]

    messages = [
        "Hello, this is a test message",
        "Analyzing network traffic patterns",
        "HTTPS communication is encrypted by default",
        "PolarProxy helps decrypt TLS traffic for analysis",
        "Wireshark is a powerful packet analyzer",
        "This message contains some longer text to create varied packet sizes and test how the system handles different payload lengths",
        "Short msg",
        "Medium length message with some additional context",
        json.dumps({"type": "json", "data": [1, 2, 3, 4, 5]}),
    ]

    search_queries = [
        "network security",
        "encryption",
        "packet analysis",
        "TLS protocols",
        "cybersecurity",
        "data privacy",
    ]

    # Initial connection test
    logger.info("=== Starting workflow ===")
    test_connection()
    time.sleep(1)

    # Register and login
    user = random.choice(users)
    username, email, password = user

    register_user(username, email, password)
    time.sleep(0.5)

    login_user(username, password)
    time.sleep(0.5)

    get_user_info(username)
    time.sleep(0.5)

    # Main activity loop
    for cycle in range(3):
        logger.info(f"=== Activity cycle {cycle + 1} ===")

        # Send some messages
        for _ in range(random.randint(1, 3)):
            send_message(random.choice(messages))
            time.sleep(random.uniform(0.3, 0.8))

        # Check messages
        get_messages()
        time.sleep(0.5)

        # Perform searches
        search_query(random.choice(search_queries))
        time.sleep(random.uniform(0.5, 1.0))

        # Get data
        if random.random() > 0.5:
            get_data()
        else:
            get_large_data()
        time.sleep(0.5)

        # Upload metadata
        if random.random() > 0.3:
            upload_file_metadata()
            time.sleep(0.5)

        # Echo test
        post_echo()
        time.sleep(1)


if __name__ == "__main__":
    logger.info("Starting enhanced HTTPS client-server communication")

    # Initial workflow
    run_workflow()

    logger.info("Entering polling loop with varied traffic patterns")

    # Continuous varied traffic
    cycle_count = 0
    while True:
        cycle_count += 1

        if cycle_count % 5 == 0:
            logger.info(f"=== Polling cycle {cycle_count} ===")
            run_workflow()
        else:
            # Light polling
            action = random.choice(
                [
                    get_data,
                    get_messages,
                    lambda: search_query(random.choice(["update", "info", "data"])),
                    post_echo,
                ]
            )
            action()

        time.sleep(random.uniform(3, 7))
