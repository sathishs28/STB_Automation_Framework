# test_capture_live.py
import cv2
from core.capture import CaptureModule

cap = CaptureModule()
cap.start()

# Verify frame shape
frame = cap.grab_frame()
print("✅ Frame shape:", frame.shape)
print("✅ Frame dtype:", frame.dtype)

# Save a screenshot
path = cap.save_screenshot("test_capture.png")
print("✅ Saved to:", path)

# Live preview — press Q to quit
print("Showing live preview — press Q to quit")
while True:
    frame = cap.grab_frame()
    cv2.imshow("PiBox HDMI Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
cap.stop()