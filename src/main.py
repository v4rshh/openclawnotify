import os
import sys
import time
import logging
from dotenv import load_dotenv

# Load .env file at the very beginning
load_dotenv()

# Ensure the parent directory is in sys.path to allow absolute imports of the 'src' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import dynamodb
from src import alerts


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
log = logging.getLogger("main")

def run_service(poll_interval_seconds: int = 300):
    """
    Main polling loop.
    Fetches device data, checks alert boundaries, and sleeps.
    """
    log.info('Modular WhatsApp alert service started')
    while True:
        try:
            devices = dynamodb.fetch_device_data()
            for device in devices:
                alerts.check_device(device)
        except Exception as e:
            log.error(f"Error in service loop: {e}", exc_info=True)
            
        log.info(f'Cycle complete. Sleeping for {poll_interval_seconds}s...')
        time.sleep(poll_interval_seconds)

if __name__ == "__main__":
    # Check every 5 minutes by default
    run_service(poll_interval_seconds=300)
