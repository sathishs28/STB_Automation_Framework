# lcn.py -- LCN related functions/methods.

import time
from core.logger import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)

class LCN:

    def __init__(self, ctx):
        self.ctx = ctx

        logger.debug(f" LCN Module called, to check the Customer:{self.ctx.customer} LCN Related testing...")

    # To find the lcn in Channel list
    def lcn_find_ch_list(self, ng_lcn, exp_lcns, repeat=1, delay=10):
        logger.info("Started LCN finding in Channel list...")

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
