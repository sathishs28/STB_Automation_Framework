import yaml
import logging
import importlib
import time
from pathlib import Path
from core.redrat.redrat_hub import RedRatHubManager
from core.exceptions import ConnectionError
from backends.ir_backend import IR_Backend

CONFIG_FILE = (
    Path(__file__).resolve().parent.parent
    /"config"
    /"devices.yaml"
)
logger = logging.getLogger(__name__)

class Device_Manager:

    def __init__(self, config_path=CONFIG_FILE):
        self.config_path = config_path
        self.backend     = None
        self.device_name = None
        self.config      = None

    def startup(self):
        """
        Call this once at the start of every test session.
        Reads devices.yaml, loads the right backend, runs health check.
        """
        logger.info("=" * 50)
        logger.info("Device Manager — starting up...")
        logger.info("=" * 50)

        # Step 1 — load devices.yaml
        self._load_config()

        # Step 2 — load the correct backend
        self._load_backend()

        # Step 3 — ensure hub is running for IR
        if isinstance(self.backend, IR_Backend):
            self.hub_manager = RedRatHubManager()
            self.hub_manager.ensure_running()

        # Step 4 — health check
        self._health_check()

        # Start capture pipeline
        self.backend.capture.start()

        logger.info(f"✅ Startup complete — ready to test [{self.device_name}]")
        logger.info("=" * 50)

        return self.backend

    def shutdown(self):
        """Call this at the end of every test session."""
        logger.info("STB Framework — shutting down")
        
        # Stop the capture Module
        if self.backend and self.backend.capture:
            self.backend.capture.stop()

        # Stop the Redrat Hub
        if hasattr(self, "hub_manager"):
            self.hub_manager.stop()

        self.backend = None
        logger.info("✅ Shutdown complete")
        logger.info("=" * 50)

    # ── private methods ──────────────────────────────────────

    def _load_config(self):
        """Read devices.yaml and get active device config."""
        # print("Read devices.yaml and get active device config")
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)

            self.device_name = self.config.get("active_device")
            # print(f"List the active device config'{self.device_name}"'')
            if not self.device_name:
                raise ValueError("'active_device' not set in devices.yaml")
            logger.info(f"Active device → '{self.device_name}'")

        except FileNotFoundError:
            logger.error(f"❌ devices.yaml not found at '{self.config_path}'")
            print("devices.yaml not found at '{}'".format(self.config_path))
            raise

    def _load_backend(self):
        """Load the correct backend based on devices.yaml config."""
        device_config = self.config["devices"].get(self.device_name)
        if not device_config:
            logger.error(f"❌ Device '{self.device_name}' not found in devices.yaml")
            raise ValueError(f"Device '{self.device_name}' not defined in devices.yaml")
        

        backend_type = device_config.get("backend")
        key_map_name = device_config.get("key_map")

        logger.info(f"Backend → '{backend_type}' | Key map → '{key_map_name}'")

        if backend_type == "ir":
            # Load the correct key_map dynamically
            key_map_module = importlib.import_module(f"backends.key_maps.{key_map_name}")
            key_map = key_map_module.KEY_MAP

            # Pass key_map into IR_Backend
            self.backend = IR_Backend(key_map=key_map)
            logger.info("✅ IR backend loaded")

        elif backend_type == "adb":
            # Placeholder — Phase 2
            raise NotImplementedError("ADB backend not yet implemented")

        else:
            raise ValueError(f"Unknown backend type '{backend_type}'")

    def _health_check(self, retries=5, delay_seconds=2):
        """Verify device is reachable before tests start."""
        logger.info("Running health check...")

        attempt = 1
        while attempt <= retries:
            info = self.backend.get_device_info()
            if info.is_connected:
                break

            logger.warning(
                f"Health check attempt {attempt}/{retries} failed: device not ready yet. Retrying in {delay_seconds}s..."
            )
            attempt += 1
            time.sleep(delay_seconds)

        if not info.is_connected:
            logger.error("❌ Health check FAILED")
            logger.error("   Check → Is RedRatHub.exe running?")
            logger.error("   Check → Is RedRat-X plugged in via USB?")
            raise ConnectionError("Device not connected — aborting startup")

        logger.info(f"✅ Health check passed")
        logger.info(f"   Device ID  : {info.device_id}")
        logger.info(f"   Dataset    : {info.dataset}")
        logger.info(f"   Backend    : {info.backend}")