import time
from pathlib import Path

# Navigators packages
from src.navigators.autoscan import Autoscan
from src.navigators.channel_banner import ChannelBanner
from src.navigators.menu import Menu

# Validators Packages
from src.validators.boot import Boot
from src.validators.live_tv import LiveTV
from src.validators.av import AV




class Setup:
    """
    Shared dependencies for all business modules.
    """

    def __init__(self, customer, backend, ocr, matcher, config, av, timer):
        self.customer = customer
        self.backend = backend
        self.ocr = ocr
        self.matcher = matcher
        self.config = config
        self.av = av
        self.timer = timer

        self._timer_started = False
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")

        project_root = Path(__file__).resolve().parents[1]
        self.templates_path = (
                project_root
                / "assets"
                / "customers"
                / self.customer
                / "templates"
        )

        self.evidence_path = (
                project_root
                / "evidence"
        )

class STB:
    """
    Main entry point for all validators and navigators.
    """

    def __init__(self, customer, backend, ocr, matcher, config, av, timer):

        self.ctx = Setup(
            customer=customer,
            backend=backend,
            ocr=ocr,
            matcher=matcher,
            config=config,
            av=av,
            timer=timer,
        )

        # Navigators...
        self.autoscan = Autoscan(self.ctx)
        self.channel_banner = ChannelBanner(self.ctx)
        self.menu = Menu(self.ctx)
        
        # Validators
        self.boot = Boot(self.ctx)
        self.liveTV = LiveTV(self.ctx)
        # self.av = AV(self.ctx)
        
        