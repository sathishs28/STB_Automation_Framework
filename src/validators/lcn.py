# lcn.py -- LCN related functions/methods.

import time
from core.logger import logging
from pathlib import Path
from src.navigators.channel_banner import ChannelBanner
from src.remote import Remote

PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)

class LCN:

    def __init__(self, ctx):
        self.ctx = ctx
        self.channel_banner = ChannelBanner(ctx)
        self.remote = Remote(ctx)

        logger.debug(f" LCN Module called, to check the Customer:{self.ctx.customer} LCN Related testing...")

    def switch_to_lcn(self, lcn):
        logger.info(f"Switching to LCN - {lcn}...")
        self.remote.send_key_sequence(lcn)
        self.remote.send_key("OK")
        """ Later implement the logic to verify if the channel has switched successfully. """


    # Main Function LCN Finding in Channel List
    def lcn_find_ch_list(self, ng_lcn, exp_lcns, repeat=1, delay=10):
        logger.info("Started LCN finding in Channel list...")

        for attempt in range(repeat):
            logger.info(f"Attempt: {attempt + 1}/{repeat}")

            if not self._invoke_channel_list():
                continue

            self._navigate_to_lcn_page(ng_lcn)

            if self._find_expected_lcns(exp_lcns, attempt, repeat):
                return True

            self.remote.send_key("EXIT", 2)

            if attempt < repeat - 1:
                logger.info("Wait for next try...")
                time.sleep(delay)

        return False

    # Invoke Channel List
    def _invoke_channel_list(self):
        logger.info("Pressing OK key to invoke the channel list...")
        self.ctx.backend.send_key("OK")
        time.sleep(2)

        while True:
            frame = self.ctx.backend.grab_frame()
            found, text = self.ctx.ocr.contains_text(frame, "Channel List")

            logger.debug(f"Text found:\n{text}")

            if found:
                logger.info("Channel List Invoked")
                return True

            logger.info("Channel List Not Invoked, trying again...")
            time.sleep(1)

    # Navigate to Required LCN Page
    def _navigate_to_lcn_page(self, ng_lcn):
        while True:
            frame = self.ctx.backend.grab_frame()
            found, text = self.ctx.ocr.contains_text(frame, ng_lcn)

            logger.debug(f"Text found:\n{text}")

            if found:
                logger.info(f"LCN - {ng_lcn} found")
                return

            logger.info(f"LCN - {ng_lcn} not found, moving to next page")

            # For page down navigation, use the appropriate key based on your STB's remote control.
            self.remote.send_key("YELLOW COLOR KEY")    

    # Find Expected LCNs
    def _find_expected_lcns(self, exp_lcns, attempt, repeat):
        frame = self.ctx.backend.grab_frame()

        for lcn in exp_lcns:
            found, _ = self.ctx.ocr.contains_text(frame, lcn)

            if found:
                logger.info(
                    f"LCN - {lcn} found at attempt {attempt + 1}/{repeat}"
                )
                return True

            logger.info(f"LCN - {lcn} not found")

        return False