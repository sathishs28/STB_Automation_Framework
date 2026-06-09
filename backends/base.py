# backends/base.py
from abc import ABC, abstractmethod


class IR_DeviceInterface(ABC):
    """Every backend must implement these 3 methods"""

    @abstractmethod
    def send_key(self, key, repeat=1):
        """Send a key press to the device"""
        pass

    @abstractmethod
    def grab_frame(self):
        """Capture a frame from HDMI feed"""
        pass

    @abstractmethod
    def get_device_info(self):
        """Return current device status"""
        pass

class CaptureInterface(ABC):

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def grab_frame(self):
        pass

    @abstractmethod
    def save_screenshot(self, filename):
        pass