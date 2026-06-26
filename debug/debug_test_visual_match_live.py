# test_visual_match_live.py
import cv2
from core.device_manager import Device_Manager
from analysis.visual_match import VisualMatcher

dm      = Device_Manager()
backend = dm.startup()

# Send IR key signal
# backend.send_key("VOL_UP",repeat=2)

# Grab live frame
frame = backend.grab_frame()

print("Printing grabed live frame", frame)
print("Frame shape", frame.shape)

template_path="assets/customers/tccl/templates/boot_logo.png"
template = cv2.imread(template_path, cv2.IMREAD_COLOR)

print("Printing the template image", template)
print("Template shape", template.shape)


matcher = VisualMatcher(threshold=0.85)

# Test 1 — match against a template you cropped
found = matcher.is_same(
    frame,
    template_path
)

print(f"Found    : {found}")
# print(f"Score    : {score:.2f}")
# print(f"Location : {location}")
"""
# Test 2 — save debug image showing match location
matcher.save_debug_image(
    frame,
    template_path,
    output_path="evidence/debug_match_volume_bar.png"
)
"""
dm.shutdown()

