# boot.py -- Boot related functions/methods.
import time
from src.navigators.channel_banner import ChannelBanner

import cv2
from core.logger import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)

class LiveTV:
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.ch_bar = ChannelBanner(ctx)

        logger.debug(f" Validator - Live TV Module called, to check the {self.ctx.customer} Live TV Test Cases")

    def is_video_alive(self, duration=5, interval=0.5, required_motion_count=7, region=None):
        """
        Check whether video is actively changing.
        Args:
            duration (int)
            interval (float)
            required_motion_count (int)
            region (Region)
        Returns:
            bool
        """
        logger.info("Checking video motion...")
        previous_frame = None
        motion_count = 0
        end_time = time.time() + duration

        while time.time() < end_time:

            """
            Feature will implement the video record for Live TV validation.
            """
            frame = self.ctx.backend.grab_frame()

            if frame is None:
                logger.warning("Unable to capture frame.")
                time.sleep(interval)
                continue

            if previous_frame is not None:

                status, _ = self.ctx.av.motion_detect(previous_frame, frame, region=region)
                if status:
                    """
                    Here checking the live frame is_frozen, 
                    returns the True - Motion detected, False - Frame not moving
                    """
                    motion_count += 1

                    logger.debug(
                        "Motion detected (%d/%d)",
                        motion_count,
                        required_motion_count,
                    )

                    if motion_count >= required_motion_count:
                        logger.info("Video is alive.")
                        return True

            previous_frame = frame
            time.sleep(interval)

        logger.warning("Video appears frozen.")
        self.ctx.backend.save_frame(f"{self.ctx.evidence_path}/Live_TV_last_frame.png", previous_frame)
        return False

    def is_live_tv_playing(self, duration=10, wait_time=30):
        """
        This method is used to check the Live TV is playing or not.
        Checking the current frame is black or not. If it detects black frame until it wait upto timeout time.
        If the frame has content not black then return the status: True
        """
        for i in range(wait_time, 0, -1):

            status, _ = self.ctx.av.is_black_screen(self.ctx.backend.grab_frame())
            if status:
                logger.warning("⚠️ Black screen detected, Live TV is not playing ⚠️")
            else:
                logger.info("✅ Live TV is playing")
                return True
            logger.info("Waiting for Live TV to play...")
            logger.info("⚠️ Timeout in %d sec", i)
            time.sleep(1)
        logger.error("❌ Timeout reached, Live TV is not playing")
        return False, "Live TV is not playing"

    def ch_up_down(self):
        self.ctx.backend.send_key("DOWN", 1)
        frame1 = self.ctx.backend.grab_frame()
        lcn = self.ch_bar.get_lcn_in_ch_bar(frame1)
        self.ctx.backend.save_frame(f"{self.ctx.evidence_path}/ch_banner.png", frame1)
        return True, lcn