# boot.py -- Boot related functions/methods.
import time
from core.logger import logging
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)

class AV:
    
    def __init__(self, ctx):
        self.ctx = ctx

        logger.debug(f" AV Performance Module called, to check the Customer:{self.ctx.customer} STB AV performances...")

    # To verify the HDMI input status    
    def is_video_freeze(self):
        
        self.ctx.timer.start()
        self.ctx._timer_started = True
        while True:
            frame1 = self.ctx.backend.grab_frame()
            self.ctx.backend.send_key("UP")
            time.sleep(2)
            frame2 = self.ctx.backend.grab_frame()

            status, _ = self.ctx.av.is_frozen(frame1, frame2)

            if status:
                elapsed = self.ctx.timer.stop()
                self.ctx._timer_started = False
                logger.warning(f"Total runtime:{elapsed}")
                return status

    def is_video_available(self, wait_time=10):
        
        self.ctx.timer.start()
        self.ctx._timer_started = True
        
        for i in range(wait_time, 0, -1):

            status, _ = self.ctx.ctx.av.is_black_screen(self.ctx.ctx.backend.grab_frame())
            if status:
                logger.warning("⚠️ Black screen detected, Video is not playing ⚠️")
            else:
                logger.info("✅ Video is playing")
                return True
            logger.info("Waiting for Live TV to play...")
            logger.info("⚠️ Timeout in %d sec", i)
            time.sleep(1)
        logger.error("❌ Timeout reached, Video is not playing")
        return False

            
