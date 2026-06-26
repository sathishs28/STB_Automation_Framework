# conftest.py
import pytest

from core.config_loader import cfg
from core.device_manager import Device_Manager

from analysis.visual_match import VisualMatcher
from analysis.ocr import OCREngine
from analysis.av_quality import AVQualityChecker
from analysis.timing import TimingEngine

from src.validators.boot import Boot


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

@pytest.fixture(scope="session")
def config():
    """
    Load customer configuration once for the entire test session.
    """
    cfg.load()
    return cfg


# ---------------------------------------------------------
# Backend
# ---------------------------------------------------------

@pytest.fixture(scope="session")
def backend():
    """
    Start backend once for the entire test session.
    """
    dm = Device_Manager()
    backend = dm.startup()

    yield backend

    dm.shutdown()


# ---------------------------------------------------------
# Analysis Engines
# ---------------------------------------------------------

@pytest.fixture(scope="session")
def matcher():
    return VisualMatcher(threshold=0.85)


@pytest.fixture(scope="session")
def ocr():
    return OCREngine()


@pytest.fixture(scope="session")
def av():
    return AVQualityChecker()


@pytest.fixture(scope="session")
def timer():
    return TimingEngine()


# ---------------------------------------------------------
# Validators
# ---------------------------------------------------------

@pytest.fixture(scope="session")
def boot(config, backend,matcher,ocr,av,timer):
    """
    Boot validator shared across the test session.
    """
    return Boot(
        customer=config.get("customer.name"),
        config=config,
        backend=backend,
        matcher=matcher,
        ocr=ocr,
        av=av,
        timer=timer,
    )