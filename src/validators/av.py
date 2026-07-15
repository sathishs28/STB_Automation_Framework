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

# This is for testing purpose, later will move to validator package
"""
    def lcn_find(self, ng_lcn, exp_lcns, repeat=1, delay=10):
        logger.info("Started LCN finding...")
        
        for attempt in range(repeat):
            logger.info("Pressing OK key to invoke the channel list...")
            logger.info(f"Attempt: {attempt + 1}/{repeat}")
            # Invoke Channel list
            self.ctx.backend.send_key("OK")
            time.sleep(2)

            # Capture frame and check the channel list invoked.
            while True:
                ch_lst_frame = self.ctx.backend.grab_frame()
                found_ch_lst, all_txt = self.ctx.ocr.contains_text(ch_lst_frame, "Channel List")
                logger.debug(f"Text found in current frame:\n {all_txt}")                
                if found_ch_lst:
                    logger.info("Channel List Invoked")
                    break
                else:
                    logger.info("Channel List Not Invoked, try again...")
                    time.sleep(1)

            # Navigate to Specific page LCNs
            while True:
                frame = self.ctx.backend.grab_frame()
                found_lcn, all_txt = self.ctx.ocr.contains_text(frame, ng_lcn)
                logger.debug(f"Text found in current frame:\n {all_txt}")

                if found_lcn:
                    logger.info(f"LCN - {ng_lcn} found")
                    break
                else:
                    logger.info(f"LCN - {ng_lcn} Not Found, go to next page")
                    self.ctx.backend.send_key("YELLOW COLOR KEY")
                    # time.sleep(0.5)

            # Finding the LCNs
            for i in exp_lcns:
                    frame = self.ctx.backend.grab_frame()
                    found_lcn, _ = self.ctx.ocr.contains_text(frame, i)
                    
                    if found_lcn:
                        logger.info(f"LCN - {i} found at attempt: {attempt + 1}/{repeat}")
                        return True
                    else:
                        logger.info(f"LCN - {i} Not Found")
            self.ctx.backend.send_key("EXIT", 2)
            if repeat > 1:
                logger.info("Wait for next try...")
                time.sleep(delay)
        return False                    
"""


            
