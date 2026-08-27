# tests/mocks/mock_backend.py
import numpy as np
from unittest.mock import MagicMock


class MockBackend:
    """
    Fake backend for unit tests.
    No hardware, no RedRat Hub, no PiBox needed.
    Implements the same interface as IRBackend.
    """

    def __init__(self):
        self._frame       = self._live_frame()
        self._key_history = []
        self.capture      = MagicMock()
        self.capture.save_screenshot = MagicMock(return_value="evidence/mock.png")

    def send_key(self, key, hold_ms=100, repeat=1):
        self._key_history.append(key)

    def grab_frame(self):
        return self._frame.copy()

    def get_device_info(self):
        info              = MagicMock()
        info.is_connected = True
        info.device_id    = "MockDevice"
        info.dataset      = "MockDataset"
        info.backend      = "mock"
        return info

    # ── Test helpers ──────────────────────────────────────

    def set_black_screen(self):
        self._frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    def set_live_screen(self):
        self._frame = self._live_frame()

    def set_custom_frame(self, frame):
        self._frame = frame

    def keys_pressed(self):
        return self._key_history.copy()

    def clear_history(self):
        self._key_history.clear()

    @staticmethod
    def _live_frame():
        frame = np.ones((720, 1280, 3), dtype=np.uint8) * 80
        frame[100:400, 200:800] = 200
        frame[50:70,   50:300]  = 255
        return frame