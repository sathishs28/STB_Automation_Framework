import os
import time
import logging
from dotenv import load_dotenv
import requests
from core.exceptions import ConnectionError, IRTransmitError
from core.logger import setup_logging

# Load .env file (silently fail if it doesn't exist)
try:
    load_dotenv()
except Exception:
    pass

# Setup logger in test script, not here.
# logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

class RedRat_Client:

    def __init__(self):
        logger.info("RedRat Client Application Starting...")
        # Load all config from .env
        self.hub_url      = os.getenv("REDRAT_HUB_URL")
        self.device_id    = os.getenv("REDRAT_DEVICE_ID")
        self.output_port  = os.getenv("REDRAT_OUTPUT_PORT")
        self.dataset      = os.getenv("REDRAT_DATASET")         # dataset means, Remote control IR signals database.
        self.timeout      = int(os.getenv("REDRAT_TIMEOUT_MS", 5000)) / 1000
        self.retry_count  = int(os.getenv("REDRAT_RETRY_COUNT", 3))

        # Validate — fail immediately if anything is missing
        missing = [k for k, v in {
            "REDRAT_HUB_URL"     : self.hub_url,
            "REDRAT_DEVICE_ID"   : self.device_id,
            "REDRAT_OUTPUT_PORT" : self.output_port,
            "REDRAT_DATASET"     : self.dataset,
        }.items() if not v]

        if missing:
            raise EnvironmentError(f"Missing .env values: {missing}")

        logger.info(f"RedRat Client ready → Hub_URL:{self.hub_url}")
        logger.info(f"dataset={self.dataset}")
        logger.info(f"output_port={self.output_port}")
    
    def get_devices(self):
        # Returns list of connected RedRat devices
        try:
            logger.info(f"Fetching devices from hub at {self.hub_url}...")
            response = requests.get(
                f"{self.hub_url}/api/redrats",
                timeout=self.timeout
            )
            # response.raise_for_status()
            if response.json() == []:
                logger.info(f"No Devices Found at {self.hub_url}")
                logger.info("Check if the RedRat Hub is running and the RedRat-X device is connected.")
                logger.info("Redrat Client Re-scaning...")
                response = requests.get(
                f"{self.hub_url}/api/redrats?rescan=true",
                timeout=self.timeout
                )
            response.raise_for_status()
            logger.info(f"Devices: {response.json()}")
            return response.json()

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Hub not reachable at {self.hub_url}")

    def get_signals(self, dataset=None):
        # Returns all signal names in a dataset
        dataset = dataset or self.dataset
        try:
            response = requests.get(
                f"{self.hub_url}/api/irdata/{dataset}",
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info(f"Signals in {dataset}: {response.json()}")
            return response.json()

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Hub not reachable at {self.hub_url}")

    def health_check(self):
        # Returns True if Hub is reachable and RedRat-X is connected
        try:
            devices = self.get_devices()
            is_healthy = len(devices) > 0
            logger.info(f"Health check: {'OK' if is_healthy else 'No devices found'}")
            return is_healthy

        except ConnectionError:
            logger.error("Health check FAILED — hub not reachable")
            return False

    def send_signal(self, signal, duration=0):
        """Send an IR signal to the STB"""

        url = f"{self.hub_url}/api/redrats/{self.device_id}/{self.output_port}"
        data = {
            "Dataset": self.dataset,
            "Signal": signal,
            "Duration": duration
        }

        last_connection_error = None

        for attempt in range(1, self.retry_count + 1):
            try:
                logger.info(f"Sending '{signal}' | attempt {attempt}")

                # Sending signal to RedRat Hub server
                response = requests.post(url, data=data, timeout=self.timeout)
                if response.status_code == 200:
                    logger.info(f"✅ '{signal}' sent successfully")
                    return True

                elif response.status_code == 400:
                    logger.error("❌ Bad request — Dataset or Signal field is missing or malformed")
                    logger.error(f"   Check → Dataset='{self.dataset}' | Signal='{signal}'")
                    raise IRTransmitError(f"Bad request for signal '{signal}'")

                elif response.status_code == 404:
                    logger.error("❌ Device not found — wrong device ID")
                    logger.error(f"   Check → REDRAT_DEVICE_ID='{self.device_id}' in your .env")
                    logger.error("   Tip   → Run GET /api/redrats in Swagger to get correct ID")
                    raise IRTransmitError(f"Device '{self.device_id}' not found")

                elif response.status_code == 500:
                    logger.error("❌ Signal not found in dataset")
                    logger.error(f"   Check → Signal='{signal}' in dataset='{self.dataset}'")
                    logger.error(
                        f"   Tip   → Run GET /api/datasets/{self.dataset}/signals in Swagger to list valid signals")
                    raise IRTransmitError(f"Signal '{signal}' not found in dataset '{self.dataset}'")

                else:
                    logger.warning(f"⚠️  Unexpected status {response.status_code} | retrying...")
            except IRTransmitError:
                # Do not retry
                raise

            except requests.exceptions.ConnectionError:
                last_connection_error = ConnectionError(f"Hub not reachable at {self.hub_url}")
                logger.warning(
                    f"Hub not reachable (attempt {attempt}/{self.retry_count})"
                )

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Timeout (attempt {attempt}/{self.retry_count})"
                )

            except Exception as e:
                logger.warning(
                    f"Unexpected error (attempt {attempt}/{self.retry_count}): {e}"
                )
            time.sleep(0.5)

        if last_connection_error is not None:
            raise last_connection_error

        return None