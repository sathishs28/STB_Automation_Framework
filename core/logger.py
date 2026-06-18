import logging
import os
import argparse

def setup_logging():
    level = os.getenv("LOG_LEVEL")
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        force=True
    )