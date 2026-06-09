import logging
import os
import sys
from pathlib import Path

# Ensure repo root is on PYTHONPATH when running this file directly.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.device_manager import Device_Manager
from core.logger import setup_logging

# Log set
setup_logging()

# Device manager start
dm = Device_Manager()
ir = dm.startup()

# Send a key
ir.send_key("VOL_UP")

# Device manager stop
dm.shutdown()