import requests
import urllib3
import time
import logging
import random
import os

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
SESSION_TOKEN = None
CURRENT_USER = None

# Get client instance ID from environment or generate random one
CLIENT_ID = os.getenv("CLIENT_ID", f"client_{random.randint(1000, 9999)}")


def test_connection():
    """Test basic GET request - creates quick, small flows"""
    try:
        response = requests.get(f"{BASE_URL}/", verify=False)
        logger.info(f"[{CLIENT_ID}] Connection test - Status: {response.status_code}")
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Connection test failed: {e}")


def register_user(username: str, email: str, password: str):
    """Register a new user - small POST request"""
    try:
        payload = {"username": username, "email": email, "password": password}
        response = requests.post(
            f"{BASE_URL}/users/register", json=payload, verify=False
        )

        if response.status_code == 201 or response.status_code == 200:
            logger.info(f"[{CLIENT_ID}] User registered: {username}")
            return True
        elif response.status_code == 409:
            logger.info(f"[{CLIENT_ID}] User {username} already exists")
            return True
        else:
            logger.error(f"[{CLIENT_ID}] Registration failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Registration failed: {e}")
        return False


def login_user(username: str, password: str):
    """Login user and get session token - interactive flow"""
    global SESSION_TOKEN, CURRENT_USER

    try:
        payload = {"username": username, "password": password}
        response = requests.post(f"{BASE_URL}/users/login", json=payload, verify=False)

        if response.status_code == 200:
            data = response.json()
            SESSION_TOKEN = data.get("SESSION_TOKEN")
            CURRENT_USER = username
            logger.info(f"[{CLIENT_ID}] Logged in as {username}")
            return True
        else:
            logger.error(f"[{CLIENT_ID}] Login failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Login failed: {e}")
        return False


def get_user_info(username: str | None):
    """Get user information - small GET request"""
    if username is None:
        logger.warning(f"[{CLIENT_ID}] Cannot get user information: not logged in")
        return

    try:
        response = requests.get(f"{BASE_URL}/users/{username}", verify=False)

        if response.status_code == 200:
            logger.info(f"[{CLIENT_ID}] User info retrieved for {username}")
        else:
            logger.warning(
                f"[{CLIENT_ID}] Failed to get user info: {response.status_code}"
            )
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Get user info failed: {e}")


def send_message(content: str):
    """Send a message - variable size POST"""
    if not CURRENT_USER:
        logger.warning(f"[{CLIENT_ID}] Cannot send message: not logged in")
        return

    try:
        payload = {
            "user_id": CURRENT_USER,
            "content": content,
            "timestamp": time.time(),
        }
        response = requests.post(f"{BASE_URL}/messages", json=payload, verify=False)

        if response.status_code == 200:
            logger.info(f"[{CLIENT_ID}] Message sent ({len(content)} chars)")
        else:
            logger.error(f"[{CLIENT_ID}] Send message failed: {response.status_code}")
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Send message failed: {e}")


def get_messages(limit: int = 5):
    """Retrieve messages - medium response size"""
    try:
        response = requests.get(
            f"{BASE_URL}/messages", params={"limit": limit, "offset": 0}, verify=False
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(
                f"[{CLIENT_ID}] Retrieved {len(data.get('messages', []))} messages"
            )
        else:
            logger.error(f"[{CLIENT_ID}] Get messages failed: {response.status_code}")
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Get messages failed: {e}")


def get_data():
    """Test GET request with data - small dataset"""
    try:
        response = requests.get(f"{BASE_URL}/data", verify=False)

        if response.status_code == 200:
            logger.info(f"[{CLIENT_ID}] GET /data - Small dataset retrieved")
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] GET /data failed: {e}")


def get_large_data():
    """Get large dataset - creates large transfer flows"""
    try:
        response = requests.get(f"{BASE_URL}/data/large", verify=False)

        if response.status_code == 200:
            data = response.json()
            logger.info(
                f"[{CLIENT_ID}] GET /data/large - Retrieved {len(data.get('dataset', []))} records"
            )
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] GET /data/large failed: {e}")


