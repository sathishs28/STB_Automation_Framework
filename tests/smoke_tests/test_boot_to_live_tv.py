import time
import pytest

from core.logger import logging

logger = logging.getLogger(__name__)

class Test_Boot_to_Live_TV:

    def test_bootup(self, stb):
        status, tl_boot_time, results = stb.boot.check_boot_sequence()
        logger.info("Total boot time: %d sec", tl_boot_time)
        logger.info("Results: %s", results)
        assert status

    def test_channel_banner_present(self, stb):
        status, lcn, sname = stb.channel_banner.is_channel_banner_present()
        if status:
            logger.info("LCN: %d", lcn)
            logger.info("SERVICE NAME: %s", sname)
        assert status

    def test_live_tv(self, stb):
        assert stb.liveTV.is_video_alive(duration=15)