# core/capture.py
import os
import time
import logging
import numpy as np
from core.exceptions import CaptureError
from core.logger import setup_logging

# Log set
setup_logging()

import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Load .env file (silently fail if it doesn't exist)
from dotenv import load_dotenv
try:
    load_dotenv()
except Exception:
    pass

logger = logging.getLogger(__name__)

# Mandatory initialization command for the GStreamer multimedia framework
Gst.init(None)


class CaptureModule:

    def __init__(self):
        # Load config from .env
        # device_index means, which capture device to use if multiple are present. To check run command "gst-device-monitor-1.0 Video/Source" in terminal.
        self.device_index = int(os.getenv("CAPTURE_DEVICE_INDEX", 0))
        self.width        = int(os.getenv("CAPTURE_WIDTH", 1920))
        self.height       = int(os.getenv("CAPTURE_HEIGHT", 1080))
        self.fps          = int(os.getenv("CAPTURE_FPS", 30))

        self.pipeline = None
        self.sink     = None
        self.running  = False

        logger.info(f"CaptureModule ready → device={self.device_index} | {self.width}x{self.height}@{self.fps}fps")

    def start(self):
        
        """Build and start the GStreamer pipeline."""
        pipeline_str = (
            f"mfvideosrc device-index={self.device_index} ! "
            f"image/jpeg,width={self.width},height={self.height},framerate={self.fps}/1 ! "
            f"queue ! "
            f"jpegdec ! "
            f"videoconvert ! "
            f"video/x-raw,format=BGR ! "
            f"queue ! "
            f"appsink name=sink emit-signals=false max-buffers=1 drop=true sync=false"
        )
        """
        The pipeline captures video from the specified device, decodes JPEG frames, converts them to BGR format, and sends them to an appsink for retrieval in Python.
        # The use of queues helps to manage the flow of data and prevent bottlenecks, while the appsink allows for efficient retrieval of frames in the application.
        # And the "drop=true" property ensures that if the application can't keep up with the frame rate, it will drop frames instead of buffering them, which helps to maintain real-time performance.
        """
        logger.info("Starting capture pipeline...")
        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
            logger.info(f"GStreamer pipeline created: {pipeline_str}")
        except Exception as exc:
            logger.error(f"Failed to create pipeline: {exc}")
            raise CaptureError(f"Failed to create pipeline: {exc}")
        
        self.sink = self.pipeline.get_by_name("sink")
        if not self.sink:
            raise CaptureError("Failed to get appsink")
        
        check_state = self.pipeline.set_state(Gst.State.PLAYING)
        logger.info(f"Pipeline state change result: {check_state}")
        if check_state == Gst.StateChangeReturn.FAILURE:
            logger.error("Failed to start pipeline")
            raise CaptureError("Failed to start pipeline")
            
        # Wait for the pipeline to transition
        # state_change, _, _ = self.pipeline.get_state(5 * Gst.SECOND)
        ret, state, pending = self.pipeline.get_state(5 * Gst.SECOND)
        logger.info(f" Pipline Current state -> ret={ret}, state={state}, pending={pending}")
        if state != Gst.State.PLAYING:
            logger.error("Pipeline did not reach PLAYING state")
            return False
        
        self.running  = True

        # Give pipeline time to start
        time.sleep(1)
        logger.info("✅ Capture pipeline running")

    def stop(self):
        """Stop the GStreamer pipeline cleanly."""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.running = False
            logger.info("✅ Capture pipeline stopped")

    def grab_frame(self):
        """
        Grab latest frame from PiBox HDMI feed.
        Returns numpy array (H, W, 3) in BGR format — ready for OpenCV.
        """
        if not self.running:
            raise RuntimeError("Capture pipeline not started — call start() first")

        # Pull latest sample from appsink
        sample = self.sink.emit("pull-sample")

        if sample is None:
            raise RuntimeError("❌ No frame received from capture device")

        # Convert GStreamer buffer to numpy array
        buf    = sample.get_buffer()
        caps   = sample.get_caps()
        struct = caps.get_structure(0)
        w      = struct.get_value("width")
        h      = struct.get_value("height")

        # Extract raw bytes → numpy array
        success, map_info = buf.map(Gst.MapFlags.READ)
        if not success:
            raise RuntimeError("❌ Failed to map GStreamer buffer")

        frame = np.frombuffer(map_info.data, dtype=np.uint8).reshape((h, w, 3)).copy()
        buf.unmap(map_info)

        return frame  # BGR numpy array — OpenCV compatible
    
    def save_screenshot(self, filename=None):
        import cv2
        import os
        import time
        import inspect

        frame = self.grab_frame()

        timestamp = time.strftime("%Y%m%d_%H%M%S")

        if not filename:
            # Get caller script filename
            caller_file = inspect.stack()[1].filename
            test_name = os.path.splitext(os.path.basename(caller_file))[0]

            filename = f"{test_name}_{timestamp}.png"
        else:
            name, ext = os.path.splitext(filename)
            ext = ext or ".png"
            filename = f"{name}_{timestamp}{ext}"

        evidence_dir = os.getenv("EVIDENCE_DIR", "evidence")
        os.makedirs(evidence_dir, exist_ok=True)

        path = os.path.join(evidence_dir, filename)
        cv2.imwrite(path, frame)

        logger.info(f"Screenshot saved → {path}")
        logger.debug(f"Screenshot saved → {path}")

        return path