def search_query(query: str):
    """Perform search - medium interactive flow"""
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
                f"[{CLIENT_ID}] Search '{query}' - Found {data.get('total_found', 0)} results"
            )
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Search failed: {e}")


def upload_file_metadata():
    """Upload file metadata - small POST"""
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
            logger.info(f"[{CLIENT_ID}] File metadata uploaded")
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Upload metadata failed: {e}")


def post_echo(size: str = "small"):
    """Test POST request with variable payload sizes"""
    try:
        if size == "tiny":
            payload = {"ping": "pong"}
        elif size == "small":
            payload = {
                "name": "test",
                "value": random.randint(1, 100),
                "timestamp": time.time(),
            }
        elif size == "medium":
            payload = {
                "name": "test",
                "value": random.randint(1, 100),
                "timestamp": time.time(),
                "data": {"nested": "value", "array": list(range(20))},
                "metadata": {"client": CLIENT_ID, "iteration": random.randint(1, 1000)},
            }
        else:  # large
            payload = {
                "name": "test",
                "value": random.randint(1, 100),
                "timestamp": time.time(),
                "data": {"nested": "value", "array": list(range(100))},
                "metadata": {
                    "client": CLIENT_ID,
                    "iteration": random.randint(1, 1000),
                    "description": "A" * 500,  # Large text field
                },
                "extra_fields": [{"id": i, "data": f"field_{i}"} for i in range(50)],
            }

        response = requests.post(f"{BASE_URL}/echo", json=payload, verify=False)

        if response.status_code == 200:
            logger.info(f"[{CLIENT_ID}] POST /echo ({size}) - Success")
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] POST /echo failed: {e}")


def health_check_polling():
    """Rapid health checks - creates periodic polling pattern"""
    try:
        response = requests.get(f"{BASE_URL}/health", verify=False)
        if response.status_code == 200:
            logger.info(f"[{CLIENT_ID}] Health check - OK")
    except Exception as e:
        logger.error(f"[{CLIENT_ID}] Health check failed: {e}")


def bulk_message_send():
    """Send multiple messages rapidly - creates burst pattern"""
    messages = [
        "Quick update",
        "Status report",
        "Task completed",
        "New notification",
        "Alert message",
    ]

    for msg in messages:
        send_message(msg)
        time.sleep(random.uniform(0.1, 0.3))  # Rapid succession


def streaming_simulation():
    """Simulate streaming behavior - steady high throughput"""
    logger.info(f"[{CLIENT_ID}] Starting streaming simulation")
    for i in range(5):
        get_large_data()
        time.sleep(random.uniform(0.5, 1.0))  # Consistent interval


def interactive_session():
    """Simulate interactive user session - variable timing"""
    actions = [
        lambda: send_message("User typing..."),
        lambda: get_messages(3),
        lambda: search_query("update"),
        lambda: get_user_info(CURRENT_USER),
        lambda: post_echo("small"),
    ]

    for _ in range(random.randint(3, 7)):
        action = random.choice(actions)
        action()
        time.sleep(random.uniform(1, 3))  # Human-like pauses


def api_polling_pattern():
    """Simulate API polling - regular intervals"""
    logger.info(f"[{CLIENT_ID}] API polling pattern")
    for _ in range(10):
        get_data()
        time.sleep(2.0)  # Fixed interval for periodic detection


def download_heavy_session():
    """Simulate heavy download activity - large transfers"""
    logger.info(f"[{CLIENT_ID}] Heavy download session")
    for _ in range(3):
        get_large_data()
        time.sleep(random.uniform(0.2, 0.5))


def mixed_size_uploads():
    """Upload different sized payloads - size variability"""
    sizes = ["tiny", "small", "medium", "large"]
    for size in sizes:
        post_echo(size)
        time.sleep(random.uniform(0.5, 1.5))


