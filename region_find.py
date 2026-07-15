import cv2
from core.capture import CaptureModule

cap      = CaptureModule()
cap.start()

frame = cap.grab_frame()

roi = cv2.selectROI("Select Region", frame, showCrosshair=True)

cv2.destroyAllWindows()

print(roi)

cap.stop()