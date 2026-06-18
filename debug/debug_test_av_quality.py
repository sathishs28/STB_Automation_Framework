# test_av_quality_live.py
import time
from core.device_manager import Device_Manager
from analysis.av_quality import AVQualityChecker
from core.logger import logging

logger = logging.getLogger(__name__)

dm      = Device_Manager()
backend = dm.startup()
av      = AVQualityChecker()

# Grab two frames 1 second apart for freeze detection
frame1 = backend.grab_frame()
time.sleep(2)
frame2 = backend.grab_frame()

# Test 1 — black screen check
logger.info(" Test-1: Start")
is_black, pct = av.is_black_screen(frame1)
print(f"Black screen : {is_black} ({pct:.2f}% black)")
logger.info(" Test-1: End")

# Test 2 — freeze check
logger.info(" Test-2: Start")
is_frozen, score = av.is_frozen(frame1, frame2)
print(f"Frozen       : {is_frozen} (similarity={score:.4f})")
logger.info(" Test-2: End")

# Test 3 — no signal check
logger.info(" Test-3: Start")
no_signal, reason = av.is_no_signal(frame1, frame2)
print(f"No signal    : {no_signal} (reason={reason})")
logger.info(" Test-3: End")

# Test 4 — combined health check
logger.info(" Test-4: Start")
health = av.check_video_health(frame1, frame2)
print(f"Health       : {health}")
logger.info(" Test-4: End")

dm.shutdown()