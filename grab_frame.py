# run this once to capture a template
import time
from core.capture import CaptureModule

cap      = CaptureModule()
cap.start()

# Grab full frame and save
# frame = backend.grab_frame()
# print(frame)

timestamp = time.strftime("%Y%m%d_%H%M%S")

path = f"frame_captured_{timestamp}.png"
cap.save_screenshot(filename=path)

print("Frame saved on Evidence directory, File name:",path)
cap.stop()
