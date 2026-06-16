from core.device_manager import Device_Manager
from analysis.visual_match import VisualMatcher
from core.logger import setup_logging

# Setup logger
setup_logging()

dm     = Device_Manager()
backend = dm.startup()

# def test_watermark_visible():
backend.send_key("MUTE", repeat=1)
frame = backend.grab_frame()

matcher = VisualMatcher(threshold=0.80)

found, score, location = matcher.match(frame, template_path="assets/templates/mute_logo.png")
# Test 1 — match against a template you cropped
print(f"Found    : {found}")
print(f"Score    : {score:.2f}")
print(f"Location : {location}")

"""
if found:
    assert found
else:
    assert found
"""
# Test 2 — save debug image showing match location
matcher.save_debug_image(
    frame,
    template_path="assets/templates/mute_logo.png",
    output_path="evidence/mute_logo_evidence.png"
)

dm.shutdown()
