# tests/mocks/mock_device_manager.py
from tests.mocks.mock_backend import MockBackend


class MockDeviceManager:
    """
    Fake DeviceManager — returns MockBackend without touching hardware.
    """

    def __init__(self):
        self._backend = MockBackend()

    def startup(self):
        return self._backend

    def shutdown(self):
        pass