import pytest

from core.logger import logging

logger = logging.getLogger(__name__)


class Test_Boot_to_Live_TV:
    
    def test_boot_to_live(self, boot):
        status, tl_boot_time, results = boot.check_boot_sequence()
        logger.info("Total boot time: %d sec", tl_boot_time)
        logger.info("Results: %s", results)
        assert status

    """
    def test_af_boot_is_live_tv_playing(self):
        pass

    def test_total_boot_time(self):
        pass
        
    """