# tests/unit_mock_tests/conftest.py
import pytest
from tests.mocks.mock_backend import MockBackend
# from analysis.visual_match import VisualMatcher
# from analysis.ocr import OCREngine
# from analysis.av_quality import AVQualityChecker
from analysis.timing import TimingEngine
from core.config_loader import cfg


# ── Override root fixtures locally ────────────────────────

@pytest.fixture(scope="session")
def config():
    """Override root config — load without hardware."""
    cfg.load()
    return cfg


@pytest.fixture(scope="session")
def customer(config):
    return config.get("customer.name", "mock_customer")


@pytest.fixture(scope="session")
def backend():
    """
    Override root backend fixture.
    Returns MockBackend — zero hardware needed.
    Root conftest.py backend is completely ignored for this folder.
    """
    return MockBackend()

"""
@pytest.fixture(scope="session")
def matcher():
    return VisualMatcher(threshold=0.85)


@pytest.fixture(scope="session")
def ocr():
    return OCREngine()


@pytest.fixture(scope="session")
def av():
    return AVQualityChecker()

"""
@pytest.fixture(scope="session")
def timer():
    return TimingEngine()


# ── Per-function mock fixtures ────────────────────────────

@pytest.fixture(scope="function")
def mock_backend():
    """Fresh MockBackend per test — live screen by default."""
    return MockBackend()


@pytest.fixture(scope="function")
def mock_backend_black():
    """Fresh MockBackend pre-set to black screen."""
    b = MockBackend()
    b.set_black_screen()
    return b


@pytest.fixture(scope="function")
def mock_stb(config, customer):
    """Full mock STB context — all analysis engines included."""
    from tests.mocks.mock_stb import MockSTB
    return MockSTB()