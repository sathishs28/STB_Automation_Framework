# smoke_test.py
from core.device_manager import Device_Manager

dm = Device_Manager()
backend = dm.startup()

# IR control
backend.send_key("VOL_UP")

# Capture
frame = backend.grab_frame()
print("Frame shape:", frame.shape)

# Save evidence
backend.capture.save_screenshot("smoke_test.png")

dm.shutdown()