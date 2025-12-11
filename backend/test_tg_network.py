import sys
import os
import requests
import socket
import logging
from pprint import pformat

# Add the current directory to sys.path to ensure we can import app modules
# Assuming this script is run from project root or backend/ directory
if os.path.join(os.getcwd(), 'backend') in sys.path:
    pass
else:
    sys.path.append(os.getcwd())

try:
    from app.core.config import settings
except ImportError:
    # Fallback if run from backend directory directly
    sys.path.append(os.path.join(os.getcwd(), '..'))
    try:
        from app.core.config import settings
    except ImportError:
        print("Error: Could not import app.core.config.settings.")
        print("Please run this script from the project root (k-alert/backend) using:")
        print("  python test_tg_network.py")
        sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dns(hostname):
    logger.info(f"Checking DNS resolution for {hostname}...")
    try:
        ip = socket.gethostbyname(hostname)
        logger.info(f"DNS resolved: {hostname} -> {ip}")
        return True
    except socket.gaierror as e:
        logger.error(f"DNS resolution failed for {hostname}: {e}")
        return False

def check_connection(url, method='GET', payload=None, timeout=10):
    logger.info(f"Testing {method} request to {url}...")
    try:
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=payload, timeout=timeout)
        
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Headers: {pformat(dict(response.headers))}")
        logger.info(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            logger.info("Request successful!")
            return True
        else:
            logger.warning("Request returned non-200 status code.")
            return False
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout Error: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Exception: {e}")
    
    return False

def main():
    logger.info("Starting Telegram Network Test...")
    
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured in settings/env.")
        return
    
    # Obfuscate token for logging
    masked_token = f"{token[:5]}...{token[-5:]}" if len(token) > 10 else "***"
    logger.info(f"Using Bot Token: {masked_token}")
    logger.info(f"Using Chat ID: {chat_id}")

    # 1. DNS Check
    if not check_dns("api.telegram.org"):
        logger.error("Aborting further tests due to DNS failure.")
        return

    # 2. Basic Connectivity Check (GET /)
    # The root url typically redirects or returns 404/200 OK depending on endpoint, 
    # but 'getMe' is a better test for the bot specifically.
    # However, to test raw network to the host, we can just hit the base domain or me endpoint.
    
    # 3. Test 'getMe' (Verifies Token and Connectivity)
    get_me_url = f"https://api.telegram.org/bot{token}/getMe"
    logger.info("\n--- Testing 'getMe' method ---")
    if not check_connection(get_me_url):
        logger.error("'getMe' check failed. Check your token or network connection.")
    else:
        logger.info("'getMe' check passed. Token is valid and API is reachable.")
        
    # 4. Test 'sendMessage' (Verifies sending capability)
    if chat_id:
        logger.info("\n--- Testing 'sendMessage' method ---")
        send_msg_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "Hello from k-alert network test script! 🚀"
        }
        if check_connection(send_msg_url, method='POST', payload=payload):
            logger.info("Message sent successfully!")
        else:
            logger.error("Failed to send message.")
    else:
        logger.warning("\nSkipping 'sendMessage' test because TELEGRAM_CHAT_ID is not set.")

    logger.info("\nTest script completed.")

if __name__ == "__main__":
    main()
