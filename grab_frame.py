# run this once to capture a template
from core.device_manager import Device_Manager

dm      = Device_Manager()
backend = dm.startup()

# Grab full frame and save
backend.capture.save_screenshot("full_screen.png")

dm.shutdown()