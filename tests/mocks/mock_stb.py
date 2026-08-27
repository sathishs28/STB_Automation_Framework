# tests/mocks/mock_stb.py
from tests.mocks.mock_backend import MockBackend
from analysis.visual_match import VisualMatcher
from analysis.ocr import OCREngine
from analysis.av_quality import AVQualityChecker
from analysis.timing import TimingEngine
from core.config_loader import cfg


class MockSTB:
    """
    Self-contained mock STB context for unit tests.
    Creates its own analysis engines — no conftest.py needed.
    """

    def __init__(self, black_screen=False):
        cfg.load()

        self.customer = cfg.get("customer.name", "mock_customer")
        self.config   = cfg
        self.backend  = MockBackend()
        self.matcher  = VisualMatcher(threshold=0.85)
        self.ocr      = OCREngine()
        self.av       = AVQualityChecker()
        self.timer    = TimingEngine()

        if black_screen:
            self.backend.set_black_screen()

    def set_black_screen(self):
        self.backend.set_black_screen()

    def set_live_screen(self):
        self.backend.set_live_screen()