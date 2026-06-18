# debug_test_timing_live.py
import time
from core.device_manager import Device_Manager
from analysis.timing import TimingEngine
from analysis.av_quality import AVQualityChecker
from core.logger import logging
import cv2

logger = logging.getLogger(__name__)

dm      = Device_Manager()
backend = dm.startup()
timer   = TimingEngine()
av      = AVQualityChecker()

# Test 1 — simple timer
logger.debug(" Test-1: Start")
timer.start()
time.sleep(0.5)
elapsed = timer.stop()
print(f"Simple timer: {elapsed:.1f}ms")   # should be ~500ms
logger.debug(" Test-1: End")

# Test 2 — wait for screen change after key press
logger.debug(" Test-2: Start")
baseline = backend.grab_frame()
changed, elapsed_ms, new_frame = timer.wait_for_frame_change(
    grab_frame_fn  = backend.grab_frame,
    baseline_frame = baseline,
    threshold      = 0.01,
    timeout        = 10
)
if new_frame:
    cv2.imwrite("temp/timing_live_T2_new_frame.png", new_frame)

print(f"Screen changed: {changed} in {elapsed_ms:.1f}ms")
logger.debug(" Test-2: End")


# Test 3 — full zap time measurement
logger.debug(" Test-3: Start")
def channel_visible(frame):
    # New channel visible = screen is not black
    is_black, _ = av.is_black_screen(frame)
    return not is_black

success, zap_ms = timer.measure_zap_time(
    grab_frame_fn = backend.grab_frame,
    send_key_fn   = backend.send_key,
    key           = "CH_UP",
    detect_fn     = channel_visible,
    timeout       = 10
)
print(f"Zap time: {zap_ms:.1f}ms | success={success}")
logger.debug(" Test-3: End")

dm.shutdown()