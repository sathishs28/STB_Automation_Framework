# backends/ir_backend.py
#import os
import time
import logging
from dataclasses import dataclass

from backends.base import IR_DeviceInterface
from backends.key_maps.OVT_NXT_Digital_Remote import KEY_MAP
from core.redrat.redrat_client import RedRat_Client
from core.redrat.exceptions import IRTransmitError, ConnectionError

# Setup logger
logger = logging.getLogger(__name__)

# Simple dataclass to hold device info
@dataclass
class DeviceInfo:
    device_type  : str
    backend      : str
    is_connected : bool
    device_id    : str
    dataset      : str
    firmware     : str = None
    capture_res  : tuple = None


class IR_Backend(IR_DeviceInterface):
    """
    IR control backend for STB using RedRat Hub REST API.
    Implements the DeviceInterface contract.
    """

    def __init__(self, key_map:None):
        self.client = RedRat_Client()
        self.key_map = key_map or {}
        logger.info("IR_Backend initialised")

    # ── 1. send_key ──────────────────────────────────────────

    def send_key(self, key, repeat=1):
        """
        Send a key press to the STB.
        key     : logical key name e.g. 'CH_UP', 'OK', 'NUM_5'
        hold_ms : how long to hold in milliseconds
        repeat  : how many times to send
        """

        # Step 1 — translate logical key to dataset signal name
        signal = KEY_MAP.get(key)
        if not signal:
            logger.error(f"❌ Key '{key}' not found in KEY_MAP")
            logger.error(f"   Available keys: {list(KEY_MAP.keys())}")
            raise IRTransmitError(f"Key '{key}' not in KEY_MAP")

        # Step 2 — send required number of times
        for i in range(repeat):
            logger.info(f"send_key → '{key}' (signal='{signal}') [{i+1}/{repeat}]")
            self.client.send_signal(signal=signal)

            # Small gap between repeated keys
            time.sleep(1)

        logger.info(f"✅ send_key '{key}' done")

    # ── 2. grab_frame ─────────────────────────────────────────

    def grab_frame(self):
        """
        Capture a frame from HDMI feed.
        STUB — will be implemented in Phase 3 (GStreamer + PiBox).
        Returns None for now.
        """
        logger.warning("grab_frame() not yet implemented — Phase 3 (GStreamer)")
        return None

    # ── 3. get_device_info ────────────────────────────────────

    def get_device_info(self):
        """
        Return current device status.
        Called by device_manager at startup and health checks.
        """
        try:
            devices = self.client.get_devices()
            is_connected = len(devices) > 0

            info = DeviceInfo(
                device_type  = "stb",
                backend      = "ir",
                is_connected = is_connected,
                device_id    = self.client.device_id,
                dataset      = self.client.dataset,
                capture_res  = None     # filled in Phase 3
            )

            logger.info(f"Device info → {info}")
            return info

        except ConnectionError:
            # Hub unreachable — return disconnected state
            return DeviceInfo(
                device_type  = "stb",
                backend      = "ir",
                is_connected = False,
                device_id    = self.client.device_id,
                dataset      = self.client.dataset,
            )
"""
backend = IR_Backend()

# 1 — check device info
info = backend.get_device_info()
print("Connected  :", info.is_connected)
print("Device ID  :", info.device_id)
print("Dataset    :", info.dataset)

# 2 — send a key — STB should respond
backend.send_key("VOL_UP")

# 3 — send repeated keys
backend.send_key("CH_UP")

# 4 — wrong key — should fail clearly
backend.send_key("WRONG_KEY")
"""