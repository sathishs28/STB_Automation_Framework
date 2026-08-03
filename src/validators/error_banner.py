# boot.py -- Boot related functions/methods.
import time
from core.logger import logging

from ast import literal_eval

logger = logging.getLogger(__name__)


class ErrorBanner:

    def __init__(self, ctx):
        self.ctx = ctx
        logger.debug(f"Error banner validator Module called, "
                     f"to check the {self.ctx.customer} STB error banner Test Cases")

    def no_signal_detect(self, timeout=10):
        """
        The is method to used to detect the "No signal banner" continuous  up to given timeout.
        grab current frame, check the NO SIGNAL message is appeared or not
        lib used: ocr.contains_text(current_frame, expected_text, region)
        returns: found (True or False), all text
        """
        for _ in range(timeout,0,-1):
            no_signal_frame = self.ctx.backend.grab_frame()
            no_signal_region = literal_eval(self.ctx.config.get("region.no_signal"))
            found, _ = self.ctx.ocr.contains_text(no_signal_frame, self.ctx.config.get("banner_messages.no_signal"), no_signal_region)

            if found:
                logger.info("No signal banner detected")
                return True
            else:
                logger.info("Wait for no signal banner...")
                time.sleep(1)
        logger.error("No signal banner is not detected")
        return False

