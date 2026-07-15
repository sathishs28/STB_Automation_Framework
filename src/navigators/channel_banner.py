# Pages | Channel Banner
import time

import cv2
from core.logger import logging
from src.remote import Remote
from pathlib import Path
from ast import literal_eval


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class ChannelBanner:

    def __init__(self, ctx):
        self.ctx = ctx
        
        # Initialize the Remote class with the backend
        self.remote = Remote(self.ctx)

        self._timer_started = False
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.templates_path = (
        PROJECT_ROOT
            / "assets"
            / "customers"
            / self.ctx.customer
            / "templates"
        )

        self.evidence_path = (
            PROJECT_ROOT
            / "evidence"
        )

    def invoke_channel_banner(self):
        self.remote.ok()
        logger.info("Channel banner Invoked.")
    def get_lcn_in_ch_bar(self, frame):
        """
        Extract the LCN from the channel banner.
        Returns:
            int: LCN if found.
            None: If no valid LCN is detected.
        """
        import re

        # 'literal_eval' used to maintain the same datatype. not consider as string
        lcn_region = literal_eval(self.ctx.config.get("region.channel_banner.lcn"))
        lcn_frm_ch_banner = self.ctx.ocr.extract_text(frame, lcn_region)

        lcn = re.search(r"\d+", lcn_frm_ch_banner)
        if not lcn:
            logger.warning("LCN not detected.")
            return None
        return int(lcn.group())

    def get_service_name_ch_bar(self, frame):
        """
        Extract the Service Name from the channel banner.
        Returns:
            str: Service Name if found.
            None: If no valid LCN is detected.
        """
        sname_region = literal_eval(self.ctx.config.get("region.channel_banner.service_name"))
        sname_frm_ch_banner = self.ctx.ocr.extract_text(frame, sname_region)
        if not sname_frm_ch_banner:
            logger.warning("Service name not detected.")
            return None
        return sname_frm_ch_banner

    # To verify the channel banner status
    def is_channel_banner_present(self, timeout=10):

        for i in range(timeout, 0, -1):
            frame = self.ctx.backend.grab_frame()

            lcn = self.get_lcn_in_ch_bar(frame)
            sname = self.get_service_name_ch_bar(frame)

            if lcn and sname is not None:
                logger.info("Channel Banner is present")
                return True, lcn, sname
            else:
                logger.info(f"Channel Banner is not present, waiting up...{i}sec")
            if i == 1:
                output_path = f"{self.evidence_path}/{self.ctx.customer}__channel_banner_not_present_{self.timestamp}.png"
                cv2.imwrite(output_path, frame)
                logger.info(f"Debug image saved → {output_path}")
            time.sleep(1)
        logger.warning("Channel banner is not present")
        return False, None, None
