"""Launch RedRatHub from the automation framework.

Use this script from the repo root:
    python run_redrathub.py

Optional port override:
    python run_redrathub.py --port 8080

The existing run_redrathub.bat file remains available for manual validation only.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))


def parse_args():
    parser = argparse.ArgumentParser(description="Start RedRatHub for the STB automation framework")
    parser.add_argument("--port", type=int, help="Override RedRatHub HTTP port")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.port:
        os.environ["REDRAT_HTTP_PORT"] = str(args.port)

    try:
        from core.redrat.redrat_hub import RedRatHubManager
    except ImportError as exc:
        raise SystemExit(
            "Failed to import core.redrat.redrat_hub. "
            "Run this script from the repository root or ensure the repo root is on PYTHONPATH."
        ) from exc

    manager = RedRatHubManager()
    manager.http_port = args.port or manager.http_port
    manager.hub_url = f"http://127.0.0.1:{manager.http_port}"

    try:
        manager.ensure_running()
    except Exception as exc:
        raise SystemExit(f"RedRatHub startup failed: {exc}") from exc

    print(f"RedRatHub is running at {manager.hub_url}")


if __name__ == "__main__":
    main()