# Traffic pattern definitions
TRAFFIC_PATTERNS = {
    "normal_user": {
        "weight": 30,
        "actions": [
            (test_connection, 0.3),
            (lambda: send_message("Normal message"), 1.0),
            (lambda: get_messages(5), 0.5),
            (lambda: search_query("search term"), 0.8),
            (get_data, 0.4),
        ],
        "sleep_range": (2, 5),
    },
    "heavy_user": {
        "weight": 20,
        "actions": [
            (get_large_data, 1.5),
            (lambda: get_messages(20), 0.8),
            (lambda: search_query("complex query"), 1.0),
            (download_heavy_session, 2.0),
        ],
        "sleep_range": (1, 3),
    },
    "api_client": {
        "weight": 15,
        "actions": [
            (health_check_polling, 0.2),
            (get_data, 0.3),
            (api_polling_pattern, 5.0),
        ],
        "sleep_range": (0.5, 2),
    },
    "interactive": {
        "weight": 20,
        "actions": [
            (interactive_session, 3.0),
            (bulk_message_send, 2.0),
            (mixed_size_uploads, 2.5),
        ],
        "sleep_range": (3, 8),
    },
    "bursty": {
        "weight": 10,
        "actions": [
            (bulk_message_send, 1.0),
            (streaming_simulation, 3.0),
            (lambda: [post_echo("large") for _ in range(5)], 2.0),
        ],
        "sleep_range": (5, 15),  # Long pauses between bursts
    },
    "idle": {
        "weight": 5,
        "actions": [
            (health_check_polling, 0.2),
            (test_connection, 0.3),
        ],
        "sleep_range": (10, 20),  # Very inactive
    },
}


def select_traffic_pattern() -> dict:
    """Select a traffic pattern based on weights"""
    patterns = list(TRAFFIC_PATTERNS.keys())
    weights = [TRAFFIC_PATTERNS[p]["weight"] for p in patterns]
    selected = random.choices(patterns, weights=weights, k=1)[0]
    logger.info(f"[{CLIENT_ID}] Selected traffic pattern: {selected}")
    return TRAFFIC_PATTERNS[selected]


def run_initial_setup():
    """Initial setup and authentication"""
    users = [
        ("alice", "alice@example.com", "password123"),
        ("bob", "bob@example.com", "secret456"),
        ("charlie", "charlie@example.com", "pass789"),
        ("david", "david@example.com", "secure999"),
        ("eve", "eve@example.com", "key777"),
    ]

    logger.info(f"[{CLIENT_ID}] === Starting setup ===")
    test_connection()
    time.sleep(0.5)

    # Register and login with random user
    user = random.choice(users)
    username, email, password = user

    register_user(username, email, password)
    time.sleep(0.3)

    login_user(username, password)
    time.sleep(0.3)

    get_user_info(username)
    time.sleep(0.5)


def run_pattern_based_traffic():
    """Run traffic based on selected pattern"""
    pattern = select_traffic_pattern()
    actions = pattern["actions"]
    sleep_range = pattern["sleep_range"]

    for action_func, duration in actions:
        try:
            action_func()
            time.sleep(duration)
        except Exception as e:
            logger.error(f"[{CLIENT_ID}] Action failed: {e}")

    # Sleep according to pattern
    sleep_time = random.uniform(*sleep_range)
    logger.info(f"[{CLIENT_ID}] Sleeping for {sleep_time:.1f}s")
    time.sleep(sleep_time)


if __name__ == "__main__":
    logger.info(f"[{CLIENT_ID}] Starting enhanced HTTPS client")
    logger.info(f"[{CLIENT_ID}] Client ID: {CLIENT_ID}")

    # Initial setup
    run_initial_setup()

    # Main loop with pattern-based traffic
    cycle_count = 0
    while True:
        cycle_count += 1
        logger.info(f"[{CLIENT_ID}] === Cycle {cycle_count} ===")

        run_pattern_based_traffic()
