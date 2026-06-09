class DeviceError(Exception):
    """Base exception for all device errors"""
    pass

class IRTransmitError(DeviceError):
    """IR signal failed to transmit"""
    pass

class ConnectionError(DeviceError):
    """Hub not reachable"""
    pass

class CaptureError(DeviceError):
    pass