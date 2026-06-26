# config/config_loader.py
import os
import yaml
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _load_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Customer config not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


class Config:
    """
    Loads customer YAML config.
    Secrets and connection details stay in .env as before.
    Customer-specific settings (channels, keys, SLAs) live in YAML.

    Usage:
        from core.config_loader import cfg
        cfg.load()
        zap_sla = cfg.get("sla.zap_time_ms")
    """

    def __init__(self):
        self._data   = {}   # Default Empty Dictonary data set defined 
        self._loaded = False

    def load(self, customer=None):
        """
        Load customer config.
        customer : customer ID — reads from CUSTOMER in .env if not passed.
        """
        customer = customer or os.getenv("CUSTOMER")

        path = f"config/customers/{customer}_config.yaml"
        logger.info(f"Loading customer config → '{customer}'")

        self._data   = _load_yaml(path)
        self._loaded = True

        logger.info(f"✅ Config loaded → {self.get('customer.name', customer)}")
        return self

    def get(self, key_path, default=None):
        """
        Access nested values using dot notation.
        e.g. cfg.get("sla.zap_time_ms")       → 5000
             cfg.get("channels.default_channel") → 6
             cfg.get("timeouts.settle_s")        → 3
        """
        keys  = key_path.split(".")
        value = self._data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default

        return value

    def get_keys(self):
        """Returns the full key mapping dict."""
        return self._data.get("keys", {})

    def get_channels(self):
        """Returns the channel list."""
        return self._data.get("channels", {})

    def get_ui_template(self):
        """Returns UI template paths."""
        return self._data.get("ui", {})

    def __repr__(self):
        return f"Config(customer='{self.get('customer.name', 'unknown')}')"


# Singleton — import this everywhere
cfg = Config()